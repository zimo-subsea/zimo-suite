from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from zimo.core.api_client import ApiClient
from zimo.modules.camera.panel import CameraPanel
from zimo.modules.vibration.panel import VibrationPanel


@dataclass(frozen=True)
class ModuleEntry:
    key: str
    label: str
    widget: QWidget


class ZimoShell(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ZiMO Control")
        self.resize(1200, 800)

        self.api_client = ApiClient()
        self.modules: List[ModuleEntry] = []
        self.module_lookup: Dict[str, QWidget] = {}

        container = QWidget()
        container.setObjectName("AppContainer")
        self.setCentralWidget(container)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        self.sidebar = self._build_sidebar()
        self.main_area = self._build_main_area()

        layout.addWidget(self.sidebar)
        layout.addWidget(self.main_area, 1)

        self._register_modules()

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(240)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(16)

        brand = QLabel("ZiMO")
        brand.setObjectName("SidebarBrand")

        subtitle = QLabel("Sensor Control")
        subtitle.setObjectName("SidebarSubtitle")

        self.module_list = QListWidget()
        self.module_list.setObjectName("ModuleList")
        self.module_list.setSpacing(4)
        self.module_list.currentRowChanged.connect(self._on_module_change)

        layout.addWidget(brand)
        layout.addWidget(subtitle)
        layout.addSpacing(12)
        layout.addWidget(self.module_list, 1)

        return sidebar

    def _build_main_area(self) -> QWidget:
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(16)

        topbar = QFrame()
        topbar.setObjectName("Topbar")
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(20, 12, 20, 12)
        topbar_layout.setSpacing(12)

        title = QLabel("Operations Dashboard")
        title.setObjectName("TopbarTitle")

        status = QLabel("API: mock://localhost")
        status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        status.setObjectName("TopbarStatus")

        topbar_layout.addWidget(title)
        topbar_layout.addStretch()
        topbar_layout.addWidget(status)

        self.stack = QStackedWidget()
        self.stack.setObjectName("ModuleStack")

        wrapper_layout.addWidget(topbar)
        wrapper_layout.addWidget(self.stack, 1)

        return wrapper

    def _register_modules(self) -> None:
        camera_panel = CameraPanel(self.api_client)
        vibration_panel = VibrationPanel(self.api_client)

        self._add_module("camera", "Camera", camera_panel)
        self._add_module("vibration", "Vibration", vibration_panel)

        if self.module_list.count() > 0:
            self.module_list.setCurrentRow(0)

    def _add_module(self, key: str, label: str, widget: QWidget) -> None:
        entry = ModuleEntry(key=key, label=label, widget=widget)
        self.modules.append(entry)
        self.module_lookup[key] = widget

        item = QListWidgetItem(label)
        item.setData(Qt.UserRole, key)
        self.module_list.addItem(item)
        self.stack.addWidget(widget)

    def _on_module_change(self, index: int) -> None:
        if index < 0:
            return
        self.stack.setCurrentIndex(index)
