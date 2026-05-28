#!/bin/bash
echo "=== CTS Verifier automation environment check ==="

ERRORS=0
WARNINGS=0

if python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "OK Python: $(python3 --version)"
else
    echo "ERROR Python 3.10+ is required"
    ERRORS=$((ERRORS + 1))
fi

if command -v adb >/dev/null 2>&1; then
    echo "OK ADB: $(adb --version | head -1)"
else
    echo "ERROR ADB not found"
    ERRORS=$((ERRORS + 1))
fi

for package in uiautomator2 yaml jinja2; do
    if python3 -c "import $package" >/dev/null 2>&1; then
        echo "OK Python package: $package"
    else
        echo "WARN Python package missing: $package"
        WARNINGS=$((WARNINGS + 1))
    fi
done

if adb devices 2>/dev/null | grep -q "device$"; then
    echo "OK Android device connected"
else
    echo "WARN no Android device detected"
    WARNINGS=$((WARNINGS + 1))
fi

if [ -f "apk/CtsVerifier.apk" ]; then
    echo "OK apk/CtsVerifier.apk exists"
else
    echo "WARN apk/CtsVerifier.apk not found"
    WARNINGS=$((WARNINGS + 1))
fi

echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"
exit "$ERRORS"
