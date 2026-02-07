from __future__ import annotations

from abc import ABC, abstractmethod

from PySide6 import QtWidgets

from zimo.core.api_client import ApiClient


class ModuleBase(ABC):
    title: str

    @abstractmethod
    def create_panel(self, api: ApiClient) -> QtWidgets.QWidget:
        raise NotImplementedError
