from __future__ import annotations

from typing import Any

from src.tests.base_test import BaseTest


class CtsVerifierLaunchSmokeTest(BaseTest):
    @property
    def test_name(self) -> str:
        return "CTS Verifier Launch Smoke Test"

    @property
    def test_category(self) -> str:
        return "smoke"

    def execute(self) -> bool:
        return True

    def validate(self) -> bool:
        expected_package = self.config.get("cts_verifier", {}).get(
            "package",
            "com.android.cts.verifier",
        )
        return self.device.get_current_package() == expected_package

    def teardown(self) -> None:
        pass
