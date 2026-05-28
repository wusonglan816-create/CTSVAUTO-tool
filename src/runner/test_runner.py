from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Iterable

from src.core.config import deep_get
from src.core.device import DeviceManager
from src.core.exceptions import CTSVerifierError
from src.core.recovery import RecoveryHandler, RecoveryStrategy
from src.core.uiautomator_client import UIAutomatorClient
from src.platforms.profile import load_platform_profile, resolve_platform_name
from src.runner.progress import ProgressBar
from src.tests.base_test import BaseTest, TestResult
from src.tests.test_registry import build_tests


class TestRunner:
    def __init__(
        self,
        config: dict,
        device_id: str | None = None,
        retry_count: int | None = None,
        platform: str | None = "auto",
    ):
        self.config = config
        self.platform = platform or "auto"
        self.logger = logging.getLogger(self.__class__.__name__)
        device_cfg = config.get("device", {})
        advanced_cfg = config.get("advanced", {})
        self.device_manager = DeviceManager(
            device_id=device_id or device_cfg.get("device_id"),
            adb_path=advanced_cfg.get("adb_path"),
            wait_timeout=device_cfg.get("wait_timeout", 30),
        )
        retries = retry_count if retry_count is not None else deep_get(config, "test.retry_count", 3)
        self.recovery = RecoveryHandler(
            max_retries=int(retries),
            retry_delay=int(deep_get(config, "test.retry_delay", 5)),
        )
        self.results: list[TestResult] = []

    def setup(self) -> UIAutomatorClient:
        self.device_manager.connect()
        self.device_manager.adb.shell("svc power stayon usb", check=False)
        self.device_manager.adb.shell("settings put global stay_on_while_plugged_in 7", check=False)
        self.device_manager.adb.shell("settings put system screen_off_timeout 1800000", check=False)
        android_version = self.device_manager.get_device_info().get("android_version", "")
        platform_name = resolve_platform_name(self.platform, android_version)
        self.config["platform_profile"] = load_platform_profile(platform_name)
        self.device_manager.wake_and_unlock()
        package = deep_get(self.config, "cts_verifier.package")
        activity = deep_get(self.config, "cts_verifier.activity")
        self.device_manager.stop_app(package)
        time.sleep(1)
        self.device_manager.start_app(package, activity)
        time.sleep(2)
        return UIAutomatorClient(
            self.device_manager,
            wait_timeout=int(deep_get(self.config, "device.wait_timeout", 30)),
        )

    def run_test(self, test: BaseTest) -> TestResult:
        retry_count = 0
        package = deep_get(self.config, "cts_verifier.package")
        while retry_count <= self.recovery.max_retries:
            started_at = time.perf_counter()
            try:
                passed = test.run_once()
                return test.build_result(
                    "passed" if passed else "failed",
                    started_at,
                    retry_count=retry_count,
                )
            except CTSVerifierError as exc:
                strategy = self.recovery.handle(exc, retry_count)
                if strategy in (RecoveryStrategy.SKIP, RecoveryStrategy.ABORT):
                    return test.build_result(
                        "skipped" if strategy == RecoveryStrategy.SKIP else "failed",
                        started_at,
                        retry_count=retry_count,
                        error=exc.message,
                    )
                if not self.recovery.execute(strategy, self.device_manager, package):
                    return test.build_result(
                        "failed",
                        started_at,
                        retry_count=retry_count,
                        error=exc.message,
                    )
                retry_count += 1
            except Exception as exc:
                self.logger.exception("Unexpected error in %s", test.test_name)
                return test.build_result(
                    "failed",
                    started_at,
                    retry_count=retry_count,
                    error=str(exc),
                )

        return TestResult(test.test_name, test.test_category, "failed", 0, retry_count, "Retry limit reached")

    def run_suite(self, specs: Iterable, show_progress: bool = True) -> list[TestResult]:
        ui_client = self.setup()
        tests = build_tests(ui_client, self.config, specs)
        progress = ProgressBar(len(tests)) if show_progress else None
        for test in tests:
            result = self.run_test(test)
            self.results.append(result)
            if progress:
                progress.update(result.status, result.test_name)
            if result.status == "failed" and deep_get(self.config, "test.stop_on_failure", False):
                break
        if progress:
            progress.finish()
        return self.results

    def device_info(self) -> dict[str, str]:
        return self.device_manager.get_device_info()

    @staticmethod
    def ensure_output_dirs(config: dict) -> None:
        for key in ("report.output_dir", "device.screenshot_dir", "logging.file"):
            value = deep_get(config, key)
            if not value:
                continue
            path = Path(value)
            if path.suffix:
                path.parent.mkdir(parents=True, exist_ok=True)
            else:
                path.mkdir(parents=True, exist_ok=True)
