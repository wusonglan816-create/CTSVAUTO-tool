from __future__ import annotations

from src.cli.common import export_report, settings
from src.core.exceptions import CTSVerifierError
from src.core.error_messages import ERRORS
from src.report.reporter import build_report
from src.runner.test_runner import TestRunner
from src.tests.test_registry import iter_specs


def cmd_run(args) -> int:
    config = settings()
    TestRunner.ensure_output_dirs(config)
    specs = list(
        iter_specs(
            args.category,
            args.test,
            automatable_only=True,
            module=getattr(args, "module", "all"),
        )
    )
    if not specs:
        print("未找到匹配测试项")
        return 1

    runner = TestRunner(
        config,
        device_id=args.device,
        retry_count=args.retry,
        platform=getattr(args, "platform", "auto"),
    )
    try:
        results = runner.run_suite(specs, show_progress=not args.quiet)
        device_info = runner.device_info()
    except CTSVerifierError as exc:
        print(exc.message)
        return 1
    except Exception as exc:
        print(ERRORS["E001"].format())
        print(f"详细信息: {exc}")
        return 1

    report = build_report(results, device_info)
    output = export_report(report, args.format, args.output)
    print(f"报告已生成: {output}")
    return 1 if report["report_info"]["failed"] else 0
