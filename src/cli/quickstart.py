from __future__ import annotations

from argparse import Namespace

from src.cli.device import cmd_device
from src.cli.run import cmd_run


def cmd_quickstart(args) -> int:
    print("CTS Verifier 快速入门")
    print("=" * 32)
    print("[1/3] 检测设备")
    device_code = cmd_device(Namespace(action="list", id=args.device))
    if device_code != 0:
        return device_code
    print("[2/3] 初始化设备")
    setup_code = cmd_device(Namespace(action="setup", id=args.device))
    if setup_code != 0:
        return setup_code
    print("[3/3] 运行冒烟测试: CTS Verifier Launch Smoke Test")
    return cmd_run(
        Namespace(
            category="smoke",
            module="all",
            platform="auto",
            test="Launch Smoke",
            device=args.device,
            output="reports/quickstart.html",
            format="html",
            retry=1,
            quiet=False,
        )
    )
