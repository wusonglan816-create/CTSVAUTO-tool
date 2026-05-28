from __future__ import annotations

import logging
import re
import time
from pathlib import Path

from src.core.adb_client import ADBClient
from src.core.exceptions import CTSVerifierError, DeviceDisconnectedError, DeviceLockedError


class DeviceManager:
    def __init__(
        self,
        device_id: str | None = None,
        adb_path: str | None = None,
        wait_timeout: int = 30,
    ):
        self.device_id = device_id
        self.wait_timeout = wait_timeout
        self.adb = ADBClient(device_id, adb_path=adb_path)
        self.u2 = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def connect(self) -> bool:
        devices = ADBClient.list_devices(self.adb.adb_path)
        if self.device_id and self.device_id not in devices:
            raise DeviceDisconnectedError(self.device_id)
        if not self.device_id:
            if not devices:
                raise DeviceDisconnectedError(None)
            self.device_id = devices[0]
            self.adb.device_id = self.device_id

        try:
            import uiautomator2 as u2
        except ImportError as exc:
            raise CTSVerifierError(
                "uiautomator2 is not installed. Run: pip install -r requirements.txt"
            ) from exc

        self.u2 = u2.connect(self.device_id)
        return True

    def reconnect(self) -> bool:
        self.u2 = None
        time.sleep(1)
        return self.connect()

    def disconnect(self) -> None:
        self.u2 = None

    def get_device_info(self) -> dict[str, str]:
        return {
            "device_id": self.device_id or "",
            "model": self.adb.getprop("ro.product.model"),
            "manufacturer": self.adb.getprop("ro.product.manufacturer"),
            "android_version": self.adb.getprop("ro.build.version.release"),
            "sdk": self.adb.getprop("ro.build.version.sdk"),
        }

    def install_apk(self, apk_path: str, timeout: int = 60) -> bool:
        path = Path(apk_path)
        if not path.exists():
            raise CTSVerifierError(f"APK not found: {apk_path}")
        self.adb.install(str(path), timeout=timeout)
        return True

    def is_locked(self) -> bool:
        output = self.adb.shell("dumpsys window", timeout=10, check=False).stdout
        lock_markers = (
            "mDreamingLockscreen=true",
            "mShowingLockscreen=true",
            "isStatusBarKeyguard=true",
        )
        if any(marker in output for marker in lock_markers):
            return True
        focus_line = next((line for line in output.splitlines() if "mCurrentFocus=" in line), "")
        return "Keyguard" in focus_line

    def _screen_size(self) -> tuple[int, int]:
        output = self.adb.shell("wm size", timeout=10, check=False).stdout
        match = re.search(r"Physical size:\s*(\d+)x(\d+)", output)
        if not match:
            return 720, 1280
        return int(match.group(1)), int(match.group(2))

    def wake_and_unlock(self) -> None:
        self.adb.shell("input keyevent WAKEUP", check=False)
        time.sleep(0.3)
        self.adb.shell("wm dismiss-keyguard", check=False)
        time.sleep(0.5)
        if self.is_locked():
            width, height = self._screen_size()
            x = width // 2
            self.adb.shell(
                f"input swipe {x} {int(height * 0.82)} {x} {int(height * 0.22)} 300",
                check=False,
            )
            time.sleep(0.8)
        if self.is_locked():
            raise DeviceLockedError()

    def start_app(self, package: str, activity: str | None = None) -> None:
        if self.u2 is not None:
            self.u2.app_start(package, activity=activity)
            return
        if activity:
            self.adb.shell(f"am start -n {package}/{activity}")
        else:
            self.adb.shell(f"monkey -p {package} 1")

    def stop_app(self, package: str) -> None:
        if self.u2 is not None:
            self.u2.app_stop(package)
            return
        self.adb.shell(f"am force-stop {package}", check=False)

    def shell(self, command: str):
        if self.u2 is not None:
            return self.u2.shell(command)
        return self.adb.shell(command)
