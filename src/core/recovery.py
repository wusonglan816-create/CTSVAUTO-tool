from __future__ import annotations

import logging
import time
from enum import Enum

from src.core.exceptions import (
    AppCrashError,
    CTSVerifierError,
    DeviceDisconnectedError,
    ElementNotFoundError,
    ValidationError,
)


class RecoveryStrategy(Enum):
    RETRY = "retry"
    SKIP = "skip"
    ABORT = "abort"
    RECONNECT = "reconnect"
    RESTART_APP = "restart_app"


class RecoveryHandler:
    def __init__(self, max_retries: int = 3, retry_delay: int = 5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(self.__class__.__name__)

    def handle(self, error: CTSVerifierError, retry_count: int) -> RecoveryStrategy:
        if isinstance(error, DeviceDisconnectedError):
            return RecoveryStrategy.RECONNECT if retry_count < self.max_retries else RecoveryStrategy.ABORT
        if isinstance(error, ElementNotFoundError):
            return RecoveryStrategy.RETRY if retry_count < self.max_retries else RecoveryStrategy.SKIP
        if isinstance(error, AppCrashError):
            return RecoveryStrategy.RESTART_APP if retry_count < self.max_retries else RecoveryStrategy.SKIP
        if isinstance(error, ValidationError):
            return RecoveryStrategy.SKIP
        return RecoveryStrategy.RETRY if retry_count < self.max_retries else RecoveryStrategy.SKIP

    def execute(self, strategy: RecoveryStrategy, device=None, package: str | None = None) -> bool:
        if strategy == RecoveryStrategy.RETRY:
            time.sleep(self.retry_delay)
            return True
        if strategy == RecoveryStrategy.SKIP:
            return True
        if strategy == RecoveryStrategy.ABORT:
            return False
        if strategy == RecoveryStrategy.RECONNECT:
            return bool(device and device.reconnect())
        if strategy == RecoveryStrategy.RESTART_APP:
            if not device or not package:
                return False
            device.stop_app(package)
            time.sleep(2)
            device.start_app(package)
            return True
        return True
