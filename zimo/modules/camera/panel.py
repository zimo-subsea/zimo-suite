from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from zimo.core.api_client import ApiClient
from zimo.core.module_base import ModuleBase


class CameraModule(ModuleBase):
    title = "Camera"

    def create_panel(self, api: ApiClient) -> QtWidgets.QWidget:
        return CameraPanel(api)


class CameraPanel(QtWidgets.QWidget):
    def __init__(self, api: ApiClient) -> None:
        super().__init__()
        self._api = api

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        header = QtWidgets.QLabel("Camera Overview")
        header.setObjectName("PageTitle")
        subtitle = QtWidgets.QLabel("Monitor the machine vision feed and adjust capture settings.")
        subtitle.setObjectName("PageSubtitle")

        layout.addWidget(header)
        layout.addWidget(subtitle)

        cards_layout = QtWidgets.QHBoxLayout()
        cards_layout.setSpacing(16)

        status_card = self._build_status_card()
        control_card = self._build_control_card()

        cards_layout.addWidget(status_card, 1)
        cards_layout.addWidget(control_card, 1)

        layout.addLayout(cards_layout)

        layout.addStretch()

    def _build_status_card(self) -> QtWidgets.QWidget:
        card = QtWidgets.QWidget()
        card.setObjectName("Card")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QtWidgets.QLabel("Status")
        title.setObjectName("CardTitle")

        status = self._api.get_camera_status()
        state = QtWidgets.QLabel("Streaming" if status.is_streaming else "Idle")
        state.setObjectName("StatusPill")
        state.setProperty("severity", "success" if status.is_streaming else "neutral")

        temp = QtWidgets.QLabel(f"Temperature: {status.temperature_c:.1f} °C")
        temp.setObjectName("CardValue")
        last_frame = QtWidgets.QLabel(f"Last frame: {status.last_frame.strftime('%H:%M:%S UTC')}")
        last_frame.setObjectName("CardMeta")

        layout.addWidget(title)
        layout.addWidget(state)
        layout.addWidget(temp)
        layout.addWidget(last_frame)
        layout.addStretch()
        return card

    def _build_control_card(self) -> QtWidgets.QWidget:
        card = QtWidgets.QWidget()
        card.setObjectName("Card")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("Capture Settings")
        title.setObjectName("CardTitle")

        exposure_label = QtWidgets.QLabel("Exposure")
        exposure_slider = self._build_slider()

        gain_label = QtWidgets.QLabel("Gain")
        gain_slider = self._build_slider()

        sync_label = QtWidgets.QLabel("Sync Mode")
        sync_toggle = QtWidgets.QPushButton("Auto")
        sync_toggle.setCheckable(True)
        sync_toggle.setCursor(QtCore.Qt.PointingHandCursor)

        layout.addWidget(title)
        layout.addWidget(exposure_label)
        layout.addWidget(exposure_slider)
        layout.addWidget(gain_label)
        layout.addWidget(gain_slider)
        layout.addWidget(sync_label)
        layout.addWidget(sync_toggle)
        layout.addStretch()

        return card

    @staticmethod
    def _build_slider() -> QtWidgets.QSlider:
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(40)
        return slider


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    panel = CameraPanel(ApiClient())
    panel.resize(800, 600)
    panel.show()
    sys.exit(app.exec())
