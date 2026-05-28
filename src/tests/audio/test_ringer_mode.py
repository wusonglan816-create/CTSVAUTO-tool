from __future__ import annotations

import logging
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from src.core.exceptions import ElementNotFoundError, ValidationError
from src.tests.base_test import BaseTest


class RingerModeTest(BaseTest):
    @property
    def test_name(self) -> str:
        return "Ringer Mode Tests"

    @property
    def test_category(self) -> str:
        return "audio"

    def setup(self) -> None:
        self._return_to_cts_home()
        if not self.device.scroll_to_text(self.test_name, attempts=5):
            short_name = "Ringer Mode"
            if not self.device.scroll_to_text(short_name, attempts=5):
                raise ElementNotFoundError({"text": self.test_name}, 5)
        target = self.device.find_element({"text": self.test_name}, timeout=1)
        if target is None:
            target = self.device.require_element({"text_contains": self.test_name}, timeout=2)
        target.click()
        time.sleep(1)
        self._click_any(("OK", "Continue", "Next", "确定", "继续"), timeout=2)

    def execute(self) -> bool:
        # Step 1: Disable DND
        self._ensure_dnd(False)
        self._complete_instruction_after_return('Please disable "Do not disturb"', occurrence=0)
        time.sleep(2)

        # Step 2: Enable DND with Priority-Only (alarms) mode
        self._ensure_dnd(True)
        self._configure_dnd_interruptions()
        self._complete_instruction_after_return("Please enable Priority-Only", occurrence=0)
        time.sleep(5)

        # Step 3: Disable DND again
        self._ensure_dnd(False)
        self._complete_instruction_after_return('Please disable "Do not disturb"', occurrence=1)
        time.sleep(2)

        # Step 4: Enable Tap & click sounds
        self._ensure_tap_click_sounds()
        self._set_test_volumes_to_max()
        self._return_to_cts_verifier()
        return self._finish_ringer_mode_test()

    def validate(self) -> bool:
        self._assert_ringer_activity_active(allow_finished=True)
        if self._click_pass_if_enabled():
            return True
        raise ValidationError(self.test_name, "Ringer Mode test did not click an enabled Pass button")

    def teardown(self) -> None:
        self._return_to_cts_home()

    def _finish_ringer_mode_test(self) -> bool:
        hard_deadline = time.monotonic() + 600
        idle_deadline = time.monotonic() + 120
        last_signature = ""
        final_action_clicked = False
        final_action_retry_after = 0.0
        while time.monotonic() < hard_deadline:
            self.device.device_manager.wake_and_unlock()
            self.device.shell("cmd statusbar collapse")
            time.sleep(0.3)
            self._ensure_ringer_activity_active()
            signature = self._progress_signature()
            if signature and signature != last_signature:
                last_signature = signature
                idle_deadline = time.monotonic() + 120

            # Step 1: click the last instruction's action button
            if not final_action_clicked:
                if time.monotonic() >= final_action_retry_after:
                    if self._complete_final_tap_click_step():
                        final_action_clicked = True
                        time.sleep(2)
                        idle_deadline = time.monotonic() + 120
                    else:
                        final_action_retry_after = time.monotonic() + 20
                continue

            # Step 2: click the green Pass button (bottom-left)
            if self._click_pass_if_enabled():
                return True
            if time.monotonic() >= idle_deadline:
                break
            time.sleep(1)

        if self._click_fail_if_enabled():
            self._screenshot_debug("ringer_timeout_fail")
            return False
        self._screenshot_debug("ringer_timeout_no_fail_button")
        raise ValidationError(self.test_name, "Timed out waiting for enabled Pass button after document steps")

    def _complete_final_tap_click_step(self) -> bool:
        self.device.scroll_to_text("Please enable Tap & click sounds", attempts=6)
        action = self._find_enabled_action_for_instruction("Please enable Tap & click sounds", 0)
        if action is None:
            return False
        if not self._is_bottom_most_enabled_action(action):
            return False
        self._tap_bounds(action)
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            self.device.scroll_to_text("Please enable Tap & click sounds", attempts=2)
            if self._find_enabled_action_for_instruction("Please enable Tap & click sounds", 0) is None:
                return True
            time.sleep(0.5)
        return False

    # ── Profile helpers ──────────────────────────────────────────

    def _profile(self):
        return self.config.get("platform_profile")

    def _profile_values(self, key: str, default: list[str]) -> list[str]:
        profile = self._profile()
        return profile.values("ringer_mode", key, default) if profile else default

    def _profile_value(self, key: str, default: str) -> str:
        profile = self._profile()
        values = profile.test("ringer_mode") if profile else {}
        return values.get(key, default)

    def _shell_command(self, name: str, default: str) -> str:
        profile = self._profile()
        return profile.command("ringer_mode", name, default) if profile else default

    # ── DND tile labels across all platforms ─────────────────────

    def _dnd_tile_labels(self) -> list[str]:
        """Collect DND tile labels from profile + hardcoded fallbacks, deduped."""
        return list(dict.fromkeys(
            self._profile_values("dnd_tile_labels", ["Do Not Disturb"])
            + ["勿扰", "免打扰", "DND", "Modes", "请勿打扰", "Ne pas déranger"]
        ))

    # ── Quick settings: open ─────────────────────────────────────

    def _open_quick_settings(self) -> bool:
        """Open quick settings panel. Returns True if panel appears open."""
        self.device.device_manager.wake_and_unlock()

        # Method 1: shell command
        self.device.shell("cmd statusbar expand-settings")
        time.sleep(1.5)
        if self._is_quick_settings_open():
            return True

        # Method 2: collapse any stale state, then swipe down twice
        self.device.shell("cmd statusbar collapse")
        time.sleep(0.5)
        screen_w, screen_h = self._screen_size()
        # First swipe: notification shade
        self.device.shell(
            f"input swipe {screen_w // 2} 10 {screen_w // 2} {screen_h // 3} 300"
        )
        time.sleep(0.8)
        # Second swipe: expand to quick settings
        self.device.shell(
            f"input swipe {screen_w // 2} 10 {screen_w // 2} {screen_h // 3} 300"
        )
        time.sleep(1)
        if self._is_quick_settings_open():
            return True

        # Method 3: expand notifications then swipe down on shade
        self.device.shell("cmd statusbar collapse")
        time.sleep(0.5)
        self.device.shell("cmd statusbar expand-notifications")
        time.sleep(1)
        shade_y = max(screen_h // 8, 200)
        self.device.shell(
            f"input swipe {screen_w // 2} {shade_y} {screen_w // 2} {screen_h // 2} 400"
        )
        time.sleep(1)
        if self._is_quick_settings_open():
            return True

        self.logger.warning("Failed to open quick settings panel via any method")
        self._screenshot_debug("qs_open_failed")
        return False

    def _is_quick_settings_open(self) -> bool:
        """Check if quick settings panel is currently displayed."""
        # Most reliable: SystemUI is foreground when QS is open
        current = self.device.get_current_package()
        if current == "com.android.systemui":
            return True
        # Fallback: look for known tile descriptions
        probes = (
            "Wi-Fi", "WiFi", "Bluetooth", "Auto-rotate", "Flashlight",
            "Mobile data", "Airplane mode", "Hotspot",
            "蓝牙", "自动旋转", "手电筒", "移动数据", "飞行模式", "热点",
        )
        for label in probes:
            element = self.device.find_element({"description_contains": label}, timeout=0.3)
            if element is not None:
                return True
        return False

    # ── DND tile: find with pagination ───────────────────────────

    def _find_dnd_tile(self):
        """Find DND tile across quick-settings pages.
        Returns (bounds, checked, node_text) or None.
        Uses both find_element and XML dump for maximum coverage."""
        labels = self._dnd_tile_labels()

        # Phase 1: current page — find_element (fast, reliable when it works)
        found = self._find_tile_by_labels(labels)
        if found is not None:
            return self._element_to_tile_info(found)

        # Phase 2: current page — XML dump search (catches tiles
        # that find_element misses due to unusual content-descriptions)
        found = self._find_tile_in_xml(labels)
        if found is not None:
            return found

        # Phase 3: paginate horizontally (paged QS layout — stock Android)
        screen_w, screen_h = self._screen_size()
        for _ in range(6):
            self._swipe_qs_left(screen_w, screen_h)
            found = self._find_tile_by_labels(labels)
            if found is not None:
                return self._element_to_tile_info(found)
            found = self._find_tile_in_xml(labels)
            if found is not None:
                return found

        # Phase 4: scroll vertically (scrollable-grid QS layout — some OEMs)
        for _ in range(6):
            self._swipe_qs_up(screen_w, screen_h)
            found = self._find_tile_by_labels(labels)
            if found is not None:
                return self._element_to_tile_info(found)
            found = self._find_tile_in_xml(labels)
            if found is not None:
                return found

        self._log_qs_diagnostics()
        self._screenshot_debug("dnd_tile_not_found")
        return None

    def _find_tile_by_labels(self, labels: list[str]):
        """Find tile using uiautomator2 find_element. Returns element or None."""
        for label in labels:
            element = self.device.find_element({"description_contains": label}, timeout=1)
            if element is not None and self._is_tile_element(element):
                return element
            element = self.device.find_element({"text_contains": label}, timeout=1)
            if element is not None and self._is_tile_element(element):
                return element
        return None

    def _is_tile_element(self, element) -> bool:
        try:
            info = element.info
            bounds = self._extract_bounds(info)
            if bounds is None:
                rect = element.rect
                bounds = (rect["left"], rect["top"], rect["right"], rect["bottom"])
        except Exception:
            return False
        return self._is_tile_bounds(bounds)

    @staticmethod
    def _is_tile_bounds(bounds: tuple[int, int, int, int]) -> bool:
        x1, y1, x2, y2 = bounds
        return (x2 - x1) >= 120 and (y2 - y1) >= 80

    def _element_to_tile_info(self, element) -> tuple[tuple[int, int, int, int], bool | None, str]:
        """Convert a uiautomator2 element to (bounds, checked, text)."""
        info = element.info
        bounds = self._extract_bounds(info)
        if bounds is None:
            rect = element.rect
            bounds = (rect["left"], rect["top"], rect["right"], rect["bottom"])
        checked = info.get("checked")
        text = info.get("text", "")
        return bounds, checked, text

    @staticmethod
    def _extract_bounds(info: dict) -> tuple[int, int, int, int] | None:
        """Extract bounds from element info dict. Handles dict and string formats."""
        raw = info.get("bounds")
        if raw is None:
            return None
        if isinstance(raw, dict):
            return raw.get("left"), raw.get("top"), raw.get("right"), raw.get("bottom")
        if isinstance(raw, str):
            try:
                left_top, right_bottom = raw.split("][")
                x1, y1 = left_top.strip("[").split(",")
                x2, y2 = right_bottom.strip("]").split(",")
                return int(x1), int(y1), int(x2), int(y2)
            except (ValueError, IndexError):
                return None
        return None

    def _find_tile_in_xml(self, labels: list[str]) -> tuple[tuple[int, int, int, int], bool | None, str] | None:
        """Search XML hierarchy for DND tile — catches tiles with unusual attributes."""
        root = self._xml_root()
        if root is None:
            return None
        lowered_labels = [l.lower() for l in labels]
        for node in root.iter("node"):
            if node.attrib.get("clickable") != "true":
                continue
            text = (node.attrib.get("text") or "").lower()
            desc = (node.attrib.get("content-desc") or "").lower()
            if not any(label in text or label in desc for label in lowered_labels):
                continue
            bounds = self._parse_bounds(node.attrib.get("bounds", ""))
            if bounds is None or not self._is_tile_bounds(bounds):
                continue
            # Determine checked state from node or descendant Switch
            checked = self._node_checked_state(node)
            node_text = node.attrib.get("text") or node.attrib.get("content-desc") or ""
            return bounds, checked, node_text
        return None

    def _node_checked_state(self, node) -> bool | None:
        """Get checked state from a node, checking descendants for Switch widgets."""
        checked = node.attrib.get("checked")
        if checked is not None:
            return checked == "true"
        for child in node.iter("node"):
            if child.attrib.get("class") == "android.widget.Switch":
                val = child.attrib.get("checked")
                if val is not None:
                    return val == "true"
        return None

    def _swipe_qs_left(self, screen_w: int, screen_h: int) -> None:
        """Swipe quick settings page to the left (reveal next page)."""
        y = int(screen_h * 0.42)
        self.device.shell(
            f"input swipe {int(screen_w * 0.85)} {y} {int(screen_w * 0.15)} {y} 300"
        )
        time.sleep(0.8)

    def _swipe_qs_right(self, screen_w: int, screen_h: int) -> None:
        """Swipe quick settings page to the right (reveal previous page)."""
        y = int(screen_h * 0.42)
        self.device.shell(
            f"input swipe {int(screen_w * 0.15)} {y} {int(screen_w * 0.85)} {y} 300"
        )
        time.sleep(0.8)

    def _swipe_qs_up(self, screen_w: int, screen_h: int) -> None:
        """Scroll quick settings tiles upward (for grid-style QS layouts)."""
        self.device.shell(
            f"input swipe {screen_w // 2} {int(screen_h * 0.35)} "
            f"{screen_w // 2} {int(screen_h * 0.08)} 300"
        )
        time.sleep(0.8)

    # ── DND toggle: document UI flow ────────────────────────────

    def _ensure_dnd(self, enabled: bool) -> None:
        """Toggle DND state from the quick-settings tile."""
        if not self._open_quick_settings():
            raise ValidationError(self.test_name, "Document UI step failed: quick settings panel did not open")

        tile_info = self._find_dnd_tile()
        if tile_info is None:
            raise ValidationError(
                self.test_name,
                "Document UI step failed: DND quick settings tile not found. Check later QS pages or move the tile out of additional tiles into the active QS pages.",
            )

        bounds, checked, text = tile_info
        # Determine current checked state
        if checked is None:
            lower_text = text.lower()
            checked = ("on" in lower_text or "开" in lower_text) and "off" not in lower_text

        if bool(checked) != enabled:
            x1, y1, x2, y2 = bounds
            self.device.click((x1 + x2) // 2, (y1 + y2) // 2)
            time.sleep(1)

    def _dnd_shell_fallback(self, enabled: bool) -> None:
        """Set DND state via shell command."""
        self.device.shell("cmd statusbar collapse")
        time.sleep(0.5)
        if enabled:
            cmd = self._shell_command("enable_dnd", "cmd notification set_dnd alarms")
        else:
            cmd = self._shell_command("disable_dnd", "cmd notification set_dnd off")
        self.device.shell(cmd)
        time.sleep(1)

    # ── DND interruption config: document UI flow ───────────────

    def _configure_dnd_interruptions(self) -> None:
        """Configure DND interruptions from the DND settings screen."""
        if not self._open_quick_settings():
            raise ValidationError(self.test_name, "Document UI step failed: quick settings panel did not open")

        if not self._long_click_dnd_tile():
            raise ValidationError(
                self.test_name,
                "Document UI step failed: DND quick settings tile not found. Check later QS pages or move the tile out of additional tiles into the active QS pages.",
            )
        time.sleep(2)

        row_labels = list(dict.fromkeys(
            [self._profile_value("dnd_interruptions_row", "Alarms & other interruptions")]
            + ["Alarms & other interruptions", "Interruptions", "Apps",
               "People & apps", "Alarms & other sounds",
               "中断", "闹钟和其他中断", "闹钟和其他声音", "应用"]
        ))
        for label in row_labels:
            if self._click_settings_row_with_scroll(label):
                break
        else:
            self._screenshot_debug("dnd_interruptions_row_not_found")
            raise ValidationError(
                self.test_name,
                "Document UI step failed: settings row not found: Alarms & other interruptions",
            )

        time.sleep(1)
        enabled_labels = self._profile_values("dnd_interruptions_enabled", ["Alarms", "Media sounds"])
        disabled_labels = self._profile_values(
            "dnd_interruptions_disabled", ["Touch sounds", "Reminders", "Calendar events"]
        )
        for label in enabled_labels:
            self.device.scroll_to_text(label, attempts=4)
            if not self._set_settings_switch(label, True, required=False):
                for cn in self._chinese_settings_labels(label):
                    self.device.scroll_to_text(cn, attempts=4)
                    if self._set_settings_switch(cn, True, required=False):
                        break
        for label in disabled_labels:
            self.device.scroll_to_text(label, attempts=4)
            if not self._set_settings_switch(label, False, required=False):
                for cn in self._chinese_settings_labels(label):
                    self.device.scroll_to_text(cn, attempts=4)
                    if self._set_settings_switch(cn, False, required=False):
                        break

    def _long_click_dnd_tile(self) -> bool:
        tile_info = self._find_dnd_tile()
        if tile_info is None:
            return False
        bounds, _, _ = tile_info
        x1, y1, x2, y2 = bounds
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        self.device.shell(f"input swipe {cx} {cy} {cx} {cy} 1000")
        return True

    def _configure_dnd_shell_fallback(self) -> None:
        """Set DND to alarms-only mode via shell (equivalent to Priority-Only with alarms)."""
        self.device.shell("cmd statusbar collapse")
        time.sleep(0.5)
        cmd = self._shell_command("enable_dnd", "cmd notification set_dnd alarms")
        self.device.shell(cmd)
        time.sleep(1)

    def _set_test_volumes_to_max(self) -> None:
        """Prepare volume streams before CTS runs the post-DND volume checks."""
        self.device.shell("cmd audio set-ringer-mode NORMAL")
        for stream in ("MUSIC", "RING", "NOTIFICATION", "ALARM"):
            self.device.shell(f"cmd audio adj-volume {stream} UNMUTE")
            self.device.shell(f"cmd audio set-volume {stream} 100")
        time.sleep(0.5)

    @staticmethod
    def _chinese_settings_labels(english: str) -> list[str]:
        """Map English settings labels to possible Chinese equivalents."""
        mapping = {
            "Alarms": ["闹钟", "闹铃"],
            "Media sounds": ["媒体声音", "媒体"],
            "Touch sounds": ["触摸提示音", "触摸声音"],
            "Reminders": ["提醒"],
            "Calendar events": ["日历活动", "日历事件"],
        }
        return mapping.get(english, [])

    # ── Tap & click sounds: Settings UI → shell fallback ─────────

    def _ensure_tap_click_sounds(self) -> None:
        """Enable tap/click sounds via Settings app, with shell fallback."""
        self.device.shell("am start -a android.settings.SOUND_SETTINGS")
        time.sleep(2)
        all_labels = ("Tap & click sounds", "Touch sounds", "点击声音", "触摸提示音")
        for label in all_labels:
            self.device.scroll_to_text(label, attempts=6)
            if self._set_settings_switch(label, True, required=False):
                return
        # Shell fallback
        self.logger.info("Tap & click sounds setting not found in UI, using shell fallback")
        self._screenshot_debug("tap_sounds_not_found")
        cmd = self._shell_command("enable_tap_sounds", "settings put system sound_effects_enabled 1")
        self.device.shell(cmd)
        time.sleep(0.5)

    # ── Navigation ───────────────────────────────────────────────

    def _return_to_cts_verifier(self) -> None:
        """Return to CTS Verifier app from any other screen."""
        self.device.device_manager.wake_and_unlock()
        self.device.shell("cmd statusbar collapse")
        time.sleep(0.5)
        for _ in range(5):
            if self.device.get_current_package() == "com.android.cts.verifier":
                return
            self.device.press_back()
            time.sleep(1)
        # Last resort: relaunch CTS Verifier
        if self.device.get_current_package() != "com.android.cts.verifier":
            self.logger.info("Back navigation failed, relaunching CTS Verifier")
            self.device.shell(
                "am start -n com.android.cts.verifier/.CtsVerifierActivity"
            )
            time.sleep(2)

    def _return_to_cts_home(self) -> None:
        self._return_to_cts_verifier()
        for _ in range(5):
            current = self.device.u2.app_current()
            if current.get("package") == "com.android.cts.verifier" and current.get("activity", "").endswith(".CtsVerifierActivity"):
                return
            self.device.press_back()
            time.sleep(1)
        current = self.device.u2.app_current()
        if not (
            current.get("package") == "com.android.cts.verifier"
            and current.get("activity", "").endswith(".CtsVerifierActivity")
        ):
            raise ValidationError(self.test_name, "Unable to return to CTS Verifier home list")

    def _complete_instruction_after_return(
        self,
        text_fragment: str,
        occurrence: int = 0,
        wait_enabled: bool = False,
    ) -> None:
        self._return_to_cts_verifier()
        self._assert_ringer_activity_active()
        self.device.scroll_to_text(text_fragment, attempts=6)
        if wait_enabled:
            self._wait_for_enabled_action(text_fragment, occurrence=occurrence)
        self._click_action_for_instruction(text_fragment, occurrence=occurrence)
        time.sleep(1)

    def _assert_ringer_activity_active(self, allow_finished: bool = False) -> None:
        current = self.device.u2.app_current()
        package = current.get("package", "")
        activity = current.get("activity", "")
        if package != "com.android.cts.verifier":
            raise ValidationError(
                self.test_name,
                f"Ringer Mode test left CTS Verifier before automatic steps completed: {package}/{activity}",
            )
        if activity.endswith(".audio.RingerModeActivity"):
            return
        if allow_finished and activity.endswith(".CtsVerifierActivity"):
            return
        if self.device.find_element({"text": self.test_name}, timeout=0.5) is not None:
            raise ValidationError(
                self.test_name,
                "Ringer Mode test returned to the CTS list before automatic steps completed",
            )

    def _ensure_ringer_activity_active(self) -> None:
        current = self.device.u2.app_current()
        package = current.get("package", "")
        activity = current.get("activity", "")
        if package == "com.android.cts.verifier" and activity.endswith(".audio.RingerModeActivity"):
            return
        self.logger.warning(
            "Ringer Mode left target activity during automatic steps: %s/%s; attempting recovery",
            package,
            activity,
        )
        self.device.shell("am start -n com.android.cts.verifier/.audio.RingerModeActivity")
        time.sleep(2)
        self.device.shell("cmd statusbar collapse")
        time.sleep(0.5)
        current = self.device.u2.app_current()
        if current.get("package") == "com.android.cts.verifier" and current.get("activity", "").endswith(".audio.RingerModeActivity"):
            return
        self._assert_ringer_activity_active()

    # ── Screen size helper ───────────────────────────────────────

    def _screen_size(self) -> tuple[int, int]:
        """Get device screen dimensions."""
        output = self.device.shell("wm size")
        if hasattr(output, "stdout"):
            output = output.stdout
        match = re.search(r"Physical size:\s*(\d+)x(\d+)", str(output))
        if match:
            return int(match.group(1)), int(match.group(2))
        return 1080, 2400

    # ── Diagnostics ──────────────────────────────────────────────

    def _screenshot_debug(self, tag: str) -> None:
        """Save a diagnostic screenshot for debugging UI failures."""
        try:
            screenshot_dir = Path("./screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            path = screenshot_dir / f"debug_{tag}_{int(time.time())}.png"
            self.device.screenshot(str(path))
            self.logger.info("Debug screenshot saved: %s", path)
        except Exception as exc:
            self.logger.debug("Failed to save debug screenshot: %s", exc)

    def _log_qs_diagnostics(self) -> None:
        """Log all visible quick-settings tile texts/descriptions for debugging."""
        root = self._xml_root()
        if root is None:
            self.logger.warning("Could not dump UI hierarchy for QS diagnostics")
            return
        tiles = []
        for node in root.iter("node"):
            text = (node.attrib.get("text") or "").strip()
            desc = (node.attrib.get("content-desc") or "").strip()
            if text or desc:
                cls = node.attrib.get("class", "")
                if "tile" in cls.lower() or "Tile" in (text + desc):
                    tiles.append(f"text={text!r} desc={desc!r}")
        if tiles:
            self.logger.info("QS tiles found: %s", "; ".join(tiles[:20]))
        else:
            # Fallback: log any clickable elements
            clickables = []
            for node in root.iter("node"):
                if node.attrib.get("clickable") != "true":
                    continue
                text = (node.attrib.get("text") or "").strip()
                desc = (node.attrib.get("content-desc") or "").strip()
                if text or desc:
                    clickables.append(f"text={text!r} desc={desc!r}")
            self.logger.info(
                "No QS tile nodes found. Clickable elements: %s",
                "; ".join(clickables[:20]),
            )

    # ── XML / UI helpers ─────────────────────────────────────────

    def _click_settings_row(self, label: str) -> bool:
        row = self._find_clickable_row(label)
        if row is None:
            return False
        x1, y1, x2, y2 = row
        self.device.click((x1 + x2) // 2, (y1 + y2) // 2)
        return True

    def _click_settings_row_with_scroll(self, label: str, attempts: int = 5) -> bool:
        if self._click_settings_row(label):
            return True
        self.device.scroll_to_text(label, attempts=attempts)
        time.sleep(0.5)
        return self._click_settings_row(label)

    def _click_action_for_instruction(self, text_fragment: str, occurrence: int = 0) -> bool:
        action = self._find_action_for_instruction(text_fragment, occurrence)
        if action is None:
            raise ValidationError(
                self.test_name,
                f"Document UI step failed: action button not found for: {text_fragment}",
            )
        self._tap_bounds(action)
        return True

    def _click_enabled_action_for_instruction(self, text_fragment: str, occurrence: int = 0) -> bool:
        action = self._find_enabled_action_for_instruction(text_fragment, occurrence)
        if action is None:
            return False
        self._tap_bounds(action)
        return True

    def _wait_for_enabled_action(self, text_fragment: str, occurrence: int = 0, timeout: int = 20) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._find_enabled_action_for_instruction(text_fragment, occurrence) is not None:
                return
            time.sleep(0.5)
        raise ValidationError(
            self.test_name,
            f"Document UI step failed: action button not enabled for: {text_fragment}",
        )

    def _tap_bounds(self, bounds: tuple[int, int, int, int]) -> None:
        x1, y1, x2, y2 = bounds
        x = (x1 + x2) // 2
        y = (y1 + y2) // 2
        self.device.shell(f"input tap {x} {y}")
        time.sleep(0.5)

    def _set_settings_switch(self, label: str, enabled: bool, required: bool = True) -> bool:
        row = self._find_switch_row(label)
        if row is None:
            if required:
                raise ValidationError(self.test_name, f"Document UI step failed: switch row not found: {label}")
            return False
        checked, bounds = row
        if checked != enabled:
            x1, y1, x2, y2 = bounds
            self.device.click((x1 + x2) // 2, (y1 + y2) // 2)
            time.sleep(0.5)
        return True

    def _find_clickable_row(self, label: str) -> tuple[int, int, int, int] | None:
        root = self._xml_root()
        if root is None:
            return None
        for node in root.iter("node"):
            if node.attrib.get("clickable") != "true":
                continue
            if self._node_has_text(node, label):
                return self._parse_bounds(node.attrib.get("bounds", ""))
        return None

    def _find_switch_row(self, label: str) -> tuple[bool, tuple[int, int, int, int]] | None:
        root = self._xml_root()
        if root is None:
            return None
        for node in root.iter("node"):
            if node.attrib.get("clickable") != "true":
                continue
            if not self._node_has_text(node, label):
                continue
            switch = self._find_descendant_switch(node)
            bounds = self._parse_bounds(node.attrib.get("bounds", ""))
            if switch is not None and bounds is not None:
                return switch.attrib.get("checked") == "true", bounds
        return None

    def _find_action_for_instruction(self, text_fragment: str, occurrence: int) -> tuple[int, int, int, int] | None:
        root = self._xml_root()
        if root is None:
            return None
        matches: list[tuple[int, int, int, int]] = []
        for node in root.iter("node"):
            if node.attrib.get("resource-id") != "com.android.cts.verifier:id/nls_instructions":
                continue
            if text_fragment.lower() not in (node.attrib.get("text") or "").lower():
                continue
            bounds = self._parse_bounds(node.attrib.get("bounds", ""))
            if bounds is not None:
                matches.append(bounds)
        if not matches:
            return None
        instruction = matches[occurrence] if occurrence < len(matches) else matches[-1]
        return self._nearest_action_button(instruction)

    def _find_enabled_action_for_instruction(self, text_fragment: str, occurrence: int) -> tuple[int, int, int, int] | None:
        root = self._xml_root()
        if root is None:
            return None
        matches: list[tuple[int, int, int, int]] = []
        for node in root.iter("node"):
            if node.attrib.get("resource-id") != "com.android.cts.verifier:id/nls_instructions":
                continue
            if text_fragment.lower() not in (node.attrib.get("text") or "").lower():
                continue
            bounds = self._parse_bounds(node.attrib.get("bounds", ""))
            if bounds is not None:
                matches.append(bounds)
        if not matches:
            return None
        instruction = matches[occurrence] if occurrence < len(matches) else matches[-1]
        return self._nearest_enabled_action_button(instruction)

    def _nearest_action_button(self, instruction: tuple[int, int, int, int]) -> tuple[int, int, int, int] | None:
        root = self._xml_root()
        if root is None:
            return None
        _, _, _, instruction_bottom = instruction
        candidates: list[tuple[int, tuple[int, int, int, int]]] = []
        for node in root.iter("node"):
            if node.attrib.get("resource-id") != "com.android.cts.verifier:id/nls_action_button":
                continue
            bounds = self._parse_bounds(node.attrib.get("bounds", ""))
            if bounds is None:
                continue
            _, button_top, _, _ = bounds
            if button_top >= instruction_bottom:
                candidates.append((button_top - instruction_bottom, bounds))
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    def _nearest_enabled_action_button(self, instruction: tuple[int, int, int, int]) -> tuple[int, int, int, int] | None:
        root = self._xml_root()
        if root is None:
            return None
        _, _, _, instruction_bottom = instruction
        candidates: list[tuple[int, tuple[int, int, int, int]]] = []
        for node in root.iter("node"):
            if node.attrib.get("resource-id") != "com.android.cts.verifier:id/nls_action_button":
                continue
            if node.attrib.get("enabled") != "true":
                continue
            bounds = self._parse_bounds(node.attrib.get("bounds", ""))
            if bounds is None:
                continue
            _, button_top, _, _ = bounds
            if button_top >= instruction_bottom:
                candidates.append((button_top - instruction_bottom, bounds))
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    def _is_bottom_most_enabled_action(self, bounds: tuple[int, int, int, int]) -> bool:
        root = self._xml_root()
        if root is None:
            return False
        target_top = bounds[1]
        max_top = target_top
        found = False
        for node in root.iter("node"):
            if node.attrib.get("resource-id") != "com.android.cts.verifier:id/nls_action_button":
                continue
            if node.attrib.get("enabled") != "true":
                continue
            candidate = self._parse_bounds(node.attrib.get("bounds", ""))
            if candidate is None:
                continue
            found = True
            max_top = max(max_top, candidate[1])
        return found and target_top >= max_top

    def _xml_root(self):
        try:
            return ET.fromstring(self.device.u2.dump_hierarchy())
        except Exception:
            return None

    def _node_has_text(self, node, text: str) -> bool:
        needle = text.lower()
        for child in node.iter("node"):
            if needle in (child.attrib.get("text") or "").lower():
                return True
        return False

    def _find_descendant_switch(self, node):
        for child in node.iter("node"):
            if child.attrib.get("class") == "android.widget.Switch":
                return child
        return None

    def _parse_bounds(self, bounds: str) -> tuple[int, int, int, int] | None:
        try:
            left_top, right_bottom = bounds.split("][")
            x1, y1 = left_top.strip("[").split(",")
            x2, y2 = right_bottom.strip("]").split(",")
            return int(x1), int(y1), int(x2), int(y2)
        except ValueError:
            return None

    def _click_any(self, texts: tuple[str, ...], timeout: int = 1) -> bool:
        for text in texts:
            element = self.device.find_element({"text": text}, timeout=timeout)
            if element is None:
                element = self.device.find_element({"text_contains": text}, timeout=timeout)
            if element is not None:
                element.click()
                return True
        return False

    def _click_done_button(self) -> bool:
        """Click the 'I'M DONE' / 'Done' / 'I'm done' button (case-insensitive).

        CTS Verifier renders this button with varying case across platforms,
        so we search the XML hierarchy case-insensitively for any clickable
        element whose text contains ``done`` or ``完成``.
        """
        root = self._xml_root()
        if root is not None:
            candidates: list[tuple[int, int, int, int]] = []
            for node in root.iter("node"):
                text = (node.attrib.get("text") or "").strip()
                if not text:
                    continue
                text_lower = text.lower()
                if "done" not in text_lower and "完成" not in text_lower:
                    continue
                if node.attrib.get("enabled") == "false":
                    continue
                clickable = node.attrib.get("clickable") == "true"
                is_button = "Button" in (node.attrib.get("class") or "")
                if not clickable and not is_button:
                    continue
                bounds = self._parse_bounds(node.attrib.get("bounds", ""))
                if bounds is not None:
                    candidates.append(bounds)
            if candidates:
                # Click the bottom-most (last) done button on screen
                candidates.sort(key=lambda b: b[1])
                self._tap_bounds(candidates[-1])
                return True

        # Fallback: find_element with common case variants
        for label in ("I'M DONE", "I'm Done", "I'm done", "Im Done",
                      "DONE", "Done", "done", "完成"):
            element = self.device.find_element({"text_contains": label}, timeout=1)
            if element is not None:
                element.click()
                return True
        return False

    def _click_pass_if_enabled(self) -> bool:
        element = self.device.find_element(
            {"resource_id": "com.android.cts.verifier:id/pass_button"},
            timeout=1,
        )
        if element is not None:
            info = element.info
            if info.get("enabled", False):
                self._tap_bounds(self._element_bounds(element))
                return True
        return False

    def _click_fail_if_enabled(self) -> bool:
        element = self.device.find_element(
            {"resource_id": "com.android.cts.verifier:id/fail_button"},
            timeout=1,
        )
        if element is not None:
            info = element.info
            if info.get("enabled", False):
                self._tap_bounds(self._element_bounds(element))
                return True
        return False

    def _element_bounds(self, element) -> tuple[int, int, int, int]:
        info = element.info
        bounds = self._extract_bounds(info)
        if bounds is not None:
            return bounds
        rect = element.rect
        return rect["left"], rect["top"], rect["right"], rect["bottom"]

    def _visible_text(self) -> str:
        try:
            xml = self.device.u2.dump_hierarchy()
        except Exception:
            return ""
        return xml

    def _progress_signature(self) -> str:
        root = self._xml_root()
        if root is None:
            return ""
        parts: list[str] = []
        for node in root.iter("node"):
            rid = node.attrib.get("resource-id") or ""
            if rid not in (
                "com.android.cts.verifier:id/nls_status",
                "com.android.cts.verifier:id/nls_instructions",
                "com.android.cts.verifier:id/nls_action_button",
                "com.android.cts.verifier:id/pass_button",
            ):
                continue
            parts.append(
                "|".join(
                    [
                        rid,
                        node.attrib.get("text", ""),
                        node.attrib.get("content-desc", ""),
                        node.attrib.get("enabled", ""),
                        node.attrib.get("bounds", ""),
                    ]
                )
            )
        return "\n".join(parts)

    def _is_finished(self, visible_text: str) -> bool:
        pass_markers = self._profile_values(
            "pass_markers",
            ["All tests passed", "Passed", "PASS", "All Tests Passed"],
        )
        return any(marker in visible_text for marker in pass_markers)
