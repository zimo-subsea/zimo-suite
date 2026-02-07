from __future__ import annotations

from typing import Protocol

from PySide6.QtWidgets import QWidget


class ModulePanel(Protocol):
    """Protocol for module panels."""

    def panel_name(self) -> str:
        ...


class BaseModule(QWidget):
    """Base widget for module panels."""

    def panel_name(self) -> str:
        return "Module"
