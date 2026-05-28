from __future__ import annotations

import argparse
import sys

from src.cli.common import setup_logging
from src.cli.config import cmd_config
from src.cli.device import cmd_device
from src.cli.list import cmd_list
from src.cli.quickstart import cmd_quickstart
from src.cli.report import cmd_report
from src.cli.run import cmd_run
from src.platforms.profile import platform_names
from src.tests.test_registry import categories, modules


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cts-verify",
        description="Android CTS Verifier 自动化测试工具",
    )
    subparsers = parser.add_subparsers(dest="command")
    category_choices = categories() + ["all"]
    module_choices = modules() + ["all"]
    platform_choices = ["auto"] + platform_names()

    run_parser = subparsers.add_parser("run", help="执行测试")
    run_parser.add_argument("--category", "-c", choices=category_choices, default="all")
    run_parser.add_argument("--module", "-m", choices=module_choices, default="all", help="按文档模块筛选")
    run_parser.add_argument("--platform", choices=platform_choices, default="auto", help="Android 14/15/16 平台配置")
    run_parser.add_argument("--test", "-t", help="测试项名称，支持部分匹配")
    run_parser.add_argument("--device", "-d", help="设备 ID，默认自动检测")
    run_parser.add_argument("--output", "-o", default="reports/report.html")
    run_parser.add_argument("--format", "-f", choices=["html", "json", "junit"], default="html")
    run_parser.add_argument("--retry", type=int, default=None)
    run_parser.add_argument("--verbose", "-v", action="store_true")
    run_parser.add_argument("--quiet", "-q", action="store_true")
    run_parser.set_defaults(func=cmd_run)

    list_parser = subparsers.add_parser("list", help="列出测试项")
    list_parser.add_argument("--category", "-c", choices=category_choices, default="all")
    list_parser.add_argument("--module", "-m", choices=module_choices, default="all", help="按文档模块筛选")
    list_parser.add_argument("--automatable", action="store_true")
    list_parser.set_defaults(func=cmd_list)

    report_parser = subparsers.add_parser("report", help="生成报告")
    report_parser.add_argument("--input", "-i", default="reports/results.json")
    report_parser.add_argument("--output", "-o", default="reports/report.html")
    report_parser.add_argument("--format", "-f", choices=["html", "json", "junit"], default="html")
    report_parser.set_defaults(func=cmd_report)

    device_parser = subparsers.add_parser("device", help="设备管理")
    device_parser.add_argument("action", choices=["list", "info", "setup"])
    device_parser.add_argument("--id", help="设备 ID")
    device_parser.set_defaults(func=cmd_device)

    config_parser = subparsers.add_parser("config", help="配置管理")
    config_parser.add_argument("action", choices=["show", "set", "init"])
    config_parser.add_argument("key", nargs="?")
    config_parser.add_argument("value", nargs="?")
    config_parser.set_defaults(func=cmd_config)

    quickstart_parser = subparsers.add_parser("quickstart", help="设备检测并运行示例测试")
    quickstart_parser.add_argument("--device", "-d", help="设备 ID，默认自动检测")
    quickstart_parser.set_defaults(func=cmd_quickstart)

    return parser


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1
    setup_logging(
        verbose=bool(getattr(args, "verbose", False)),
        quiet=bool(getattr(args, "quiet", False)),
    )
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
