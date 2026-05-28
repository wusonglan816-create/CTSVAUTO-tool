from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from src.core.exceptions import ElementNotFoundError


class UIAutomatorClient:
    def __init__(self, device_manager, wait_timeout: int = 30):
        self.device_manager = device_manager
        self.u2 = device_manager.u2
        self.wait_timeout = wait_timeout

    def _selector(self, selector: dict[str, Any]):
        kwargs: dict[str, Any] = {}
        mapping = {
            "text": "text",
            "text_contains": "textContains",
            "resource_id": "resourceId",
            "description": "description",
            "description_contains": "descriptionContains",
            "class_name": "className",
        }
        for key, target in mapping.items():
            if key in selector:
                kwargs[target] = selector[key]
        return self.u2(**kwargs)

    def click(self, x: int, y: int) -> bool:
        self.u2.click(x, y)
        return True

    def click_element(self, selector: dict[str, Any], timeout: int | None = None) -> bool:
        element = self.find_element(selector, timeout)
        if element is None:
            raise ElementNotFoundError(selector, timeout or self.wait_timeout)
        element.click()
        return True

    def long_click_element(self, selector: dict[str, Any], timeout: int | None = None) -> bool:
        element = self.find_element(selector, timeout)
        if element is None:
            raise ElementNotFoundError(selector, timeout or self.wait_timeout)
        element.long_click()
        return True

    def find_element(self, selector: dict[str, Any], timeout: int | None = None):
        timeout = timeout if timeout is not None else self.wait_timeout
        element = self._selector(selector)
        if element.exists(timeout=timeout):
            return element
        return None

    def require_element(self, selector: dict[str, Any], timeout: int | None = None):
        timeout = timeout if timeout is not None else self.wait_timeout
        element = self.find_element(selector, timeout)
        if element is None:
            raise ElementNotFoundError(selector, timeout)
        return element

    def get_text(self, selector: dict[str, Any], timeout: int | None = None) -> str:
        element = self.require_element(selector, timeout)
        return element.info.get("text", "")

    def scroll_to_text(self, text: str, attempts: int = 3) -> bool:
        if self.find_element({"text": text}, timeout=1):
            return True
        if self.find_element({"text_contains": text}, timeout=1):
            return True
        try:
            self.u2(scrollable=True).scroll.to(text=text)
            if self.find_element({"text": text}, timeout=1):
                return True
        except Exception:
            pass
        try:
            self.u2(scrollable=True).scroll.to(textContains=text)
            if self.find_element({"text_contains": text}, timeout=1):
                return True
        except Exception:
            pass
        for _ in range(attempts):
            if self.find_element({"text": text}, timeout=1):
                return True
            if self.find_element({"text_contains": text}, timeout=1):
                return True
            self.u2.swipe_ext("up")
            time.sleep(0.5)
        return False

    def screenshot(self, save_path: str | None = None):
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            return self.u2.screenshot(save_path)
        return self.u2.screenshot()

    def wait_for_element(self, selector: dict[str, Any], timeout: int = 30) -> bool:
        return self.find_element(selector, timeout=timeout) is not None

    def get_current_activity(self) -> str:
        return self.u2.app_current().get("activity", "")

    def get_current_package(self) -> str:
        return self.u2.app_current().get("package", "")

    def press_back(self) -> None:
        self.u2.press("back")

    def press(self, key: str) -> None:
        self.u2.press(key)

    def shell(self, command: str):
        return self.device_manager.shell(command)
