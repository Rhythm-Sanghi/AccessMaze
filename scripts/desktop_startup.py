"""Measure a packaged desktop reaching connected UI, then close only owned processes."""

import argparse
import asyncio
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

import psutil
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True)
    args = parser.parse_args()
    package = (ROOT / "dist" / args.package).resolve()
    if package.parent != (ROOT / "dist").resolve():
        raise ValueError("Package must be directly inside dist")
    endpoint = "http://127.0.0.1:9227"
    try:
        urllib.request.urlopen(endpoint + "/json/version", timeout=1)
    except OSError:
        pass
    else:
        raise RuntimeError("Test port 9227 already occupied")
    samples = []
    async with async_playwright() as pw:
        for _ in range(3):
            startup = subprocess.STARTUPINFO()
            startup.dwFlags = subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 0
            started = time.perf_counter()
            process = subprocess.Popen(
                [str(package / "AccessMaze.exe")],
                cwd=package,
                env={
                    **os.environ,
                    "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS": "--remote-debugging-port=9227 --remote-debugging-address=127.0.0.1",
                },
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=startup,
            )
            owned = []
            try:
                for _ in range(150):
                    try:
                        browser = await pw.chromium.connect_over_cdp(
                            endpoint, timeout=500
                        )
                        break
                    except Exception:
                        if process.poll() is not None:
                            raise RuntimeError("Owned desktop exited before connection")
                        await asyncio.sleep(0.1)
                else:
                    raise TimeoutError("Desktop debugging endpoint unavailable")
                page = browser.contexts[0].pages[0]
                await page.wait_for_url("**tauri.localhost**", timeout=30000)
                await page.get_by_text("Worker connected", exact=True).wait_for(
                    timeout=30000
                )
                ready = time.perf_counter() - started
                desktop = psutil.Process(process.pid)
                owned = desktop.children(recursive=True)
                rss = sum(
                    p.memory_info().rss for p in [desktop, *owned] if p.is_running()
                )
                samples.append(
                    {
                        "connected_ui_seconds": round(ready, 3),
                        "ready_summed_rss_mib": round(rss / 1024**2, 2),
                        "child_processes": len(owned),
                    }
                )
            finally:
                if process.poll() is None:
                    owned = psutil.Process(process.pid).children(recursive=True)
                    try:
                        subprocess.run(
                            [
                                str(
                                    Path(os.environ["SystemRoot"])
                                    / "System32/WindowsPowerShell/v1.0/powershell.exe"
                                ),
                                "-NoProfile",
                                "-Command",
                                f"(Get-Process -Id {process.pid}).CloseMainWindow()",
                            ],
                            capture_output=True,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                            timeout=10,
                        )
                    except (OSError, subprocess.TimeoutExpired):
                        # Cleanup must still run when the close helper is unavailable.
                        process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait(timeout=10)
                for _ in range(50):
                    if not any(p.is_running() for p in owned):
                        break
                    await asyncio.sleep(0.1)
                assert not any(p.is_running() for p in owned), (
                    "Owned desktop left children"
                )
    result = {
        "package": args.package,
        "measurements": samples,
        "scope": "Same laptop, existing synthetic AppData history, three sequential launches; cache state uncontrolled. Time to CDP-observed Worker connected includes polling/harness overhead. RSS includes desktop, WebView2 and worker; shared pages counted repeatedly. Test-only loopback port closed after owned desktop exit.",
    }
    (ROOT / "docs/testing/desktop-startup.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
