import json

from src.report.exporters.html_exporter import export_html
from src.report.exporters.json_exporter import export_json
from src.report.exporters.junit_exporter import export_junit
from src.report.reporter import build_report
from src.tests.base_test import TestResult


def test_exporters_write_files(tmp_path):
    report = build_report([TestResult("A", "audio", "passed", 10)])

    json_path = export_json(report, str(tmp_path / "report.json"))
    html_path = export_html(report, str(tmp_path / "report.html"))
    junit_path = export_junit(report, str(tmp_path / "report.xml"))

    assert json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))["report_info"]["passed"] == 1
    assert json_path.endswith("report.json")
    assert html_path.endswith("report.html")
    assert junit_path.endswith("report.xml")
