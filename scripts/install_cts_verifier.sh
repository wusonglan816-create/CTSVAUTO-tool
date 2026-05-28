#!/bin/bash
set -e

APK_PATH=${1:-"./apk/CtsVerifier.apk"}
DEVICE_ID=${2:-}

if [ ! -f "$APK_PATH" ]; then
    echo "APK not found: $APK_PATH"
    exit 1
fi

ADB_CMD=(adb)
if [ -n "$DEVICE_ID" ]; then
    ADB_CMD=(adb -s "$DEVICE_ID")
fi

"${ADB_CMD[@]}" install -r "$APK_PATH"
"${ADB_CMD[@]}" shell pm list packages | grep "com.android.cts.verifier"
echo "CTS Verifier installed"
