from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from src.tests.base_test import TestResult


def build_report(results: list[TestResult], device: dict[str, str] | None = None) -> dict[str, Any]:
    grouped: dict[str, list[TestResult]] = defaultdict(list)
    for result in results:
        grouped[result.test_category].append(result)

    total = len(results)
    passed = sum(1 for result in results if result.status == "passed")
    failed = sum(1 for result in results if result.status == "failed")
    skipped = sum(1 for result in results if result.status == "skipped")
    duration_ms = sum(result.duration_ms for result in results)

    categories = []
    for name, category_results in sorted(grouped.items()):
        categories.append(
            {
                "name": name,
                "total": len(category_results),
                "passed": sum(1 for item in category_results if item.status == "passed"),
                "failed": sum(1 for item in category_results if item.status == "failed"),
                "skipped": sum(1 for item in category_results if item.status == "skipped"),
                "tests": [result.__dict__ for result in category_results],
            }
        )

    return {
        "report_info": {
            "version": "0.1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "device": device or {},
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "duration_seconds": round(duration_ms / 1000, 3),
        },
        "categories": categories,
    }
