from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from zimo.core.api_client import ApiClient
from zimo.core.module_base import BaseModule


class CameraPanel(BaseModule):
    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.api_client = api_client

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        header = QLabel("Camera Module")
        header.setObjectName("ModuleHeader")

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        status_card = self._build_status_card()
        stream_card = self._build_stream_card()
        controls_card = self._build_controls_card()

        grid.addWidget(status_card, 0, 0)
        grid.addWidget(stream_card, 0, 1)
        grid.addWidget(controls_card, 1, 0, 1, 2)

        layout.addWidget(header)
        layout.addLayout(grid)
        layout.addStretch()

    def panel_name(self) -> str:
        return "Camera"

    def _build_status_card(self) -> QFrame:
        status = self.api_client.fetch_camera_status()

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)

        title = QLabel("Status")
        title.setObjectName("CardTitle")

        online = QLabel("Online" if status.online else "Offline")
        online.setObjectName("StatusOnline" if status.online else "StatusOffline")

        metrics = QVBoxLayout()
        metrics.setSpacing(6)
        metrics.addWidget(self._metric_row("Temperature", f"{status.temperature_c:.1f} °C"))
        metrics.addWidget(self._metric_row("Bitrate", f"{status.bitrate_mbps:.1f} Mbps"))
        metrics.addWidget(self._metric_row("Last seen", self._format_timestamp(status.last_seen)))

        card_layout.addWidget(title)
        card_layout.addWidget(online)
        card_layout.addLayout(metrics)
        card_layout.addStretch()

        return card

    def _build_stream_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Stream")
        title.setObjectName("CardTitle")

        placeholder = QFrame()
        placeholder.setObjectName("MediaPlaceholder")
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_layout.setContentsMargins(12, 12, 12, 12)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(QLabel("Video feed placeholder"))

        layout.addWidget(title)
        layout.addWidget(placeholder, 1)

        return card

    def _build_controls_card(self) -> QFrame:
        settings = self.api_client.fetch_camera_settings()

        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Controls")
        title.setObjectName("CardTitle")

        sliders = QHBoxLayout()
        sliders.setSpacing(16)
        sliders.addWidget(self._slider_block("Exposure", settings["exposure"]))
        sliders.addWidget(self._slider_block("Gain", settings["gain"]))
        sliders.addWidget(self._slider_block("Gamma", settings["gamma"]))

        layout.addWidget(title)
        layout.addLayout(sliders)

        return card

    def _metric_row(self, label: str, value: str) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label_widget = QLabel(label)
        label_widget.setObjectName("MetricLabel")
        value_widget = QLabel(value)
        value_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        value_widget.setObjectName("MetricValue")

        layout.addWidget(label_widget)
        layout.addStretch()
        layout.addWidget(value_widget)

        return row

    def _slider_block(self, label: str, value: int) -> QWidget:
        block = QFrame()
        block.setObjectName("SliderBlock")
        layout = QVBoxLayout(block)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel(label)
        title.setObjectName("SliderLabel")

        slider = QSlider(Qt.Horizontal)
        slider.setValue(value)
        slider.setObjectName("ControlSlider")

        meter = QProgressBar()
        meter.setRange(0, 100)
        meter.setValue(value)
        meter.setTextVisible(False)
        meter.setObjectName("ControlMeter")

        layout.addWidget(title)
        layout.addWidget(slider)
        layout.addWidget(meter)

        return block

    @staticmethod
    def _format_timestamp(value: datetime) -> str:
        return value.strftime("%H:%M:%S UTC")
