from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def export_json(report: dict[str, Any], output: str) -> str:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)
