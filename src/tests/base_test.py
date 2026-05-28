from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TestResult:
    __test__ = False

    test_name: str
    test_category: str
    status: str
    duration_ms: int
    retry_count: int = 0
    error: str | None = None
    screenshot: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status == "passed"


class BaseTest(ABC):
    requires_user_confirmation = False

    def __init__(self, device, config: dict[str, Any] | None = None):
        self.device = device
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def test_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def test_category(self) -> str:
        raise NotImplementedError

    def setup(self) -> None:
        pass

    @abstractmethod
    def execute(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def validate(self) -> bool:
        raise NotImplementedError

    def teardown(self) -> None:
        pass

    def run_once(self) -> bool:
        self.setup()
        try:
            executed = self.execute()
            return bool(executed and self.validate())
        finally:
            self.teardown()

    def build_result(
        self,
        status: str,
        started_at: float,
        retry_count: int = 0,
        error: str | None = None,
        screenshot: str | None = None,
    ) -> TestResult:
        return TestResult(
            test_name=self.test_name,
            test_category=self.test_category,
            status=status,
            duration_ms=int((time.perf_counter() - started_at) * 1000),
            retry_count=retry_count,
            error=error,
            screenshot=screenshot,
        )
