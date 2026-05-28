from __future__ import annotations

from abc import ABC, abstractmethod


class BaseValidator(ABC):
    @abstractmethod
    def validate(self) -> bool:
        raise NotImplementedError
