from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from zimo.core.api_client import ApiClient
from zimo.core.module_base import BaseModule


class VibrationPanel(BaseModule):
    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.api_client = api_client

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        header = QLabel("Vibration Module")
        header.setObjectName("ModuleHeader")

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(8)

        card_layout.addWidget(QLabel("Module placeholder"))

        layout.addWidget(header)
        layout.addWidget(card)
        layout.addStretch()

    def panel_name(self) -> str:
        return "Vibration"
