from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from src.core.exceptions import ElementNotFoundError, ValidationError
from src.tests.base_test import BaseTest


@dataclass(frozen=True)
class TestCaseSpec:
    name: str
    category: str
    priority: str = "medium"
    automatable: bool = True
    strategy: str = "ui_text"
    timeout: int = 60
    notes: str = ""
    module: str = ""

    @property
    def document_module(self) -> str:
        return self.module or self.category.upper()


class GenericCtsUiTest(BaseTest):
    """Generic CTS Verifier flow for simple tests with visible pass/fail text."""

    def __init__(self, device, spec: TestCaseSpec, config: dict[str, Any] | None = None):
        super().__init__(device, config)
        self.spec = spec

    @property
    def test_name(self) -> str:
        return self.spec.name

    @property
    def test_category(self) -> str:
        return self.spec.category

    def setup(self) -> None:
        if not self.device.scroll_to_text(self.test_name, attempts=5):
            raise ElementNotFoundError({"text": self.test_name}, 5)
        target = self.device.find_element({"text": self.test_name}, timeout=1)
        if target is None:
            target = self.device.require_element({"text_contains": self.test_name}, timeout=2)
        target.click()
        time.sleep(1)
        self._dismiss_initial_prompts()

    def _dismiss_initial_prompts(self) -> None:
        for text in ("OK", "Allow", "Continue", "Next", "确定", "允许", "继续"):
            element = self.device.find_element({"text": text}, timeout=1)
            if element is not None:
                element.click()
                time.sleep(1)
                return

    def execute(self) -> bool:
        for text in ("Test", "Run", "Start", "开始", "运行", "Next"):
            element = self.device.find_element({"text": text}, timeout=2)
            if element is not None:
                element.click()
                time.sleep(self.config.get("validation", {}).get("wait_after_action", 1.0))
                return True
        return True

    def validate(self) -> bool:
        validation = self.config.get("validation", {})
        timeout = self.spec.timeout
        for text in validation.get("fail_texts", []):
            if self.device.find_element({"text_contains": text}, timeout=1):
                raise ValidationError(self.test_name, f"Found fail text: {text}")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for text in validation.get("pass_texts", []):
                if self.device.find_element({"text_contains": text}, timeout=1):
                    return True
            time.sleep(1)
        raise ValidationError(self.test_name, "No pass text found")

    def teardown(self) -> None:
        self.device.press_back()
