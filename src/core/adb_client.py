from __future__ import annotations

import subprocess
from dataclasses import dataclass

from src.core.exceptions import ADBCommandError


@dataclass
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def output(self) -> str:
        return (self.stdout or self.stderr).strip()


class ADBClient:
    def __init__(self, device_id: str | None = None, adb_path: str | None = None):
        self.device_id = device_id
        self.adb_path = adb_path or "adb"

    def _base_cmd(self) -> list[str]:
        cmd = [self.adb_path]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        return cmd

    def run(self, args: list[str], timeout: int = 30, check: bool = True) -> CommandResult:
        command = self._base_cmd() + args
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        result = CommandResult(command, completed.returncode, completed.stdout, completed.stderr)
        if check and result.returncode != 0:
            raise ADBCommandError(" ".join(command), result.output)
        return result

    def shell(self, command: str, timeout: int = 30, check: bool = True) -> CommandResult:
        return self.run(["shell", command], timeout=timeout, check=check)

    def install(self, apk_path: str, timeout: int = 60) -> CommandResult:
        return self.run(["install", "-r", apk_path], timeout=timeout)

    def list_packages(self) -> list[str]:
        result = self.shell("pm list packages", check=False)
        return [line.replace("package:", "").strip() for line in result.stdout.splitlines()]

    def is_package_installed(self, package: str) -> bool:
        return package in self.list_packages()

    def getprop(self, prop: str) -> str:
        return self.shell(f"getprop {prop}", check=False).stdout.strip()

    def get_logcat(self, lines: int = 500) -> str:
        return self.run(["logcat", "-d", "-t", str(lines)], timeout=15, check=False).stdout

    @classmethod
    def list_devices(cls, adb_path: str | None = None) -> list[str]:
        client = cls(adb_path=adb_path)
        result = client.run(["devices"], timeout=10, check=False)
        devices: list[str] = []
        for line in result.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])
        return devices
