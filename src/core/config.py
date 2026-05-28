from __future__ import annotations

from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError(
            "PyYAML is required to read configuration. Run: pip install -r requirements.txt"
        ) from exc

    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_settings(path: str | Path | None = None) -> dict[str, Any]:
    config_path = Path(path) if path else PROJECT_ROOT / "config" / "settings.yaml"
    return _load_yaml(config_path)


def load_test_cases(path: str | Path | None = None) -> dict[str, Any]:
    config_path = Path(path) if path else PROJECT_ROOT / "config" / "test_cases.yaml"
    return _load_yaml(config_path)


def deep_get(data: dict[str, Any], key: str, default: Any = None) -> Any:
    current: Any = data
    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current
