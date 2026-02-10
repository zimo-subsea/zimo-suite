from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PySide6 import QtCore, QtGui, QtWidgets, QtSvgWidgets

from zimo.core.api_client import ApiClient
from zimo.core.module_base import ModuleBase
from zimo.modules.vpu.panel import VpuModule
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
        self.setWindowTitle("ZiMO Suite")
        self.resize(1280, 800)
        icon_path = Path(__file__).with_name("logo.png")
        self.setWindowIcon(QtGui.QIcon(str(icon_path)))

        self._api = ApiClient()
        self._modules: list[ModuleEntry] = []
        self._sidebar_modules_layout: QtWidgets.QVBoxLayout | None = None
        self._module_status = {
            "Vision Processing Unit": True,
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

        self._load_modules([VpuModule(), VibrationModule()])

    def _build_topbar(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QWidget()
        bar.setObjectName("TopBar")
        layout = QtWidgets.QHBoxLayout(bar)
        layout.setContentsMargins(24, 12, 24, 12)

        logo_path = Path(__file__).with_name("header_logo.svg")
        logo = QtSvgWidgets.QSvgWidget(str(logo_path))
        logo.setObjectName("Logo")
        logo.setFixedSize(80, 28)
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

        modules_container = QtWidgets.QWidget()
        modules_layout = QtWidgets.QVBoxLayout(modules_container)
        modules_layout.setContentsMargins(0, 0, 0, 0)
        modules_layout.setSpacing(8)
        self._sidebar_modules_layout = modules_layout
        layout.addWidget(modules_container)

        layout.addStretch()

        products_button = QtWidgets.QPushButton("Products")
        products_button.setObjectName("SidebarProductsButton")
        products_button.setCursor(QtCore.Qt.PointingHandCursor)
        products_button.clicked.connect(
            lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://www.zimo.no/products/"))
        )
        layout.addWidget(products_button)

        layout.addWidget(self._build_sidebar_status_legend())

        return sidebar

    def _load_modules(self, modules: Iterable[ModuleBase]) -> None:
        if self._sidebar_modules_layout is None:
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

            self._sidebar_modules_layout.addWidget(row)

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

    def _build_sidebar_status_legend(self) -> QtWidgets.QWidget:
        legend = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(legend)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title = QtWidgets.QLabel("Status legend")
        title.setObjectName("SidebarTitle")

        online_row = QtWidgets.QWidget()
        online_layout = QtWidgets.QHBoxLayout(online_row)
        online_layout.setContentsMargins(0, 0, 0, 0)
        online_layout.setSpacing(8)
        online_layout.addWidget(self._build_status_dot(True))
        online_label = QtWidgets.QLabel("Connected")
        online_label.setObjectName("CardMeta")
        online_layout.addWidget(online_label)

        offline_row = QtWidgets.QWidget()
        offline_layout = QtWidgets.QHBoxLayout(offline_row)
        offline_layout.setContentsMargins(0, 0, 0, 0)
        offline_layout.setSpacing(8)
        offline_layout.addWidget(self._build_status_dot(False))
        offline_label = QtWidgets.QLabel("Disconnected")
        offline_label.setObjectName("CardMeta")
        offline_layout.addWidget(offline_label)

        layout.addWidget(title)
        layout.addWidget(online_row)
        layout.addWidget(offline_row)
        return legend

    @staticmethod
    def _build_status_dot(is_online: bool) -> QtWidgets.QLabel:
        dot = QtWidgets.QLabel("●")
        dot.setObjectName("StatusDot")
        dot.setProperty("severity", "success" if is_online else "danger")
        return dot
