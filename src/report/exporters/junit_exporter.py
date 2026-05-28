from __future__ import annotations

from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


def export_junit(report: dict[str, Any], output: str) -> str:
    info = report["report_info"]
    root = ET.Element(
        "testsuites",
        {
            "name": "CTS Verifier Tests",
            "tests": str(info["total_tests"]),
            "failures": str(info["failed"]),
            "skipped": str(info["skipped"]),
            "time": str(info["duration_seconds"]),
        },
    )
    for category in report.get("categories", []):
        suite = ET.SubElement(
            root,
            "testsuite",
            {
                "name": category["name"],
                "tests": str(category["total"]),
                "failures": str(category["failed"]),
                "skipped": str(category["skipped"]),
            },
        )
        for test in category.get("tests", []):
            case = ET.SubElement(
                suite,
                "testcase",
                {
                    "name": test["test_name"],
                    "classname": category["name"],
                    "time": str(round(test["duration_ms"] / 1000, 3)),
                },
            )
            if test["status"] == "failed":
                failure = ET.SubElement(case, "failure", {"message": test.get("error") or "failed"})
                failure.text = test.get("error") or ""
            elif test["status"] == "skipped":
                ET.SubElement(case, "skipped", {"message": test.get("error") or "skipped"})

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return str(path)
