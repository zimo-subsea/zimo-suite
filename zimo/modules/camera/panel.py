from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from zimo.core.api_client import ApiClient
from zimo.core.module_base import ModuleBase


class CameraPanel(ModuleBase):
    def __init__(self, api_client: ApiClient, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.api_client = api_client
        self.setObjectName("CameraPanel")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(32, 24, 32, 32)
        root_layout.setSpacing(24)

        header = self._build_header()
        root_layout.addWidget(header)

        cards = QGridLayout()
        cards.setHorizontalSpacing(24)
        cards.setVerticalSpacing(24)

        cards.addWidget(self._build_status_card(), 0, 0)
        cards.addWidget(self._build_controls_card(), 0, 1)
        cards.addWidget(self._build_health_card(), 1, 0)
        cards.addWidget(self._build_stream_card(), 1, 1)

        root_layout.addLayout(cards)
        root_layout.addStretch(1)

    @property
    def module_name(self) -> str:
        return "Camera"

    def _build_header(self) -> QWidget:
        header = QWidget()
        layout = QVBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel("Camera Module")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Subsea vision control, monitoring, and calibration")
        subtitle.setObjectName("PageSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        return header

    def _build_status_card(self) -> QFrame:
        card = self._build_card("Camera Status")
        status = self.api_client.get_camera_status()

        status_row = self._build_info_row("State", status.state)
        temp_row = self._build_info_row("Temperature", f"{status.temperature_c:.1f} °C")
        exposure_row = self._build_info_row("Exposure", f"{status.exposure_ms:.1f} ms")
        gain_row = self._build_info_row("Gain", f"{status.gain_db:.1f} dB")

        layout = card.layout()
        layout.addWidget(status_row)
        layout.addWidget(temp_row)
        layout.addWidget(exposure_row)
        layout.addWidget(gain_row)
        layout.addStretch(1)

        return card

    def _build_controls_card(self) -> QFrame:
        card = self._build_card("Exposure & Gain")
        layout = card.layout()

        layout.addWidget(self._build_slider("Exposure", 1, 20, 8))
        layout.addWidget(self._build_slider("Gain", 0, 12, 3))
        layout.addStretch(1)

        return card

    def _build_health_card(self) -> QFrame:
        card = self._build_card("Diagnostics")
        layout = card.layout()

        layout.addWidget(self._build_info_row("Packets", "124.3k"))
        layout.addWidget(self._build_info_row("Latency", "Ultra-low"))
        layout.addWidget(self._build_info_row("Low-light", "Optimized"))
        layout.addStretch(1)

        return card

    def _build_stream_card(self) -> QFrame:
        card = self._build_card("Stream")
        layout = card.layout()

        placeholder = QLabel("Live stream placeholder")
        placeholder.setObjectName("StreamPlaceholder")
        placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(placeholder, stretch=1)

        return card

    def _build_card(self, title: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel(title)
        header.setObjectName("CardTitle")
        layout.addWidget(header)

        return card

    def _build_info_row(self, label: str, value: str) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label_widget = QLabel(label)
        label_widget.setObjectName("InfoLabel")
        value_widget = QLabel(value)
        value_widget.setObjectName("InfoValue")

        layout.addWidget(label_widget)
        layout.addStretch(1)
        layout.addWidget(value_widget)

        return row

    def _build_slider(self, label: str, minimum: int, maximum: int, value: int) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label_row = QHBoxLayout()
        label_widget = QLabel(label)
        label_widget.setObjectName("InfoLabel")
        value_widget = QLabel(str(value))
        value_widget.setObjectName("SliderValue")
        label_row.addWidget(label_widget)
        label_row.addStretch(1)
        label_row.addWidget(value_widget)

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(minimum)
        slider.setMaximum(maximum)
        slider.setValue(value)
        slider.valueChanged.connect(lambda val: value_widget.setText(str(val)))

        layout.addLayout(label_row)
        layout.addWidget(slider)
        return wrapper
