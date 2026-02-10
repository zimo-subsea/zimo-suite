from __future__ import annotations

import json
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from zimo.core.api_client import ApiClient
from zimo.core.module_base import ModuleBase


class VpuModule(ModuleBase):
    title = "Vision Processing Unit"

    def create_panel(self, api: ApiClient) -> QtWidgets.QWidget:
        return VpuPanel(api)


class VpuPanel(QtWidgets.QWidget):
    def __init__(self, api: ApiClient) -> None:
        super().__init__()
        self._api = api
        self._camera_names = [f"Camera {index}" for index in range(1, 9)]
        self._camera_connected = [True, True, False, True, False, True, True, False]
        self._camera_buttons: list[QtWidgets.QPushButton] = []
        self._camera_name_edits: list[QtWidgets.QLineEdit] = []
        self._current_camera_index = 0
        self._current_camera_label: QtWidgets.QLabel | None = None
        self._camera_pen_buttons: list[QtWidgets.QPushButton] = []
        self._settings_file = Path(__file__).with_name("vpu_settings.json")
        self._camera_settings: dict[str, dict[str, object]] = self._load_settings()
        self._fps_selector: QtWidgets.QComboBox | None = None
        self._resolution_selector: QtWidgets.QComboBox | None = None
        self._exposure_slider: QtWidgets.QSlider | None = None
        self._auto_exposure_toggle: QtWidgets.QCheckBox | None = None
        self._gain_slider: QtWidgets.QSlider | None = None
        self._auto_gain_toggle: QtWidgets.QCheckBox | None = None
        self._wb_slider: QtWidgets.QSlider | None = None
        self._auto_wb_toggle: QtWidgets.QCheckBox | None = None
        self._enable_toggle: QtWidgets.QCheckBox | None = None
        self._aruco_toggle: QtWidgets.QCheckBox | None = None
        self._aruco_dict: QtWidgets.QComboBox | None = None
        self._advanced_toggle: QtWidgets.QPushButton | None = None
        self._advanced_settings_panel: QtWidgets.QWidget | None = None
        self._sensor_roi_enable_toggle: QtWidgets.QCheckBox | None = None
        self._sensor_roi_x: QtWidgets.QSpinBox | None = None
        self._sensor_roi_y: QtWidgets.QSpinBox | None = None
        self._sensor_roi_width: QtWidgets.QSpinBox | None = None
        self._sensor_roi_height: QtWidgets.QSpinBox | None = None
        self._sensor_black_level_slider: QtWidgets.QSlider | None = None
        self._sensor_black_level_spinbox: QtWidgets.QSpinBox | None = None
        self._encoder_keyframe_interval: QtWidgets.QSpinBox | None = None
        self._ai_input_resolution: QtWidgets.QComboBox | None = None
        self._ai_processing_rate: QtWidgets.QSpinBox | None = None
        self._ai_overlay_toggle: QtWidgets.QCheckBox | None = None
        self._network_destination_ip: QtWidgets.QLineEdit | None = None
        self._network_base_port: QtWidgets.QSpinBox | None = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        header = QtWidgets.QLabel("Camera Overview")
        header.setObjectName("PageTitle")
        subtitle = QtWidgets.QLabel("Monitor the machine vision feed and adjust capture settings.")
        subtitle.setObjectName("PageSubtitle")

        layout.addWidget(header)
        layout.addWidget(subtitle)
        body_layout = QtWidgets.QHBoxLayout()
        body_layout.setSpacing(16)

        left_column = QtWidgets.QVBoxLayout()
        left_column.setSpacing(16)

        selection_card = self._build_selection_card()
        status_card = self._build_status_card()

        left_column.addWidget(selection_card, 1)
        left_column.addWidget(status_card, 1)
        left_column.addStretch()
        left_column.addWidget(self._build_status_legend())

        settings_card = self._build_settings_card()
        settings_scroll = QtWidgets.QScrollArea()
        settings_scroll.setObjectName("SettingsScrollArea")
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        settings_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        settings_scroll.setWidget(settings_card)

        body_layout.addLayout(left_column, 1)
        body_layout.addWidget(settings_scroll, 2)

        layout.addLayout(body_layout)

        layout.addStretch()

    def _build_selection_card(self) -> QtWidgets.QWidget:
        card = QtWidgets.QWidget()
        card.setObjectName("Card")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QtWidgets.QLabel("Camera Selection")
        title.setObjectName("CardTitle")
        hint = QtWidgets.QLabel("Select a camera to edit its settings.")
        hint.setObjectName("CardMeta")

        layout.addWidget(title)
        layout.addWidget(hint)

        button_group = QtWidgets.QButtonGroup(self)
        button_group.setExclusive(True)

        for index, name in enumerate(self._camera_names):
            row = QtWidgets.QWidget()
            row_layout = QtWidgets.QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            status_dot = self._build_status_dot(self._camera_connected[index])
            row_layout.addWidget(status_dot)

            button = QtWidgets.QPushButton(name)
            button.setCheckable(True)
            button.setCursor(QtCore.Qt.PointingHandCursor)
            button.clicked.connect(lambda checked, i=index: self._select_camera(i))
            if index == self._current_camera_index:
                button.setChecked(True)
            button_group.addButton(button)
            row_layout.addWidget(button, 1)

            edit = QtWidgets.QLineEdit(name)
            edit.setPlaceholderText("Camera name")
            edit.setVisible(False)
            edit.editingFinished.connect(lambda i=index: self._apply_camera_rename(i))
            row_layout.addWidget(edit, 1)

            pen = QtWidgets.QPushButton("✎")
            pen.setObjectName("SelectionPen")
            pen.setCursor(QtCore.Qt.PointingHandCursor)
            pen.setVisible(index == self._current_camera_index)
            pen.clicked.connect(lambda checked=False, i=index: self._enable_name_edit(i))
            row_layout.addWidget(pen)

            layout.addWidget(row)
            self._camera_buttons.append(button)
            self._camera_name_edits.append(edit)
            self._camera_pen_buttons.append(pen)
        layout.addStretch()
        return card

    def _build_status_card(self) -> QtWidgets.QWidget:
        card = QtWidgets.QWidget()
        card.setObjectName("Card")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QtWidgets.QLabel("Status")
        title.setObjectName("CardTitle")

        docs_button = QtWidgets.QPushButton("Open VPU documentation")
        docs_button.setCursor(QtCore.Qt.PointingHandCursor)
        docs_button.clicked.connect(
            lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://docs.zimo.no/products/vpu/"))
        )

        layout.addWidget(title)
        layout.addWidget(docs_button)
        layout.addStretch()
        return card

    def _build_settings_card(self) -> QtWidgets.QWidget:
        card = QtWidgets.QWidget()
        card.setObjectName("Card")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("Camera Settings")
        title.setObjectName("CardTitle")

        layout.addWidget(title)

        current_label = QtWidgets.QLabel(self._camera_names[self._current_camera_index])
        current_label.setObjectName("CardValue")
        self._current_camera_label = current_label
        header_row = QtWidgets.QHBoxLayout()
        header_row.addWidget(current_label)
        header_row.addStretch()
        enable_toggle = self._build_toggle("On", "Off")
        enable_toggle.toggled.connect(lambda checked: self._update_toggle_label(enable_toggle, "On", "Off"))
        self._update_toggle_label(enable_toggle, "On", "Off")
        self._enable_toggle = enable_toggle
        header_row.addWidget(enable_toggle)
        layout.addLayout(header_row)

        form = QtWidgets.QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        form.setColumnStretch(1, 1)

        row = 0

        fps_selector = QtWidgets.QComboBox()
        fps_selector.addItems(["24 FPS", "30 FPS", "60 FPS", "90 FPS", "120 FPS"])
        self._fps_selector = fps_selector
        form.addWidget(QtWidgets.QLabel("FPS"), row, 0)
        form.addWidget(fps_selector, row, 1)
        row += 1

        resolution_selector = QtWidgets.QComboBox()
        resolution_selector.addItems(["1280 × 720", "1920 × 1080", "2560 × 1440", "3840 × 2160 (4K)"])
        self._resolution_selector = resolution_selector
        form.addWidget(QtWidgets.QLabel("Resolution"), row, 0)
        form.addWidget(resolution_selector, row, 1)
        row += 1

        exposure_slider = self._build_slider()
        auto_exposure_toggle = self._build_toggle("Auto", "Manual")
        self._bind_auto_toggle(auto_exposure_toggle, exposure_slider)
        self._exposure_slider = exposure_slider
        self._auto_exposure_toggle = auto_exposure_toggle
        form.addWidget(QtWidgets.QLabel("Exposure"), row, 0)
        form.addWidget(exposure_slider, row, 1)
        form.addWidget(auto_exposure_toggle, row, 2)
        row += 1

        gain_slider = self._build_slider()
        auto_gain_toggle = self._build_toggle("Auto", "Manual")
        self._bind_auto_toggle(auto_gain_toggle, gain_slider)
        self._gain_slider = gain_slider
        self._auto_gain_toggle = auto_gain_toggle
        form.addWidget(QtWidgets.QLabel("Gain"), row, 0)
        form.addWidget(gain_slider, row, 1)
        form.addWidget(auto_gain_toggle, row, 2)
        row += 1

        wb_slider = self._build_slider()
        auto_wb_toggle = self._build_toggle("Auto", "Manual")
        self._bind_auto_toggle(auto_wb_toggle, wb_slider)
        self._wb_slider = wb_slider
        self._auto_wb_toggle = auto_wb_toggle
        form.addWidget(QtWidgets.QLabel("White balance"), row, 0)
        form.addWidget(wb_slider, row, 1)
        form.addWidget(auto_wb_toggle, row, 2)
        row += 1

        docs_button = QtWidgets.QPushButton("Open camera documentation")
        docs_button.setCursor(QtCore.Qt.PointingHandCursor)
        docs_button.clicked.connect(
            lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://docs.zimo.no/products/camera/"))
        )
        form.addWidget(QtWidgets.QLabel("Camera docs"), row, 0)
        form.addWidget(docs_button, row, 1)
        row += 1

        aruco_toggle = self._build_toggle("On", "Off")
        aruco_toggle.toggled.connect(lambda checked: self._update_toggle_label(aruco_toggle, "On", "Off"))
        self._update_toggle_label(aruco_toggle, "On", "Off")
        self._aruco_toggle = aruco_toggle
        form.addWidget(QtWidgets.QLabel("Enable ArUco"), row, 0)
        form.addWidget(aruco_toggle, row, 1)
        row += 1

        aruco_dict = QtWidgets.QComboBox()
        aruco_dict.addItems(
            [
                "DICT_4X4_50",
                "DICT_4X4_100",
                "DICT_5X5_50",
                "DICT_6X6_100",
                "DICT_7X7_250",
            ]
        )
        self._aruco_dict = aruco_dict
        form.addWidget(QtWidgets.QLabel("ArUco dictionary"), row, 0)
        form.addWidget(aruco_dict, row, 1)
        row += 1

        layout.addLayout(form)

        advanced_toggle = QtWidgets.QPushButton("Advanced settings ▸")
        advanced_toggle.setObjectName("AdvancedSettingsToggle")
        advanced_toggle.setCheckable(True)
        advanced_toggle.setCursor(QtCore.Qt.PointingHandCursor)
        self._advanced_toggle = advanced_toggle
        layout.addWidget(advanced_toggle)

        advanced_panel = QtWidgets.QWidget()
        advanced_panel.setVisible(False)
        advanced_form = QtWidgets.QGridLayout(advanced_panel)
        advanced_form.setContentsMargins(0, 0, 0, 0)
        advanced_form.setHorizontalSpacing(12)
        advanced_form.setVerticalSpacing(10)
        advanced_form.setColumnStretch(1, 1)

        advanced_row = 0

        sensor_header = QtWidgets.QLabel("Sensor")
        sensor_header.setObjectName("CardValue")
        advanced_form.addWidget(sensor_header, advanced_row, 0, 1, 3)
        advanced_row += 1

        roi_toggle = self._build_toggle("On", "Off")
        roi_toggle.toggled.connect(lambda checked: self._update_toggle_label(roi_toggle, "On", "Off"))
        self._update_toggle_label(roi_toggle, "On", "Off")
        self._sensor_roi_enable_toggle = roi_toggle
        advanced_form.addWidget(QtWidgets.QLabel("ROI-enable"), advanced_row, 0)
        advanced_form.addWidget(roi_toggle, advanced_row, 1)
        advanced_row += 1

        roi_row = QtWidgets.QHBoxLayout()
        roi_x = QtWidgets.QSpinBox()
        roi_x.setRange(0, 10000)
        roi_x.setPrefix("x: ")
        roi_y = QtWidgets.QSpinBox()
        roi_y.setRange(0, 10000)
        roi_y.setPrefix("y: ")
        roi_w = QtWidgets.QSpinBox()
        roi_w.setRange(1, 10000)
        roi_w.setPrefix("w: ")
        roi_h = QtWidgets.QSpinBox()
        roi_h.setRange(1, 10000)
        roi_h.setPrefix("h: ")
        self._sensor_roi_x = roi_x
        self._sensor_roi_y = roi_y
        self._sensor_roi_width = roi_w
        self._sensor_roi_height = roi_h
        roi_row.addWidget(roi_x)
        roi_row.addWidget(roi_y)
        roi_row.addWidget(roi_w)
        roi_row.addWidget(roi_h)
        roi_widget = QtWidgets.QWidget()
        roi_widget.setLayout(roi_row)
        advanced_form.addWidget(QtWidgets.QLabel("ROI-innstillinger"), advanced_row, 0)
        advanced_form.addWidget(roi_widget, advanced_row, 1, 1, 2)
        advanced_row += 1

        black_level_slider, black_level_spin = self._build_slider_with_spinbox()
        self._sensor_black_level_slider = black_level_slider
        self._sensor_black_level_spinbox = black_level_spin
        black_level_widget = QtWidgets.QWidget()
        black_level_layout = QtWidgets.QHBoxLayout(black_level_widget)
        black_level_layout.setContentsMargins(0, 0, 0, 0)
        black_level_layout.setSpacing(8)
        black_level_layout.addWidget(black_level_slider, 1)
        black_level_layout.addWidget(black_level_spin)
        advanced_form.addWidget(QtWidgets.QLabel("Black level"), advanced_row, 0)
        advanced_form.addWidget(black_level_widget, advanced_row, 1, 1, 2)
        advanced_row += 1

        encoder_header = QtWidgets.QLabel("Encoder")
        encoder_header.setObjectName("CardValue")
        advanced_form.addWidget(encoder_header, advanced_row, 0, 1, 3)
        advanced_row += 1

        keyframe_interval = QtWidgets.QSpinBox()
        keyframe_interval.setRange(1, 600)
        self._encoder_keyframe_interval = keyframe_interval
        advanced_form.addWidget(QtWidgets.QLabel("Keyframe interval"), advanced_row, 0)
        advanced_form.addWidget(keyframe_interval, advanced_row, 1)
        advanced_row += 1

        force_idr_button = QtWidgets.QPushButton("Force IDR")
        force_idr_button.setCursor(QtCore.Qt.PointingHandCursor)
        force_idr_button.clicked.connect(self._force_idr)
        advanced_form.addWidget(QtWidgets.QLabel("Force IDR"), advanced_row, 0)
        advanced_form.addWidget(force_idr_button, advanced_row, 1)
        advanced_row += 1

        ai_header = QtWidgets.QLabel("AI/CV")
        ai_header.setObjectName("CardValue")
        advanced_form.addWidget(ai_header, advanced_row, 0, 1, 3)
        advanced_row += 1

        ai_input_resolution = QtWidgets.QComboBox()
        ai_input_resolution.addItems(["640 × 360", "1280 × 720", "1920 × 1080"])
        self._ai_input_resolution = ai_input_resolution
        advanced_form.addWidget(QtWidgets.QLabel("AI input resolution"), advanced_row, 0)
        advanced_form.addWidget(ai_input_resolution, advanced_row, 1)
        advanced_row += 1

        ai_processing_rate = QtWidgets.QSpinBox()
        ai_processing_rate.setRange(1, 120)
        ai_processing_rate.setSuffix(" (hver N-te frame)")
        self._ai_processing_rate = ai_processing_rate
        advanced_form.addWidget(QtWidgets.QLabel("AI prosesseringsrate"), advanced_row, 0)
        advanced_form.addWidget(ai_processing_rate, advanced_row, 1)
        advanced_row += 1

        overlay_toggle = self._build_toggle("On", "Off")
        overlay_toggle.toggled.connect(lambda checked: self._update_toggle_label(overlay_toggle, "On", "Off"))
        self._update_toggle_label(overlay_toggle, "On", "Off")
        self._ai_overlay_toggle = overlay_toggle
        advanced_form.addWidget(QtWidgets.QLabel("Overlay"), advanced_row, 0)
        advanced_form.addWidget(overlay_toggle, advanced_row, 1)
        advanced_row += 1

        network_header = QtWidgets.QLabel("Nettverk")
        network_header.setObjectName("CardValue")
        advanced_form.addWidget(network_header, advanced_row, 0, 1, 3)
        advanced_row += 1

        destination_ip = QtWidgets.QLineEdit()
        destination_ip.setPlaceholderText("192.168.1.100")
        self._network_destination_ip = destination_ip
        advanced_form.addWidget(QtWidgets.QLabel("Destination IP"), advanced_row, 0)
        advanced_form.addWidget(destination_ip, advanced_row, 1)
        advanced_row += 1

        base_port = QtWidgets.QSpinBox()
        base_port.setRange(1, 65535)
        self._network_base_port = base_port
        advanced_form.addWidget(QtWidgets.QLabel("Base port"), advanced_row, 0)
        advanced_form.addWidget(base_port, advanced_row, 1)

        self._advanced_settings_panel = advanced_panel
        advanced_toggle.toggled.connect(self._set_advanced_settings_expanded)
        layout.addWidget(advanced_panel)

        presets_row = QtWidgets.QHBoxLayout()
        apply_button = QtWidgets.QPushButton("Apply")
        apply_button.setCursor(QtCore.Qt.PointingHandCursor)
        apply_button.clicked.connect(self._apply_settings)
        save_button = QtWidgets.QPushButton("Save setup")
        save_button.setCursor(QtCore.Qt.PointingHandCursor)
        save_button.clicked.connect(self._save_preset)
        load_button = QtWidgets.QPushButton("Load preset")
        load_button.setCursor(QtCore.Qt.PointingHandCursor)
        load_button.clicked.connect(self._load_preset)
        presets_row.addWidget(apply_button)
        presets_row.addWidget(save_button)
        presets_row.addWidget(load_button)
        presets_row.addStretch()
        layout.addLayout(presets_row)
        layout.addStretch()

        self._apply_loaded_settings()

        return card

    @staticmethod
    def _build_slider() -> QtWidgets.QSlider:
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(40)
        return slider

    @staticmethod
    def _build_toggle(label_on: str, label_off: str) -> QtWidgets.QCheckBox:
        toggle = QtWidgets.QCheckBox(label_on)
        toggle.setObjectName("ToggleSwitch")
        toggle.setCursor(QtCore.Qt.PointingHandCursor)
        toggle.setChecked(True)
        toggle.setProperty("label_on", label_on)
        toggle.setProperty("label_off", label_off)
        return toggle

    @staticmethod
    def _build_slider_with_spinbox() -> tuple[QtWidgets.QSlider, QtWidgets.QSpinBox]:
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(0, 255)
        slider.setValue(16)
        spinbox = QtWidgets.QSpinBox()
        spinbox.setRange(0, 255)
        spinbox.setValue(16)
        slider.valueChanged.connect(spinbox.setValue)
        spinbox.valueChanged.connect(slider.setValue)
        return slider, spinbox

    @staticmethod
    def _update_toggle_label(toggle: QtWidgets.QCheckBox, label_on: str, label_off: str) -> None:
        toggle.setText(label_on if toggle.isChecked() else label_off)

    def _bind_auto_toggle(self, toggle: QtWidgets.QCheckBox, slider: QtWidgets.QSlider) -> None:
        def _sync_state(checked: bool) -> None:
            toggle.setText("Auto" if checked else "Manual")
            slider.setEnabled(not checked)

        toggle.setChecked(True)
        _sync_state(toggle.isChecked())
        toggle.toggled.connect(_sync_state)

    def _set_advanced_settings_expanded(self, expanded: bool) -> None:
        if self._advanced_settings_panel is not None:
            self._advanced_settings_panel.setVisible(expanded)
        if self._advanced_toggle is not None:
            self._advanced_toggle.setText("Advanced settings ▾" if expanded else "Advanced settings ▸")

    def _force_idr(self) -> None:
        QtWidgets.QMessageBox.information(self, "Force IDR", "IDR frame triggered.")

    @staticmethod
    def _build_status_dot(is_online: bool) -> QtWidgets.QLabel:
        dot = QtWidgets.QLabel("●")
        dot.setObjectName("StatusDot")
        dot.setProperty("severity", "success" if is_online else "danger")
        return dot

    def _build_status_legend(self) -> QtWidgets.QWidget:
        legend = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(legend)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title = QtWidgets.QLabel("Status legend:")
        title.setObjectName("CardMeta")

        online_row = QtWidgets.QWidget()
        online_layout = QtWidgets.QHBoxLayout(online_row)
        online_layout.setContentsMargins(0, 0, 0, 0)
        online_layout.setSpacing(8)
        online_dot = self._build_status_dot(True)
        online_label = QtWidgets.QLabel("Connected")
        online_label.setObjectName("CardMeta")
        online_layout.addWidget(online_dot)
        online_layout.addWidget(online_label)

        offline_row = QtWidgets.QWidget()
        offline_layout = QtWidgets.QHBoxLayout(offline_row)
        offline_layout.setContentsMargins(0, 0, 0, 0)
        offline_layout.setSpacing(8)
        offline_dot = self._build_status_dot(False)
        offline_label = QtWidgets.QLabel("Disconnected")
        offline_label.setObjectName("CardMeta")
        offline_layout.addWidget(offline_dot)
        offline_layout.addWidget(offline_label)

        layout.addWidget(title)
        layout.addWidget(online_row)
        layout.addWidget(offline_row)
        return legend

    def _select_camera(self, index: int) -> None:
        self._current_camera_index = index
        if self._current_camera_label is not None:
            self._current_camera_label.setText(self._camera_names[index])
        for button_index, button in enumerate(self._camera_buttons):
            button.setChecked(button_index == index)
        for pen_index, pen in enumerate(self._camera_pen_buttons):
            pen.setVisible(pen_index == index)
        for edit_index, edit in enumerate(self._camera_name_edits):
            edit.setText(self._camera_names[edit_index])
            edit.setVisible(False)
            self._camera_buttons[edit_index].setVisible(True)
        self._apply_loaded_settings()

    def _enable_name_edit(self, index: int) -> None:
        edit = self._camera_name_edits[index]
        edit.setVisible(True)
        self._camera_buttons[index].setVisible(False)
        edit.setFocus()
        edit.selectAll()

    def _apply_camera_rename(self, index: int) -> None:
        edit = self._camera_name_edits[index]
        new_name = edit.text().strip()
        if not new_name:
            edit.setText(self._camera_names[index])
            new_name = self._camera_names[index]
        self._camera_names[index] = new_name
        self._camera_buttons[index].setText(new_name)
        edit.setText(new_name)
        edit.setVisible(False)
        self._camera_buttons[index].setVisible(True)
        if self._current_camera_label is not None and index == self._current_camera_index:
            self._current_camera_label.setText(new_name)

    def _load_settings(self) -> dict[str, dict[str, object]]:
        if not self._settings_file.exists():
            return {}
        try:
            return json.loads(self._settings_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    @staticmethod
    def _default_settings() -> dict[str, object]:
        return {
            "enabled": True,
            "fps": "30 FPS",
            "resolution": "1920 × 1080",
            "exposure": {"value": 40, "auto": True},
            "gain": {"value": 40, "auto": True},
            "white_balance": {"value": 40, "auto": True},
            "aruco": {"enabled": True, "dictionary": "DICT_4X4_50"},
            "advanced": {
                "sensor": {
                    "roi_enabled": False,
                    "roi": {"x": 0, "y": 0, "width": 1920, "height": 1080},
                    "black_level": 16,
                },
                "encoder": {"keyframe_interval": 30},
                "ai_cv": {
                    "input_resolution": "1280 × 720",
                    "processing_rate": 1,
                    "overlay": True,
                },
                "network": {"destination_ip": "192.168.1.100", "base_port": 5000},
            },
        }

    def _camera_key(self, index: int | None = None) -> str:
        if index is None:
            index = self._current_camera_index
        return f"camera_{index + 1}"

    def _apply_settings(self) -> None:
        settings = self._collect_settings(include_name=True)
        self._camera_settings[self._camera_key()] = settings
        self._settings_file.write_text(
            json.dumps(self._camera_settings, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _apply_loaded_settings(self) -> None:
        settings = self._camera_settings.get(self._camera_key(), {})
        if not settings:
            settings = self._default_settings()
        if not settings:
            return
        name = settings.get("name")
        if isinstance(name, str) and name:
            self._camera_names[self._current_camera_index] = name
            if self._current_camera_label is not None:
                self._current_camera_label.setText(name)
            button = self._camera_buttons[self._current_camera_index]
            button.setText(name)
            edit = self._camera_name_edits[self._current_camera_index]
            edit.setText(name)
        if self._fps_selector is not None:
            self._fps_selector.setCurrentText(settings.get("fps", self._fps_selector.currentText()))
        if self._resolution_selector is not None:
            self._resolution_selector.setCurrentText(
                settings.get("resolution", self._resolution_selector.currentText())
            )
        if self._enable_toggle is not None:
            self._enable_toggle.setChecked(bool(settings.get("enabled", True)))
            self._update_toggle_label(self._enable_toggle, "On", "Off")
        exposure = settings.get("exposure", {})
        if self._exposure_slider is not None:
            self._exposure_slider.setValue(int(exposure.get("value", self._exposure_slider.value())))
        if self._auto_exposure_toggle is not None:
            self._auto_exposure_toggle.setChecked(bool(exposure.get("auto", True)))
        gain = settings.get("gain", {})
        if self._gain_slider is not None:
            self._gain_slider.setValue(int(gain.get("value", self._gain_slider.value())))
        if self._auto_gain_toggle is not None:
            self._auto_gain_toggle.setChecked(bool(gain.get("auto", True)))
        white_balance = settings.get("white_balance", {})
        if self._wb_slider is not None:
            self._wb_slider.setValue(int(white_balance.get("value", self._wb_slider.value())))
        if self._auto_wb_toggle is not None:
            self._auto_wb_toggle.setChecked(bool(white_balance.get("auto", True)))
        aruco = settings.get("aruco", {})
        if self._aruco_toggle is not None:
            self._aruco_toggle.setChecked(bool(aruco.get("enabled", True)))
            self._update_toggle_label(self._aruco_toggle, "On", "Off")
        if self._aruco_dict is not None:
            self._aruco_dict.setCurrentText(aruco.get("dictionary", self._aruco_dict.currentText()))

        advanced = settings.get("advanced", {})
        sensor = advanced.get("sensor", {}) if isinstance(advanced, dict) else {}
        roi = sensor.get("roi", {}) if isinstance(sensor, dict) else {}
        if self._sensor_roi_enable_toggle is not None:
            self._sensor_roi_enable_toggle.setChecked(bool(sensor.get("roi_enabled", False)))
            self._update_toggle_label(self._sensor_roi_enable_toggle, "On", "Off")
        if self._sensor_roi_x is not None:
            self._sensor_roi_x.setValue(int(roi.get("x", self._sensor_roi_x.value())))
        if self._sensor_roi_y is not None:
            self._sensor_roi_y.setValue(int(roi.get("y", self._sensor_roi_y.value())))
        if self._sensor_roi_width is not None:
            self._sensor_roi_width.setValue(int(roi.get("width", self._sensor_roi_width.value())))
        if self._sensor_roi_height is not None:
            self._sensor_roi_height.setValue(int(roi.get("height", self._sensor_roi_height.value())))
        if self._sensor_black_level_slider is not None:
            self._sensor_black_level_slider.setValue(int(sensor.get("black_level", self._sensor_black_level_slider.value())))

        encoder = advanced.get("encoder", {}) if isinstance(advanced, dict) else {}
        if self._encoder_keyframe_interval is not None:
            self._encoder_keyframe_interval.setValue(
                int(encoder.get("keyframe_interval", self._encoder_keyframe_interval.value()))
            )

        ai_cv = advanced.get("ai_cv", {}) if isinstance(advanced, dict) else {}
        if self._ai_input_resolution is not None:
            self._ai_input_resolution.setCurrentText(
                str(ai_cv.get("input_resolution", self._ai_input_resolution.currentText()))
            )
        if self._ai_processing_rate is not None:
            self._ai_processing_rate.setValue(int(ai_cv.get("processing_rate", self._ai_processing_rate.value())))
        if self._ai_overlay_toggle is not None:
            self._ai_overlay_toggle.setChecked(bool(ai_cv.get("overlay", True)))
            self._update_toggle_label(self._ai_overlay_toggle, "On", "Off")

        network = advanced.get("network", {}) if isinstance(advanced, dict) else {}
        if self._network_destination_ip is not None:
            self._network_destination_ip.setText(str(network.get("destination_ip", self._network_destination_ip.text())))
        if self._network_base_port is not None:
            self._network_base_port.setValue(int(network.get("base_port", self._network_base_port.value())))

    def _collect_settings(self, include_name: bool = True) -> dict[str, object]:
        base = {
            "enabled": bool(self._enable_toggle and self._enable_toggle.isChecked()),
            "fps": self._fps_selector.currentText() if self._fps_selector else "30 FPS",
            "resolution": self._resolution_selector.currentText() if self._resolution_selector else "1920 × 1080",
            "exposure": {
                "value": self._exposure_slider.value() if self._exposure_slider else 0,
                "auto": bool(self._auto_exposure_toggle and self._auto_exposure_toggle.isChecked()),
            },
            "gain": {
                "value": self._gain_slider.value() if self._gain_slider else 0,
                "auto": bool(self._auto_gain_toggle and self._auto_gain_toggle.isChecked()),
            },
            "white_balance": {
                "value": self._wb_slider.value() if self._wb_slider else 0,
                "auto": bool(self._auto_wb_toggle and self._auto_wb_toggle.isChecked()),
            },
            "aruco": {
                "enabled": bool(self._aruco_toggle and self._aruco_toggle.isChecked()),
                "dictionary": self._aruco_dict.currentText() if self._aruco_dict else "",
            },
            "advanced": {
                "sensor": {
                    "roi_enabled": bool(self._sensor_roi_enable_toggle and self._sensor_roi_enable_toggle.isChecked()),
                    "roi": {
                        "x": self._sensor_roi_x.value() if self._sensor_roi_x else 0,
                        "y": self._sensor_roi_y.value() if self._sensor_roi_y else 0,
                        "width": self._sensor_roi_width.value() if self._sensor_roi_width else 1920,
                        "height": self._sensor_roi_height.value() if self._sensor_roi_height else 1080,
                    },
                    "black_level": self._sensor_black_level_slider.value() if self._sensor_black_level_slider else 16,
                },
                "encoder": {
                    "keyframe_interval": self._encoder_keyframe_interval.value() if self._encoder_keyframe_interval else 30,
                },
                "ai_cv": {
                    "input_resolution": self._ai_input_resolution.currentText() if self._ai_input_resolution else "1280 × 720",
                    "processing_rate": self._ai_processing_rate.value() if self._ai_processing_rate else 1,
                    "overlay": bool(self._ai_overlay_toggle and self._ai_overlay_toggle.isChecked()),
                },
                "network": {
                    "destination_ip": self._network_destination_ip.text() if self._network_destination_ip else "",
                    "base_port": self._network_base_port.value() if self._network_base_port else 5000,
                },
            },
        }
        if include_name:
            base["name"] = self._camera_names[self._current_camera_index]
        return base

    def _apply_settings_snapshot(self, settings: dict[str, object]) -> None:
        if self._enable_toggle is not None:
            self._enable_toggle.setChecked(bool(settings.get("enabled", True)))
            self._update_toggle_label(self._enable_toggle, "On", "Off")
        if self._fps_selector is not None:
            self._fps_selector.setCurrentText(str(settings.get("fps", "30 FPS")))
        if self._resolution_selector is not None:
            self._resolution_selector.setCurrentText(str(settings.get("resolution", "1920 × 1080")))
        exposure = settings.get("exposure", {})
        if self._exposure_slider is not None:
            self._exposure_slider.setValue(int(exposure.get("value", self._exposure_slider.value())))
        if self._auto_exposure_toggle is not None:
            self._auto_exposure_toggle.setChecked(bool(exposure.get("auto", True)))
        gain = settings.get("gain", {})
        if self._gain_slider is not None:
            self._gain_slider.setValue(int(gain.get("value", self._gain_slider.value())))
        if self._auto_gain_toggle is not None:
            self._auto_gain_toggle.setChecked(bool(gain.get("auto", True)))
        white_balance = settings.get("white_balance", {})
        if self._wb_slider is not None:
            self._wb_slider.setValue(int(white_balance.get("value", self._wb_slider.value())))
        if self._auto_wb_toggle is not None:
            self._auto_wb_toggle.setChecked(bool(white_balance.get("auto", True)))
        aruco = settings.get("aruco", {})
        if self._aruco_toggle is not None:
            self._aruco_toggle.setChecked(bool(aruco.get("enabled", True)))
            self._update_toggle_label(self._aruco_toggle, "On", "Off")
        if self._aruco_dict is not None:
            self._aruco_dict.setCurrentText(str(aruco.get("dictionary", "DICT_4X4_50")))

        advanced = settings.get("advanced", {})
        sensor = advanced.get("sensor", {}) if isinstance(advanced, dict) else {}
        roi = sensor.get("roi", {}) if isinstance(sensor, dict) else {}
        if self._sensor_roi_enable_toggle is not None:
            self._sensor_roi_enable_toggle.setChecked(bool(sensor.get("roi_enabled", False)))
            self._update_toggle_label(self._sensor_roi_enable_toggle, "On", "Off")
        if self._sensor_roi_x is not None:
            self._sensor_roi_x.setValue(int(roi.get("x", 0)))
        if self._sensor_roi_y is not None:
            self._sensor_roi_y.setValue(int(roi.get("y", 0)))
        if self._sensor_roi_width is not None:
            self._sensor_roi_width.setValue(int(roi.get("width", 1920)))
        if self._sensor_roi_height is not None:
            self._sensor_roi_height.setValue(int(roi.get("height", 1080)))
        if self._sensor_black_level_slider is not None:
            self._sensor_black_level_slider.setValue(int(sensor.get("black_level", 16)))

        encoder = advanced.get("encoder", {}) if isinstance(advanced, dict) else {}
        if self._encoder_keyframe_interval is not None:
            self._encoder_keyframe_interval.setValue(int(encoder.get("keyframe_interval", 30)))

        ai_cv = advanced.get("ai_cv", {}) if isinstance(advanced, dict) else {}
        if self._ai_input_resolution is not None:
            self._ai_input_resolution.setCurrentText(str(ai_cv.get("input_resolution", "1280 × 720")))
        if self._ai_processing_rate is not None:
            self._ai_processing_rate.setValue(int(ai_cv.get("processing_rate", 1)))
        if self._ai_overlay_toggle is not None:
            self._ai_overlay_toggle.setChecked(bool(ai_cv.get("overlay", True)))
            self._update_toggle_label(self._ai_overlay_toggle, "On", "Off")

        network = advanced.get("network", {}) if isinstance(advanced, dict) else {}
        if self._network_destination_ip is not None:
            self._network_destination_ip.setText(str(network.get("destination_ip", "192.168.1.100")))
        if self._network_base_port is not None:
            self._network_base_port.setValue(int(network.get("base_port", 5000)))

    def _presets_dir(self) -> Path:
        return Path(__file__).with_name("presets")

    def _save_preset(self) -> None:
        preset_name, ok = QtWidgets.QInputDialog.getText(
            self,
            "Save preset",
            "Preset name:",
        )
        if not ok or not preset_name.strip():
            return
        safe_name = preset_name.strip().replace("/", "-")
        preset_path = self._presets_dir() / f"{safe_name}.json"
        preset_path.parent.mkdir(parents=True, exist_ok=True)
        preset_settings = self._collect_settings(include_name=False)
        preset_path.write_text(
            json.dumps(preset_settings, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load_preset(self) -> None:
        presets_dir = self._presets_dir()
        if not presets_dir.exists():
            QtWidgets.QMessageBox.information(self, "Load preset", "No presets found.")
            return
        preset_files = sorted(presets_dir.glob("*.json"))
        if not preset_files:
            QtWidgets.QMessageBox.information(self, "Load preset", "No presets found.")
            return
        preset_names = [path.stem for path in preset_files]
        selection, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Load preset",
            "Choose preset:",
            preset_names,
            0,
            False,
        )
        if not ok or not selection:
            return
        preset_path = presets_dir / f"{selection}.json"
        try:
            preset_settings = json.loads(preset_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            QtWidgets.QMessageBox.warning(self, "Load preset", "Preset could not be loaded.")
            return
        self._apply_settings_snapshot(preset_settings)
        self._persist_current_settings()

    def _persist_current_settings(self) -> None:
        settings = self._collect_settings(include_name=True)
        self._camera_settings[self._camera_key()] = settings
        self._settings_file.write_text(
            json.dumps(self._camera_settings, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    panel = VpuPanel(ApiClient())
    panel.resize(800, 600)
    panel.show()
    sys.exit(app.exec())
