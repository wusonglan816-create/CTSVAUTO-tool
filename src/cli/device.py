from __future__ import annotations

from pathlib import Path

from src.core.adb_client import ADBClient
from src.core.config import deep_get
from src.core.device import DeviceManager
from src.core.error_messages import ERRORS
from src.core.exceptions import CTSVerifierError
from src.cli.common import settings


def cmd_device(args) -> int:
    config = settings()
    adb_path = deep_get(config, "advanced.adb_path")
    if args.action == "list":
        try:
            devices = ADBClient.list_devices(adb_path)
        except Exception as exc:
            print(ERRORS["E001"].format())
            print(f"ADB 输出: {exc}")
            return 1
        if not devices:
            print(ERRORS["E001"].format())
            return 1
        for device in devices:
            print(device)
        return 0

    manager = DeviceManager(args.id, adb_path=adb_path)
    try:
        manager.connect()
    except Exception as exc:
        print(ERRORS["E001"].format())
        print(f"详细信息: {exc}")
        return 1

    if args.action == "info":
        for key, value in manager.get_device_info().items():
            print(f"{key}: {value}")
        return 0

    if args.action == "setup":
        package = deep_get(config, "cts_verifier.package")
        apk = Path("apk/CtsVerifier.apk")
        if not manager.adb.is_package_installed(package):
            if not apk.exists():
                print(ERRORS["E002"].format())
                return 1
            manager.install_apk(str(apk), timeout=int(deep_get(config, "cts_verifier.install_timeout", 60)))
        try:
            manager.wake_and_unlock()
        except CTSVerifierError as exc:
            print(exc.message)
            return 1
        manager.adb.shell("settings put global window_animation_scale 0", check=False)
        manager.adb.shell("settings put global transition_animation_scale 0", check=False)
        manager.adb.shell("settings put global animator_duration_scale 0", check=False)
        manager.adb.shell("svc power stayon usb", check=False)
        print("设备初始化完成")
        return 0

    return 1
