from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.config import PROJECT_ROOT


@dataclass(frozen=True)
class PlatformProfile:
    name: str
    android_major: int | None
    data: dict[str, Any]

    def test(self, key: str) -> dict[str, Any]:
        return self.data.get("tests", {}).get(key, {})

    def command(self, test_key: str, command_key: str, default: str) -> str:
        return self.test(test_key).get("shell", {}).get(command_key, default)

    def values(self, test_key: str, key: str, default: list[str]) -> list[str]:
        value = self.test(test_key).get(key)
        if not value:
            return default
        return list(value)


def load_platform_profile(name: str = "android16") -> PlatformProfile:
    normalized = name.lower()
    path = PROJECT_ROOT / "config" / "platforms" / f"{normalized}.yaml"
    if not path.exists():
        raise ValueError(f"Unknown platform profile: {name}")
    data = _load_yaml(path)
    return PlatformProfile(
        name=data.get("platform", normalized),
        android_major=data.get("android_major"),
        data=data,
    )


def resolve_platform_name(requested: str | None, android_version: str | None = None) -> str:
    if requested and requested != "auto":
        return requested
    if android_version:
        major = android_version.split(".", maxsplit=1)[0]
        if major in {"14", "15", "16"}:
            return f"android{major}"
    return "android16"


def platform_names() -> list[str]:
    platform_dir = PROJECT_ROOT / "config" / "platforms"
    return sorted(path.stem for path in platform_dir.glob("android*.yaml"))


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to read platform profiles") from exc
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}
