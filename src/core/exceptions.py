from enum import Enum


class ErrorSeverity(Enum):
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class CTSVerifierError(Exception):
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.ERROR):
        self.message = message
        self.severity = severity
        super().__init__(message)


class DeviceDisconnectedError(CTSVerifierError):
    def __init__(self, device_id: str | None):
        label = device_id or "auto-detected"
        super().__init__(f"Device {label} disconnected", ErrorSeverity.CRITICAL)


class DeviceLockedError(CTSVerifierError):
    def __init__(self):
        super().__init__(
            "Device is locked. Unlock the screen, then rerun the command.",
            ErrorSeverity.CRITICAL,
        )


class ElementNotFoundError(CTSVerifierError):
    def __init__(self, selector: dict, timeout: int):
        super().__init__(
            f"Element not found: {selector} after {timeout}s",
            ErrorSeverity.ERROR,
        )


class AppCrashError(CTSVerifierError):
    def __init__(self, package: str):
        super().__init__(f"App {package} crashed", ErrorSeverity.ERROR)


class ADBCommandError(CTSVerifierError):
    def __init__(self, command: str, output: str):
        super().__init__(f"ADB command failed: {command}\nOutput: {output}", ErrorSeverity.ERROR)


class ValidationError(CTSVerifierError):
    def __init__(self, test_name: str, reason: str):
        super().__init__(
            f"Validation failed for {test_name}: {reason}",
            ErrorSeverity.WARNING,
        )
