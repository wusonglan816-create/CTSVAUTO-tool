from __future__ import annotations

from collections.abc import Iterable

from src.tests.audio.test_ringer_mode import RingerModeTest
from src.tests.common.generic_ui_test import GenericCtsUiTest, TestCaseSpec
from src.tests.common.smoke_test import CtsVerifierLaunchSmokeTest


TEST_SPECS: list[TestCaseSpec] = [
    TestCaseSpec("CTS Verifier Launch Smoke Test", "smoke", "high", strategy="launch_smoke", timeout=10, module="SMOKE"),
    TestCaseSpec("Audio Acoustic Echo Cancellation (AEC) Test", "audio", "high", module="AUDIO"),
    TestCaseSpec("Ringer Mode Tests", "audio", "high", strategy="ringer_mode", timeout=120, module="AUDIO"),
    TestCaseSpec("Camera Flashlight", "camera", "high", strategy="ui_api", module="CAMERA"),
    TestCaseSpec("Camera Formats", "camera", "high", module="CAMERA"),
    TestCaseSpec("Screen Lock Test", "device_admin", "high", module="DEVICE ADMINISTRATION"),
    TestCaseSpec("Wi-Fi Test", "networking", "high", module="NETWORKING"),
    TestCaseSpec("Notification Listener Test", "notification", "high", module="NOTIFICATIONS"),
    TestCaseSpec("Has Vibrator Test", "vibrator", "high", strategy="ui_api", timeout=30, module="VIBRATIONS"),
    TestCaseSpec("Audio Frequency Line Test", "audio", "medium", module="AUDIO"),
    TestCaseSpec("Audio Frequency Speaker Test", "audio", "medium", module="AUDIO"),
    TestCaseSpec("Camera Intents", "camera", "medium", module="CAMERA"),
    TestCaseSpec("Camera Orientation", "camera", "medium", module="CAMERA"),
    TestCaseSpec("Device Admin Tapjacking Test", "device_admin", "medium", module="DEVICE ADMINISTRATION"),
    TestCaseSpec("Device Admin Uninstall Test", "device_admin", "medium", module="DEVICE ADMINISTRATION"),
    TestCaseSpec("Multinetwork connectivity Test", "networking", "medium", module="NETWORKING"),
    TestCaseSpec("Network Background Connectivity Test", "networking", "medium", module="NETWORKING"),
    TestCaseSpec("Bubble Notification Tests", "notification", "medium", module="NOTIFICATIONS"),
    TestCaseSpec("Sharesheet Payload Toggle Test", "sharesheet", "medium", module="SHARESHEET"),
    TestCaseSpec("Projection Video Playback Test", "projection", "low", timeout=120, module="PROJECTION TESTS"),
    TestCaseSpec("Streaming Video Quality Verifier", "streaming_video", "low", timeout=300, module="STREAMING"),
]


def iter_specs(
    category: str = "all",
    name_filter: str | None = None,
    automatable_only: bool = False,
    module: str = "all",
) -> Iterable[TestCaseSpec]:
    lowered_filter = name_filter.lower() if name_filter else None
    normalized_module = module.upper() if module != "all" else "all"
    for spec in TEST_SPECS:
        if category != "all" and spec.category != category:
            continue
        if normalized_module != "all" and spec.document_module.upper() != normalized_module:
            continue
        if lowered_filter and lowered_filter not in spec.name.lower():
            continue
        if automatable_only and not spec.automatable:
            continue
        yield spec


def build_tests(device, config: dict, specs: Iterable[TestCaseSpec]):
    tests = []
    for spec in specs:
        if spec.strategy == "launch_smoke":
            tests.append(CtsVerifierLaunchSmokeTest(device, config))
        elif spec.strategy == "ringer_mode":
            tests.append(RingerModeTest(device, config))
        else:
            tests.append(GenericCtsUiTest(device, spec, config))
    return tests


def categories() -> list[str]:
    return sorted({spec.category for spec in TEST_SPECS})


def modules() -> list[str]:
    return sorted({spec.document_module for spec in TEST_SPECS})
