from __future__ import annotations

import logging
from pathlib import Path

from src.core.config import load_settings
from src.report.exporters.html_exporter import export_html
from src.report.exporters.json_exporter import export_json
from src.report.exporters.junit_exporter import export_junit


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    if quiet:
        level = logging.ERROR
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("logs/cts_automation.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def settings() -> dict:
    return load_settings()


def export_report(report: dict, fmt: str, output: str) -> str:
    if fmt == "json":
        return export_json(report, output)
    if fmt == "junit":
        return export_junit(report, output)
    return export_html(report, output)
