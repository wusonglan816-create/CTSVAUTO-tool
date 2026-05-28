from __future__ import annotations

import json
from pathlib import Path

from src.cli.common import export_report


def cmd_report(args) -> int:
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"结果文件不存在: {input_path}")
        return 1
    report = json.loads(input_path.read_text(encoding="utf-8"))
    output = export_report(report, args.format, args.output)
    print(f"报告已生成: {output}")
    return 0
