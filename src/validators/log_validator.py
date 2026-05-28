from __future__ import annotations

import re


class LogValidator:
    def __init__(self, adb_client):
        self.adb = adb_client

    def any_pattern_matches(self, patterns: list[str], lines: int = 500) -> bool:
        logs = self.adb.get_logcat(lines=lines)
        return any(re.search(pattern, logs) for pattern in patterns)
