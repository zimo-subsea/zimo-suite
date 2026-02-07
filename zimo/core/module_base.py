from __future__ import annotations

from abc import ABC, abstractmethod

from PySide6.QtWidgets import QWidget


class ModuleBase(QWidget, ABC):
    """Base class for pluggable ZiMO modules."""

    @property
    @abstractmethod
    def module_name(self) -> str:
        raise NotImplementedError
