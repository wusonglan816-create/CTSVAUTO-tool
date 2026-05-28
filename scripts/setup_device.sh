#!/bin/bash
set -e

DEVICE_ID=${1:-}
ADB_CMD=(adb)
if [ -n "$DEVICE_ID" ]; then
    ADB_CMD=(adb -s "$DEVICE_ID")
fi

if ! "${ADB_CMD[@]}" devices | grep -q "device$"; then
    echo "No Android device detected"
    exit 1
fi

if ! "${ADB_CMD[@]}" shell pm list packages | grep -q "com.android.cts.verifier"; then
    if [ -f "./apk/CtsVerifier.apk" ]; then
        "${ADB_CMD[@]}" install -r "./apk/CtsVerifier.apk"
    else
        echo "CTS Verifier is not installed and ./apk/CtsVerifier.apk is missing"
        exit 1
    fi
fi

"${ADB_CMD[@]}" shell settings put global window_animation_scale 0
"${ADB_CMD[@]}" shell settings put global transition_animation_scale 0
"${ADB_CMD[@]}" shell settings put global animator_duration_scale 0
"${ADB_CMD[@]}" shell svc power stayon usb
echo "Device setup complete"
