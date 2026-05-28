# Module Ledger

This ledger is for recurring CTS automation failures in this repo. Add new findings here before building more generic logic.

## AUDIO

### Ringer Mode Tests

- Symptom: host report generated before device-side test visibly finished.
  - Cause: script matched row status icons named `Pass` instead of the real bottom `pass_button`.
  - Guardrail: only use `resource-id=com.android.cts.verifier:id/pass_button` as final pass.

- Symptom: test occasionally started from the wrong CTS screen and then failed to find `Ringer Mode Tests`.
  - Cause: helper only checked CTS package, not whether it had returned to the CTS home list.
  - Guardrail: distinguish CTS home list from in-test activities.

- Symptom: `Do Not Disturb` tile not found.
  - Cause: tile may live on later QS pages, vertical grids, or additional tiles.
  - Guardrail: search multiple QS pages/grids and fail with an explicit "move tile into active QS pages" message if still absent.

- Symptom: final `Please enable Tap & click sounds` action did not progress.
  - Cause: the last row-specific button can remain visible while CTS is still in a transient state; generic `I'm done` searching may hit the wrong row.
  - Guardrail: target the specific final row, verify the row button state changes, and avoid global done-button searches during the final phase.

- Symptom: `Test volume change part 2` kept ringing and looked like it restarted.
  - Cause: repeated clicks on the same final action button retriggered the CTS flow.
  - Guardrail: click the final action once, then observe for a cooldown period before any retry.

- Symptom: CTS in-app taps looked like no-ops.
  - Cause: `NotificationShade` still covered the app.
  - Guardrail: collapse status bar before CTS in-app taps during recovery and final waiting.

- Symptom: last `Tap & click sounds` row completed manually, after which auto-pass worked.
  - Interpretation: remaining failures were in the final row action, not the final green pass logic.

## COMMON

### Generic UI navigation

- Treat `SoundSettingsActivity`, quick settings, and CTS sub-activities as valid transient states during UI automation.
- Prefer deterministic activity/package checks over vague text-only checks when returning to a known screen.
- On timeout or failure, preserve a screenshot before leaving the scene.

## PLATFORM

### Android 14/15/16 profiles

- Platform differences belong in profile data first:
  - tile label variations
  - settings row labels
  - localized labels
- Do not hardcode a single QS layout assumption across platform versions.

## REPORTING

- A host-side `passed` result is valid only when the device-side green `pass_button` was enabled and clicked.
- A host-side timeout should try to drive the device-side `fail_button` if present so the phone and report tell the same story.

## FUTURE MODULE TEMPLATE

When a new module fails, record:

1. Symptom as seen by the user.
2. Device-side page/activity where it stopped.
3. Actual root cause.
4. Guardrail that should prevent recurrence.
