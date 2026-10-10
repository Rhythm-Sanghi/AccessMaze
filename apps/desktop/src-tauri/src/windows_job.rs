use std::{os::windows::io::AsRawHandle, process::Child};
use windows_sys::Win32::{
    Foundation::CloseHandle,
    System::JobObjects::{
        AssignProcessToJobObject, CreateJobObjectW, JobObjectExtendedLimitInformation,
        SetInformationJobObject, JOBOBJECT_EXTENDED_LIMIT_INFORMATION,
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
    },
};

// The owning handle is stored as an integer so the host can move it between command threads.
pub struct WindowsJob(isize);

impl WindowsJob {
    pub fn attach(child: &Child) -> Result<Self, String> {
        // Windows fills no Rust-owned memory here; the structure is the Win32 POD layout.
        unsafe {
            let handle = CreateJobObjectW(std::ptr::null(), std::ptr::null());
            if handle.is_null() {
                return Err(std::io::Error::last_os_error().to_string());
            }
            let job = Self(handle as isize);
            let mut limits: JOBOBJECT_EXTENDED_LIMIT_INFORMATION = std::mem::zeroed();
            limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
            if SetInformationJobObject(
                handle,
                JobObjectExtendedLimitInformation,
                &limits as *const _ as *const _,
                std::mem::size_of_val(&limits) as u32,
            ) == 0
            {
                return Err(std::io::Error::last_os_error().to_string());
            }
            if AssignProcessToJobObject(handle, child.as_raw_handle()) == 0 {
                return Err(std::io::Error::last_os_error().to_string());
            }
            Ok(job)
        }
    }
}

impl Drop for WindowsJob {
    fn drop(&mut self) {
        // The handle is owned once. Closing it terminates surviving worker descendants.
        unsafe {
            CloseHandle(self.0 as _);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::{
        process::{Command, Stdio},
        time::{Duration, Instant},
    };

    #[test]
    fn closing_job_terminates_a_managed_process() {
        let mut child = Command::new("ping.exe")
            .args(["-t", "127.0.0.1"])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .unwrap();
        let job = WindowsJob::attach(&child).unwrap();
        drop(job);
        let deadline = Instant::now() + Duration::from_secs(5);
        while child.try_wait().unwrap().is_none() && Instant::now() < deadline {
            std::thread::sleep(Duration::from_millis(20));
        }
        let stopped = child.try_wait().unwrap().is_some();
        if !stopped {
            let _ = child.kill();
        }
        let _ = child.wait();
        assert!(stopped, "Managed process survived job closure");
    }
}
