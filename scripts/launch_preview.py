"""Launch only the locally built portable preview for WebView2 integration testing."""

import os
import argparse
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--package", default="AccessMaze-web-preview")
options = parser.parse_args()
package = (root / "dist" / options.package).resolve()
if package.parent != (root / "dist").resolve():
    raise SystemExit("Package must be directly inside dist")
startup = subprocess.STARTUPINFO()
startup.dwFlags = subprocess.STARTF_USESHOWWINDOW
startup.wShowWindow = 0
process = subprocess.Popen(
    [str(package / "AccessMaze.exe")],
    cwd=package,
    env={
        **os.environ,
        "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS": "--remote-debugging-port=9224 --remote-debugging-address=127.0.0.1",
    },
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    startupinfo=startup,
)
print(f"Portable desktop test process: {process.pid}")
