from src.report.reporter import build_report
from src.tests.base_test import TestResult


def test_build_report_groups_results():
    report = build_report(
        [
            TestResult("A", "audio", "passed", 10),
            TestResult("B", "audio", "failed", 20, error="x"),
            TestResult("C", "camera", "skipped", 30),
        ],
        {"device_id": "demo"},
    )

    assert report["report_info"]["total_tests"] == 3
    assert report["report_info"]["passed"] == 1
    assert report["report_info"]["failed"] == 1
    assert report["report_info"]["skipped"] == 1
    assert {category["name"] for category in report["categories"]} == {"audio", "camera"}
