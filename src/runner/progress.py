from __future__ import annotations

import sys


class ProgressBar:
    def __init__(self, total: int, width: int = 36):
        self.total = max(total, 1)
        self.width = width
        self.current = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def update(self, status: str, test_name: str) -> None:
        self.current += 1
        if status == "passed":
            self.passed += 1
        elif status == "skipped":
            self.skipped += 1
        else:
            self.failed += 1
        filled = int(self.width * self.current / self.total)
        bar = "#" * filled + "." * (self.width - filled)
        sys.stdout.write(
            f"\r[{bar}] {self.current}/{self.total} "
            f"P:{self.passed} F:{self.failed} S:{self.skipped} | {test_name[:40]}"
        )
        sys.stdout.flush()

    def finish(self) -> None:
        sys.stdout.write("\n")
