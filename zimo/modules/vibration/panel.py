from __future__ import annotations

from PySide6 import QtWidgets

from zimo.core.api_client import ApiClient
from zimo.core.module_base import ModuleBase


class VibrationModule(ModuleBase):
    title = "Vibration"

    def create_panel(self, api: ApiClient) -> QtWidgets.QWidget:
        return VibrationPanel()


class VibrationPanel(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("Vibration")
        title.setObjectName("PageTitle")
        subtitle = QtWidgets.QLabel("Module placeholder – connect to vibration API endpoints.")
        subtitle.setObjectName("PageSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()
