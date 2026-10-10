#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde_json::{json, Value};
use std::{
    io::{BufRead, BufReader, Write},
    path::PathBuf,
    process::{Child, ChildStdin, Command, Stdio},
    sync::{mpsc, Mutex},
    time::{Duration, Instant},
};
use tauri::Manager;

#[cfg(windows)]
mod windows_job;

struct Worker {
    #[cfg(windows)]
    _job: windows_job::WindowsJob,
    child: Child,
    input: Option<ChildStdin>,
    output: mpsc::Receiver<Result<String, String>>,
    sequence: u64,
    broken: bool,
}

impl Worker {
    fn start(storage: PathBuf) -> Result<Self, String> {
        std::fs::create_dir_all(&storage).map_err(|e| e.to_string())?;
        let log = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(storage.join("worker.log"))
            .map_err(|e| e.to_string())?;
        let mut command;
        if cfg!(debug_assertions) {
            let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../..");
            let python = root.join(if cfg!(windows) {
                "engine/.venv/Scripts/python.exe"
            } else {
                "engine/.venv/bin/python"
            });
            command = Command::new(python);
            command
                .args(["-m", "accessmaze.worker", "--resources"])
                .arg(&root)
                .current_dir(&root);
        } else {
            let directory = std::env::current_exe()
                .map_err(|e| e.to_string())?
                .parent()
                .ok_or("Application directory missing")?
                .to_owned();
            command = Command::new(directory.join(if cfg!(windows) {
                "accessmaze-worker.exe"
            } else {
                "accessmaze-worker"
            }));
            command.arg("--resources").arg(directory.join("resources"));
        }
        command
            .arg("--storage")
            .arg(storage)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::from(log));
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            command.creation_flags(0x08000000);
        }
        let mut child = command
            .spawn()
            .map_err(|e| format!("Cannot launch worker: {e}"))?;
        #[cfg(windows)]
        let job = match windows_job::WindowsJob::attach(&child) {
            Ok(job) => job,
            Err(error) => {
                let _ = child.kill();
                let _ = child.wait();
                return Err(error);
            }
        };
        let input = child.stdin.take().ok_or("Worker stdin missing")?;
        let output = child.stdout.take().ok_or("Worker stdout missing")?;
        let (sender, receiver) = mpsc::sync_channel(8);
        std::thread::spawn(move || {
            for line in BufReader::new(output).lines() {
                if sender.send(line.map_err(|e| e.to_string())).is_err() {
                    break;
                }
            }
        });
        Ok(Self {
            #[cfg(windows)]
            _job: job,
            child,
            input: Some(input),
            output: receiver,
            sequence: 0,
            broken: false,
        })
    }

    fn request(&mut self, method: String, params: Value) -> Result<Value, String> {
        self.broken = true;
        self.sequence += 1;
        let id = self.sequence.to_string();
        let message = json!({"version":1,"id":id,"method":method,"params":params});
        let input = self.input.as_mut().ok_or("Worker stopped")?;
        writeln!(input, "{message}")
            .and_then(|_| input.flush())
            .map_err(|e| e.to_string())?;
        let line = self
            .output
            .recv_timeout(Duration::from_secs(20))
            .map_err(|_| {
                "Worker stopped responding. Reconnect the engine in Projects.".to_owned()
            })??;
        let response: Value = serde_json::from_str(&line).map_err(|e| e.to_string())?;
        if response["version"] != 1 || response["id"] != id {
            return Err("Worker protocol mismatch".into());
        }
        self.broken = false;
        if let Some(error) = response.get("error") {
            return Err(error["message"]
                .as_str()
                .unwrap_or("Worker request failed")
                .to_owned());
        }
        response
            .get("result")
            .cloned()
            .ok_or("Worker response missing result".into())
    }
}

impl Drop for Worker {
    fn drop(&mut self) {
        self.input.take(); // EOF asks the Python worker to cancel and close Chromium.
        let started = Instant::now();
        while started.elapsed() < Duration::from_secs(12) {
            if matches!(self.child.try_wait(), Ok(Some(_))) {
                return;
            }
            std::thread::sleep(Duration::from_millis(50));
        }
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            let _ = Command::new("taskkill")
                .args(["/PID", &self.child.id().to_string(), "/T", "/F"])
                .creation_flags(0x08000000)
                .output();
        }
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

struct Host(Mutex<Option<Worker>>);

#[tauri::command]
async fn worker_request(
    app: tauri::AppHandle,
    method: String,
    params: Value,
) -> Result<Value, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let host = app.state::<Host>();
        let mut slot = host.0.lock().map_err(|_| "Worker state lock failed")?;
        if slot.is_none() {
            *slot = Some(Worker::start(
                app.path().app_data_dir().map_err(|e| e.to_string())?,
            )?);
        }
        if slot
            .as_mut()
            .unwrap()
            .child
            .try_wait()
            .map_err(|e| e.to_string())?
            .is_some()
        {
            *slot = Some(Worker::start(
                app.path().app_data_dir().map_err(|e| e.to_string())?,
            )?);
        }
        let result = slot.as_mut().unwrap().request(method, params);
        if slot.as_ref().unwrap().broken {
            slot.take();
        }
        result
    })
    .await
    .map_err(|e| e.to_string())?
}

fn main() {
    tauri::Builder::default()
        .manage(Host(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![worker_request])
        .on_window_event(|window, event| {
            if matches!(event, tauri::WindowEvent::Destroyed) {
                if let Ok(mut worker) = window.state::<Host>().0.lock() {
                    worker.take();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("AccessMaze desktop host failed");
}
