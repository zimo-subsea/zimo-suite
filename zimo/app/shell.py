from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from PySide6 import QtCore, QtWidgets

from zimo.core.api_client import ApiClient
from zimo.core.module_base import ModuleBase
from zimo.modules.camera.panel import CameraModule
from zimo.modules.vibration.panel import VibrationModule


@dataclass(frozen=True)
class ModuleEntry:
    module: ModuleBase
    button: QtWidgets.QPushButton
    widget: QtWidgets.QWidget
    status_dot: QtWidgets.QLabel


class ZiMOShell(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ZiMO Control")
        self.resize(1280, 800)

        self._api = ApiClient()
        self._modules: list[ModuleEntry] = []
        self._module_status = {
            "Camera": True,
            "Vibration": False,
        }

        root = QtWidgets.QWidget()
        root_layout = QtWidgets.QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._topbar = self._build_topbar()
        root_layout.addWidget(self._topbar)

        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._sidebar = self._build_sidebar()
        content_layout.addWidget(self._sidebar)

        self._stack = QtWidgets.QStackedWidget()
        content_layout.addWidget(self._stack, 1)

        root_layout.addWidget(content, 1)

        self.setCentralWidget(root)

        self._load_modules([CameraModule(), VibrationModule()])

    def _build_topbar(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QWidget()
        bar.setObjectName("TopBar")
        layout = QtWidgets.QHBoxLayout(bar)
        layout.setContentsMargins(24, 12, 24, 12)

        logo = QtWidgets.QLabel("ZiMO")
        logo.setObjectName("Logo")
        status = QtWidgets.QLabel("Online · 3 devices")
        status.setObjectName("Status")
        status.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        layout.addWidget(logo)
        layout.addStretch()
        layout.addWidget(status)
        return bar

    def _build_sidebar(self) -> QtWidgets.QWidget:
        sidebar = QtWidgets.QWidget()
        sidebar.setObjectName("Sidebar")
        layout = QtWidgets.QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(12)

        title = QtWidgets.QLabel("Modules")
        title.setObjectName("SidebarTitle")
        layout.addWidget(title)

        layout.addStretch()
        return sidebar

    def _load_modules(self, modules: Iterable[ModuleBase]) -> None:
        sidebar_layout = self._sidebar.layout()
        if not isinstance(sidebar_layout, QtWidgets.QVBoxLayout):
            return

        for module in modules:
            panel = module.create_panel(self._api)
            self._stack.addWidget(panel)

            row = QtWidgets.QWidget()
            row_layout = QtWidgets.QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            status_dot = self._build_status_dot(self._module_status.get(module.title, False))
            row_layout.addWidget(status_dot)

            button = QtWidgets.QPushButton(module.title)
            button.setCheckable(True)
            button.setCursor(QtCore.Qt.PointingHandCursor)
            button.clicked.connect(lambda checked, m=module: self._select_module(m))
            row_layout.addWidget(button, 1)

            sidebar_layout.insertWidget(sidebar_layout.count() - 2, row)

            self._modules.append(
                ModuleEntry(module=module, button=button, widget=panel, status_dot=status_dot)
            )

        if self._modules:
            self._select_module(self._modules[0].module)

    def _select_module(self, module: ModuleBase) -> None:
        for entry in self._modules:
            is_active = entry.module is module
            entry.button.setChecked(is_active)
            if is_active:
                self._stack.setCurrentWidget(entry.widget)

    @staticmethod
    def _build_status_dot(is_online: bool) -> QtWidgets.QLabel:
        dot = QtWidgets.QLabel("●")
        dot.setObjectName("StatusDot")
        dot.setProperty("severity", "success" if is_online else "danger")
        return dot
