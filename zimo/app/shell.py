from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from zimo.core.api_client import ApiClient
from zimo.modules.camera.panel import CameraPanel


@dataclass(frozen=True)
class ModuleDescriptor:
    name: str
    widget: QWidget


class ZiMOShell(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ZiMO Control Suite")
        self.setMinimumSize(1200, 720)

        self.api_client = ApiClient()

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.sidebar.setFixedWidth(240)

        self.stack = QStackedWidget()
        self.stack.setObjectName("MainStack")

        self.status_label = QLabel("Status: Connecting…")
        self.status_label.setObjectName("StatusLabel")

        self.modules: list[ModuleDescriptor] = []
        self._register_modules()
        self._build_layout()
        self._connect_signals()
        self._update_status()

    def _register_modules(self) -> None:
        camera_panel = CameraPanel(self.api_client)
        self._add_module("Camera", camera_panel)

    def _add_module(self, name: str, widget: QWidget) -> None:
        self.modules.append(ModuleDescriptor(name=name, widget=widget))
        item = QListWidgetItem(name)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.sidebar.addItem(item)
        self.stack.addWidget(widget)

    def _build_layout(self) -> None:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.sidebar)

        main_column = QVBoxLayout()
        main_column.setContentsMargins(0, 0, 0, 0)
        main_column.setSpacing(0)

        topbar = self._build_topbar()
        main_column.addWidget(topbar)
        main_column.addWidget(self.stack, stretch=1)

        main_frame = QFrame()
        main_frame.setObjectName("MainFrame")
        main_frame.setLayout(main_column)

        layout.addWidget(main_frame, stretch=1)
        self.setCentralWidget(container)

        if self.modules:
            self.sidebar.setCurrentRow(0)
            self.stack.setCurrentIndex(0)

    def _build_topbar(self) -> QWidget:
        topbar = QFrame()
        topbar.setObjectName("Topbar")
        topbar.setFixedHeight(64)

        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)

        logo = QLabel("ZiMO")
        logo.setObjectName("Logo")

        module_hint = QLabel("Sensor Control Dashboard")
        module_hint.setObjectName("TopbarSubtitle")

        layout.addWidget(logo)
        layout.addWidget(module_hint)
        layout.addStretch(1)
        layout.addWidget(self.status_label)

        return topbar

    def _connect_signals(self) -> None:
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)

    def _update_status(self) -> None:
        status = self.api_client.get_system_status()
        self.status_label.setText(f"Status: {status.state}")
