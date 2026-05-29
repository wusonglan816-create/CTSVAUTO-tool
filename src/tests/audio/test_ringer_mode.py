from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from src.core.exceptions import ElementNotFoundError, ValidationError
from src.tests.base_test import BaseTest


CTS_PACKAGE = "com.android.cts.verifier"
RINGER_ACTIVITY = ".audio.RingerModeActivity"
PASS_BUTTON_ID = f"{CTS_PACKAGE}:id/pass_button"
FAIL_BUTTON_ID = f"{CTS_PACKAGE}:id/fail_button"
ACTION_BUTTON_ID = f"{CTS_PACKAGE}:id/nls_action_button"


@dataclass(frozen=True)
class UiNode:
    text: str
    description: str
    resource_id: str
    class_name: str
    enabled: bool
    checked: bool
    bounds: tuple[int, int, int, int]

    @property
    def center(self) -> tuple[int, int]:
        left, top, right, bottom = self.bounds
        return (left + right) // 2, (top + bottom) // 2


class RingerModeTest(BaseTest):
    """Automates CTS Verifier Ringer Mode Tests in CTS source order."""

    @property
    def test_name(self) -> str:
        return "Ringer Mode Tests"

    @property
    def test_category(self) -> str:
        return "audio"

    def setup(self) -> None:
        self.profile = self.config.get("platform_profile")
        self.test_cfg = self.profile.test("ringer_mode") if self.profile else {}
        self.done_labels = self.test_cfg.get("done_buttons") or ["I'M DONE", "I’M DONE", "DONE"]
        self.dnd_tile_labels = self.test_cfg.get("dnd_tile_labels") or ["Do Not Disturb"]
        self._clear_logcat()
        self._prepare_ringer_test_start()

    def execute(self) -> bool:
        try:
            self._set_normal_audio_state()
            self._complete_disable_dnd_step(next_marker="next test is: SetModePriorityTest")
            self._complete_priority_dnd_step()
            self._wait_for_logcat_marker("next test is: SetModeAllTest", timeout=180, context="DND priority auto cases")

            self._complete_disable_dnd_step()
            self._wait_for_logcat_marker("next test is: EnableSoundEffects", timeout=240, context="normal-ringer auto cases")

            self._complete_tap_click_sounds_step()
            self._wait_for_pass_button(timeout=240)
            self._click_bottom_button(PASS_BUTTON_ID, require_enabled=True)
            self._passed_on_device = True
            return True
        except Exception as exc:
            self._click_fail_on_failure()
            if isinstance(exc, ValidationError):
                raise
            raise ValidationError(self.test_name, str(exc)) from exc

    def validate(self) -> bool:
        return bool(getattr(self, "_passed_on_device", False))

    def teardown(self) -> None:
        self._run_shell(self._command("disable_dnd", "cmd notification set_dnd off"), timeout=10)
        self._run_shell(self._command("set_ringer_normal", "cmd audio set-ringer-mode NORMAL"), timeout=10)
        self._collapse_status_bar()

    def _prepare_ringer_test_start(self) -> None:
        self._collapse_status_bar()
        current = self._current_app()
        if self._is_ringer_activity(current):
            return

        if not self.device.scroll_to_text(self.test_name, attempts=8):
            raise ElementNotFoundError({"text": self.test_name}, 8)
        target = self.device.find_element({"text": self.test_name}, timeout=1)
        if target is None:
            target = self.device.require_element({"text_contains": self.test_name}, timeout=2)
        target.click()
        time.sleep(2)
        self._dismiss_initial_prompts()
        self._ensure_ringer_activity()

    def _dismiss_initial_prompts(self) -> None:
        for text in ("OK", "Allow", "Continue", "Next", "确定", "允许", "继续"):
            element = self.device.find_element({"text": text}, timeout=1)
            if element is not None:
                element.click()
                time.sleep(0.8)

    def _complete_disable_dnd_step(self, next_marker: str | None = None) -> None:
        self._set_dnd(False)
        self._return_to_ringer_activity()
        self._click_done_for_instruction(['Please disable "Do not disturb"', "Please disable"])
        if next_marker:
            self._wait_for_logcat_marker(next_marker, timeout=60, context="disable DND")

    def _complete_priority_dnd_step(self) -> None:
        self._set_dnd(True)
        self._configure_priority_dnd_from_tile()
        self._return_to_ringer_activity()
        self._click_done_for_instruction(["Priority-Only", "Please enable Priority"])
        self._wait_for_logcat_marker("next test is: TestAccessRingerModeDndOn", timeout=60, context="priority DND")

    def _complete_tap_click_sounds_step(self) -> None:
        self._run_shell(self._command("enable_tap_sounds", "settings put system sound_effects_enabled 1"), timeout=10)
        self._set_test_volumes_to_max()
        self._return_to_ringer_activity()
        self._click_done_for_instruction(["Please enable Tap & click sounds", "Tap & click sounds"])

    def _set_normal_audio_state(self) -> None:
        self._run_shell(self._command("disable_dnd", "cmd notification set_dnd off"), timeout=10)
        self._run_shell(self._command("set_ringer_normal", "cmd audio set-ringer-mode NORMAL"), timeout=10)

    def _set_dnd(self, enabled: bool) -> None:
        self._open_quick_settings()
        tile = self._find_dnd_tile()
        if tile is None:
            raise ValidationError(
                self.test_name,
                "Do Not Disturb quick-settings tile not found. Move the tile into an active QS page.",
            )

        current = self._zen_mode()
        needs_click = (enabled and current == "0") or (not enabled and current != "0")
        if needs_click:
            self._tap_node(tile)
            time.sleep(1.5)

        command_key = "enable_dnd" if enabled else "disable_dnd"
        default = "cmd notification set_dnd alarms" if enabled else "cmd notification set_dnd off"
        self._run_shell(self._command(command_key, default), timeout=10)
        time.sleep(1)
        self._collapse_status_bar()

    def _configure_priority_dnd_from_tile(self) -> None:
        self._open_quick_settings()
        tile = self._find_dnd_tile()
        if tile is None:
            raise ValidationError(
                self.test_name,
                "Do Not Disturb quick-settings tile not found for long-press configuration.",
            )
        x, y = tile.center
        self.device.u2.long_click(x, y, duration=1.2)
        time.sleep(2)

        row = self.test_cfg.get("dnd_interruptions_row", "Alarms & other interruptions")
        self._click_text_or_contains(row, timeout=6, scroll=True)
        time.sleep(1)
        for label in self.test_cfg.get("dnd_interruptions_enabled", ["Alarms", "Media sounds"]):
            self._set_settings_switch(label, checked=True)
        for label in self.test_cfg.get(
            "dnd_interruptions_disabled",
            ["Touch sounds", "Reminders", "Calendar events"],
        ):
            self._set_settings_switch(label, checked=False)

    def _set_settings_switch(self, label: str, checked: bool) -> None:
        if not self._scroll_to_text(label, attempts=4):
            return
        node, switch = self._find_label_and_nearby_switch(label)
        if node is None:
            return
        if switch is None:
            self._tap_node(node)
            time.sleep(0.6)
            return
        if switch.checked != checked:
            self._tap_node(switch)
            time.sleep(0.6)

    def _wait_for_instruction(self, fragments: list[str], timeout: int, context: str) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self._raise_if_device_side_failed(context)
            if self._has_text(fragments):
                return
            if self._bottom_button_enabled(PASS_BUTTON_ID):
                return
            time.sleep(1)
        raise ValidationError(self.test_name, f"Timed out waiting for instruction during {context}")

    def _wait_for_logcat_marker(self, marker: str, timeout: int, context: str) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self._raise_if_device_side_failed(context)
            output = self._run_adb(["logcat", "-d", "-t", "800"], timeout=8)
            if marker in output:
                return
            time.sleep(1)
        raise ValidationError(self.test_name, f"Timed out waiting for CTS progress marker during {context}: {marker}")

    def _wait_for_pass_button(self, timeout: int) -> None:
        deadline = time.monotonic() + timeout
        last_scroll = 0.0
        while time.monotonic() < deadline:
            self._raise_if_device_side_failed("final pass wait")
            self._collapse_status_bar()
            if self._bottom_button_enabled(PASS_BUTTON_ID):
                return
            if time.monotonic() - last_scroll > 8:
                self.device.u2.swipe_ext("down")
                last_scroll = time.monotonic()
            time.sleep(1)
        raise ValidationError(self.test_name, "Device-side pass_button did not become enabled")

    def _click_done_for_instruction(self, fragments: list[str]) -> None:
        self._collapse_status_bar()
        button = self._find_done_button_for_instruction(fragments)
        if button is None:
            if not self._scroll_to_text(fragments[0], attempts=5):
                raise ValidationError(self.test_name, f"Cannot find instruction: {fragments[0]}")
            button = self._find_done_button_for_instruction(fragments)
        if button is None:
            button = self._find_enabled_done_button()
        if button is None:
            raise ValidationError(self.test_name, f"Cannot find enabled I'm done button for {fragments[0]}")
        self._tap_node(button)
        time.sleep(1.2)

    def _find_done_button_for_instruction(self, fragments: list[str]) -> UiNode | None:
        root = self._dump_xml()
        candidates: list[tuple[int, UiNode]] = []

        def walk(element: ET.Element) -> None:
            nodes = [self._node_from_xml(item) for item in element.iter()]
            has_instruction = any(
                self._node_text_matches(node, fragments) for node in nodes
            )
            if has_instruction:
                for node in nodes:
                    if self._is_done_button(node):
                        left, top, right, bottom = self._element_bounds(element)
                        candidates.append((max(0, bottom - top) + max(0, right - left), node))
            for child in element:
                walk(child)

        walk(root)
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    def _find_enabled_done_button(self) -> UiNode | None:
        for node in self._dump_nodes():
            if self._is_done_button(node):
                return node
        return None

    def _is_done_button(self, node: UiNode) -> bool:
        return (
            node.enabled
            and node.resource_id == ACTION_BUTTON_ID
            and self._normalize(node.text) in {self._normalize(label) for label in self.done_labels}
        )

    def _open_quick_settings(self) -> None:
        self._run_shell("cmd statusbar expand-settings", timeout=5)
        time.sleep(1)
        if self._current_app().get("package") == "com.android.systemui":
            return
        width, height = self._screen_size()
        for _ in range(2):
            self._run_shell(
                f"input swipe {width // 2} 10 {width // 2} {height // 2} 300",
                timeout=5,
            )
            time.sleep(0.8)

    def _find_dnd_tile(self) -> UiNode | None:
        seen_signatures: set[str] = set()
        for direction in ("current", "left", "left", "left", "right", "right", "up", "down"):
            signature = self._hierarchy_signature()
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                tile = self._find_node_by_text_or_description(self.dnd_tile_labels)
                if tile is not None:
                    return tile

            if direction == "left":
                self.device.u2.swipe_ext("left")
            elif direction == "right":
                self.device.u2.swipe_ext("right")
            elif direction == "up":
                self.device.u2.swipe_ext("up")
            elif direction == "down":
                self.device.u2.swipe_ext("down")
            time.sleep(0.8)
        return None

    def _find_node_by_text_or_description(self, labels: list[str]) -> UiNode | None:
        for node in self._dump_nodes():
            haystacks = (node.text, node.description)
            if any(self._contains_any(value, labels) for value in haystacks):
                return node
        return None

    def _click_text_or_contains(self, text: str, timeout: int = 5, scroll: bool = False) -> None:
        if scroll:
            self._scroll_to_text(text, attempts=4)
        element = self.device.find_element({"text": text}, timeout=timeout)
        if element is None:
            element = self.device.find_element({"text_contains": text}, timeout=timeout)
        if element is None:
            raise ElementNotFoundError({"text_contains": text}, timeout)
        element.click()

    def _scroll_to_text(self, text: str, attempts: int) -> bool:
        return self.device.scroll_to_text(text, attempts=attempts)

    def _find_label_and_nearby_switch(self, label: str) -> tuple[UiNode | None, UiNode | None]:
        nodes = self._dump_nodes()
        label_nodes = [node for node in nodes if self._contains_any(node.text, [label])]
        if not label_nodes:
            return None, None
        label_node = label_nodes[0]
        switches = [
            node for node in nodes
            if "Switch" in node.class_name or node.class_name.endswith("CheckBox")
        ]
        if not switches:
            return label_node, None
        lx1, ly1, lx2, ly2 = label_node.bounds
        same_row = [
            switch for switch in switches
            if min(abs(switch.bounds[1] - ly1), abs(switch.bounds[3] - ly2)) < 120
        ]
        if same_row:
            return label_node, same_row[0]
        return label_node, min(switches, key=lambda item: abs(item.bounds[1] - ly1))

    def _return_to_ringer_activity(self) -> None:
        self._collapse_status_bar()
        for _ in range(5):
            current = self._current_app()
            if self._is_ringer_activity(current):
                return
            self.device.press_back()
            time.sleep(1)
        self._run_shell(f"am start -n {CTS_PACKAGE}/{CTS_PACKAGE}{RINGER_ACTIVITY}", timeout=10)
        time.sleep(2)
        self._ensure_ringer_activity()

    def _ensure_ringer_activity(self) -> None:
        current = self._current_app()
        if not self._is_ringer_activity(current):
            raise ValidationError(self.test_name, f"Not in RingerModeActivity: {current}")

    def _click_bottom_button(self, resource_id: str, require_enabled: bool) -> bool:
        button = self.device.find_element({"resource_id": resource_id}, timeout=2)
        if button is None:
            return False
        if require_enabled and not button.info.get("enabled", False):
            return False
        button.click()
        time.sleep(1)
        return True

    def _click_fail_on_failure(self) -> None:
        self._collapse_status_bar()
        self._click_bottom_button(FAIL_BUTTON_ID, require_enabled=False)

    def _bottom_button_enabled(self, resource_id: str) -> bool:
        button = self.device.find_element({"resource_id": resource_id}, timeout=1)
        return bool(button is not None and button.info.get("enabled", False))

    def _raise_if_device_side_failed(self, context: str) -> None:
        output = self._run_adb(["logcat", "-d", "-t", "300"], timeout=8)
        fail_markers = (
            "InteractiveVerifier: FAIL:",
            "InteractiveVerifier: failed",
            "RingerModeActivity: failed",
            "failed Test",
        )
        if any(marker in output for marker in fail_markers):
            raise ValidationError(self.test_name, f"Device-side subcase failed during {context}")

    def _clear_logcat(self) -> None:
        self._run_adb(["logcat", "-c"], timeout=8)

    def _set_test_volumes_to_max(self) -> None:
        for stream in (1, 2, 3, 4, 5):
            self._run_shell(f"cmd media_session volume --stream {stream} --set 15", timeout=5)
            self._run_shell(f"cmd audio set-stream-volume {stream} 15", timeout=5)

    def _zen_mode(self) -> str:
        output = self._run_shell("settings get global zen_mode", timeout=5)
        return output.strip() or "unknown"

    def _has_text(self, fragments: list[str]) -> bool:
        return any(self._node_text_matches(node, fragments) for node in self._dump_nodes())

    def _node_text_matches(self, node: UiNode, fragments: list[str]) -> bool:
        return self._contains_any(node.text, fragments) or self._contains_any(node.description, fragments)

    def _contains_any(self, value: str, fragments: list[str]) -> bool:
        normalized = self._normalize(value)
        return bool(normalized) and any(self._normalize(fragment) in normalized for fragment in fragments)

    def _normalize(self, value: str) -> str:
        return value.replace("’", "'").replace("\u00a0", " ").strip().lower()

    def _tap_node(self, node: UiNode) -> None:
        x, y = node.center
        self.device.click(x, y)

    def _dump_nodes(self) -> list[UiNode]:
        return [self._node_from_xml(element) for element in self._dump_xml().iter()]

    def _dump_xml(self) -> ET.Element:
        xml = self.device.u2.dump_hierarchy(compressed=False)
        return ET.fromstring(xml)

    def _node_from_xml(self, element: ET.Element) -> UiNode:
        bounds = self._parse_bounds(element.attrib.get("bounds", ""))
        return UiNode(
            text=element.attrib.get("text", ""),
            description=element.attrib.get("content-desc", ""),
            resource_id=element.attrib.get("resource-id", ""),
            class_name=element.attrib.get("class", ""),
            enabled=element.attrib.get("enabled", "true") == "true",
            checked=element.attrib.get("checked", "false") == "true",
            bounds=bounds,
        )

    def _element_bounds(self, element: ET.Element) -> tuple[int, int, int, int]:
        own = self._parse_bounds(element.attrib.get("bounds", ""))
        child_bounds = [self._parse_bounds(item.attrib.get("bounds", "")) for item in element.iter()]
        valid = [bounds for bounds in [own, *child_bounds] if bounds != (0, 0, 0, 0)]
        if not valid:
            return own
        return (
            min(bounds[0] for bounds in valid),
            min(bounds[1] for bounds in valid),
            max(bounds[2] for bounds in valid),
            max(bounds[3] for bounds in valid),
        )

    def _parse_bounds(self, value: str) -> tuple[int, int, int, int]:
        match = re.match(r"\[(\d+),(\d+)]\[(\d+),(\d+)]", value or "")
        if not match:
            return (0, 0, 0, 0)
        return tuple(int(part) for part in match.groups())  # type: ignore[return-value]

    def _hierarchy_signature(self) -> str:
        return "|".join(f"{node.text}:{node.description}:{node.bounds}" for node in self._dump_nodes())

    def _collapse_status_bar(self) -> None:
        self._run_shell("cmd statusbar collapse", timeout=5)
        time.sleep(0.5)

    def _is_ringer_activity(self, current: dict[str, str]) -> bool:
        activity = current.get("activity", "")
        return current.get("package") == CTS_PACKAGE and activity.endswith("audio.RingerModeActivity")

    def _screen_size(self) -> tuple[int, int]:
        output = self._run_shell("wm size", timeout=5)
        match = re.search(r"Physical size:\s*(\d+)x(\d+)", output)
        if not match:
            return 720, 1280
        return int(match.group(1)), int(match.group(2))

    def _current_app(self) -> dict[str, str]:
        try:
            return self.device.u2.app_current()
        except Exception:
            return {"package": self.device.get_current_package(), "activity": self.device.get_current_activity()}

    def _command(self, key: str, default: str) -> str:
        if self.profile:
            return self.profile.command("ringer_mode", key, default)
        return default

    def _run_shell(self, command: str, timeout: int = 30) -> str:
        try:
            result = self.device.device_manager.adb.shell(command, timeout=timeout, check=False)
            return result.stdout or result.stderr or ""
        except AttributeError:
            result = self.device.shell(command)
            if isinstance(result, tuple):
                return str(result[0])
            return str(result)

    def _run_adb(self, args: list[str], timeout: int = 30) -> str:
        try:
            result = self.device.device_manager.adb.run(args, timeout=timeout, check=False)
            return result.stdout or result.stderr or ""
        except AttributeError:
            return ""
