from __future__ import annotations

from pathlib import Path
from typing import Any


def export_html(report: dict[str, Any], output: str) -> str:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[str] = []
    for category in report.get("categories", []):
        for test in category.get("tests", []):
            rows.append(
                "<tr>"
                f"<td>{category['name']}</td>"
                f"<td>{test['test_name']}</td>"
                f"<td class='{test['status']}'>{test['status']}</td>"
                f"<td>{test['duration_ms']}</td>"
                f"<td>{test.get('retry_count', 0)}</td>"
                f"<td>{test.get('error') or ''}</td>"
                "</tr>"
            )
    info = report["report_info"]
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>CTS Verifier Automation Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2933; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 8px; text-align: left; }}
    th {{ background: #f0f4f8; }}
    .passed {{ color: #0b6b3a; font-weight: bold; }}
    .failed {{ color: #b42318; font-weight: bold; }}
    .skipped {{ color: #8a5a00; font-weight: bold; }}
    .summary {{ margin-bottom: 18px; }}
  </style>
</head>
<body>
  <h1>CTS Verifier Automation Report</h1>
  <div class="summary">
    <div>Generated: {info['generated_at']}</div>
    <div>Total: {info['total_tests']} Passed: {info['passed']} Failed: {info['failed']} Skipped: {info['skipped']}</div>
    <div>Duration: {info['duration_seconds']}s</div>
  </div>
  <table>
    <thead><tr><th>Category</th><th>Test</th><th>Status</th><th>Duration ms</th><th>Retries</th><th>Error</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")
    return str(path)
