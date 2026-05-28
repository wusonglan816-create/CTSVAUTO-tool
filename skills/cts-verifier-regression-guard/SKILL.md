---
name: cts-verifier-regression-guard
description: Use when maintaining or extending this CTS Verifier automation repo, especially for audio and other CTS UI-driven modules that can fail due to timing, page state, quick-settings layout changes, or false pass/fail detection. Helps prevent repeated regressions by following repo-specific guardrails, debugging steps, and per-module issue records.
---

# CTS Verifier Regression Guard

Use this skill when changing CTS Verifier automation in this repo.

## Core workflow

1. Reproduce the failure on device when possible. Prefer a single test item such as `Ringer Mode`.
2. Separate three classes of failures before changing code:
   - Python/code exception
   - UI action not executed or not consumed by CTS
   - CTS automatic sub-test still running while host-side timeout/teardown fires
3. Only mark a test as passed when the real CTS bottom `pass_button` is enabled and clicked.
4. If the test times out and the CTS bottom `fail_button` is enabled, click it so the device-side state matches the host-side result.
5. Keep per-step actions idempotent. If a button can retrigger the same CTS sub-test, never spam it in a loop.

## Guardrails

- Do not treat status icons with `content-desc=Pass` as the final pass button.
- Do not use package-only checks to mean "returned to CTS home". Distinguish:
  - `com.android.cts.verifier/.CtsVerifierActivity`: CTS home list
  - `com.android.cts.verifier/.audio.RingerModeActivity`: still inside the test
- Collapse `NotificationShade` before any CTS in-app tap during recovery or end-of-test waiting.
- When using quick settings tiles, search:
  - current page
  - later horizontal pages
  - vertical scrollable grids
- If the tile still is not found, fail with a message that tells the operator to move the tile from additional tiles into active quick settings pages.
- For final confirmation buttons inside long CTS lists, verify the specific row/button pair instead of searching globally for generic text like `I'm done`.
- If a final CTS button must be clicked after a system-side action, click once and then observe; do not keep retriggering it in a tight loop.
- Prefer screenshots on timeout/fail exits so device-side evidence is preserved.

## Audio module rules

- `Ringer Mode Tests`:
  - First three `I'm done` buttons are normal step confirmations.
  - The last `I'm done` belongs to `Please enable Tap & click sounds in Sound settings.` and must be handled as a dedicated final-step action.
  - After enabling `Tap & click sounds`, set test volumes to max before returning.
  - After the final `I'm done`, CTS may take a long time in `Test volume change part 2/3`; keep waiting while the CTS page is still progressing.
  - Never re-click the final action button during the ringing phase unless you have verified CTS did not consume the click.
- Treat `SoundSettingsActivity` as a legitimate transient state, not a crash.
- If `Pass` does not enable after the final action and the page stops progressing for a long period, click device-side `Fail` if enabled.

## Per-module notes

- See [references/module-ledger.md](references/module-ledger.md) for issues, fixes, and carry-forward guardrails by module.

## Recommended debug order

1. Read `reports/report.html`.
2. Check current `app_current()` and focused window.
3. Dump only the CTS rows/buttons relevant to the failing step.
4. Confirm whether the device is at:
   - CTS home list
   - target test activity
   - quick settings
   - Android Settings
5. Only then patch the smallest piece of flow logic that explains the failure.
