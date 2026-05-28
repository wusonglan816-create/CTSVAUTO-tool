from __future__ import annotations


class UIValidator:
    def __init__(self, device):
        self.device = device

    def any_text_visible(self, texts: list[str], timeout: int = 5) -> bool:
        return any(self.device.find_element({"text_contains": text}, timeout=timeout) for text in texts)
