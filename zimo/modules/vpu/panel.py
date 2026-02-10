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
        self._auto_wb_toggle: QtWidgets.QCheckBox | None = None
        self._wb_preset_selector: QtWidgets.QComboBox | None = None
        self._bitrate_selector: QtWidgets.QComboBox | None = None
        self._mode_selector: QtWidgets.QComboBox | None = None
        self._enable_toggle: QtWidgets.QCheckBox | None = None
        self._aruco_toggle: QtWidgets.QCheckBox | None = None
        self._aruco_dict: QtWidgets.QComboBox | None = None
        self._advanced_toggle: QtWidgets.QCheckBox | None = None
        self._advanced_section: QtWidgets.QWidget | None = None
        self._roi_toggle: QtWidgets.QCheckBox | None = None
        self._roi_x: QtWidgets.QSpinBox | None = None
        self._roi_y: QtWidgets.QSpinBox | None = None
        self._roi_width: QtWidgets.QSpinBox | None = None
        self._roi_height: QtWidgets.QSpinBox | None = None
        self._black_level: QtWidgets.QSlider | None = None
        self._keyframe_interval: QtWidgets.QSpinBox | None = None
        self._ai_input_resolution: QtWidgets.QComboBox | None = None
        self._ai_rate: QtWidgets.QSpinBox | None = None
        self._overlay_toggle: QtWidgets.QCheckBox | None = None

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

        body_layout.addLayout(left_column, 1)
        body_layout.addWidget(settings_card, 2)

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
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(0)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        content = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)
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

        mode_selector = QtWidgets.QComboBox()
        mode_selector.addItems(["Opptak", "Visning"])
        self._mode_selector = mode_selector
        form.addWidget(QtWidgets.QLabel("Mode"), row, 0)
        form.addWidget(mode_selector, row, 1)
        row += 1

        fps_selector = QtWidgets.QComboBox()
        fps_selector.addItems(["30 FPS", "60 FPS", "120 FPS"])
        self._fps_selector = fps_selector
        form.addWidget(QtWidgets.QLabel("FPS"), row, 0)
        form.addWidget(fps_selector, row, 1)
        row += 1

        resolution_selector = QtWidgets.QComboBox()
        resolution_selector.addItems(["3840 × 2160 (4K)", "1920 × 1080 (HD)", "1280 × 720"])
        self._resolution_selector = resolution_selector
        form.addWidget(QtWidgets.QLabel("Resolution"), row, 0)
        form.addWidget(resolution_selector, row, 1)
        row += 1

        exposure_slider = self._build_slider()
        auto_exposure_toggle = self._build_auto_checkbox()
        self._bind_auto_toggle(auto_exposure_toggle, exposure_slider)
        self._exposure_slider = exposure_slider
        self._auto_exposure_toggle = auto_exposure_toggle
        form.addWidget(QtWidgets.QLabel("Exposure"), row, 0)
        form.addWidget(exposure_slider, row, 1)
        form.addWidget(auto_exposure_toggle, row, 2)
        row += 1

        gain_slider = self._build_slider()
        auto_gain_toggle = self._build_auto_checkbox()
        self._bind_auto_toggle(auto_gain_toggle, gain_slider)
        self._gain_slider = gain_slider
        self._auto_gain_toggle = auto_gain_toggle
        form.addWidget(QtWidgets.QLabel("Gain"), row, 0)
        form.addWidget(gain_slider, row, 1)
        form.addWidget(auto_gain_toggle, row, 2)
        row += 1

        wb_preset_selector = QtWidgets.QComboBox()
        wb_preset_selector.addItems(["Daylight", "Cloudy", "Tungsten", "Fluorescent", "Warm LED", "Cool LED"])
        auto_wb_toggle = self._build_auto_checkbox()
        self._auto_wb_toggle = auto_wb_toggle
        self._wb_preset_selector = wb_preset_selector
        def _sync_wb_mode(checked: bool) -> None:
            wb_preset_selector.setEnabled(not checked)
        _sync_wb_mode(auto_wb_toggle.isChecked())
        auto_wb_toggle.toggled.connect(_sync_wb_mode)
        form.addWidget(QtWidgets.QLabel("White balance"), row, 0)
        form.addWidget(wb_preset_selector, row, 1)
        form.addWidget(auto_wb_toggle, row, 2)
        row += 1

        bitrate_selector = QtWidgets.QComboBox()
        bitrate_selector.addItems(["2 Mbps", "4 Mbps", "8 Mbps", "12 Mbps", "20 Mbps", "40 Mbps"])
        self._bitrate_selector = bitrate_selector
        form.addWidget(QtWidgets.QLabel("Bitrate"), row, 0)
        form.addWidget(bitrate_selector, row, 1)
        row += 1

        codec_value = QtWidgets.QLabel("H.264")
        codec_value.setObjectName("CardMeta")
        form.addWidget(QtWidgets.QLabel("Codec"), row, 0)
        form.addWidget(codec_value, row, 1)
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

        advanced_toggle = QtWidgets.QCheckBox("Show advanced settings")
        advanced_toggle.setCursor(QtCore.Qt.PointingHandCursor)
        self._advanced_toggle = advanced_toggle
        layout.addWidget(advanced_toggle)

        advanced_section = QtWidgets.QWidget()
        self._advanced_section = advanced_section
        advanced_form = QtWidgets.QGridLayout(advanced_section)
        advanced_form.setHorizontalSpacing(12)
        advanced_form.setVerticalSpacing(10)
        advanced_form.setColumnStretch(1, 1)

        adv_row = 0
        roi_toggle = self._build_toggle("On", "Off")
        roi_toggle.toggled.connect(lambda checked: self._update_toggle_label(roi_toggle, "On", "Off"))
        self._update_toggle_label(roi_toggle, "On", "Off")
        self._roi_toggle = roi_toggle
        advanced_form.addWidget(QtWidgets.QLabel("ROI enable"), adv_row, 0)
        advanced_form.addWidget(roi_toggle, adv_row, 1)
        adv_row += 1

        roi_widget = QtWidgets.QWidget()
        roi_layout = QtWidgets.QHBoxLayout(roi_widget)
        roi_layout.setContentsMargins(0, 0, 0, 0)
        roi_layout.setSpacing(6)
        roi_x = QtWidgets.QSpinBox(); roi_x.setRange(0, 4000); roi_x.setPrefix("x: ")
        roi_y = QtWidgets.QSpinBox(); roi_y.setRange(0, 4000); roi_y.setPrefix("y: ")
        roi_width = QtWidgets.QSpinBox(); roi_width.setRange(1, 4000); roi_width.setPrefix("w: "); roi_width.setValue(1280)
        roi_height = QtWidgets.QSpinBox(); roi_height.setRange(1, 4000); roi_height.setPrefix("h: "); roi_height.setValue(720)
        self._roi_x = roi_x; self._roi_y = roi_y; self._roi_width = roi_width; self._roi_height = roi_height
        roi_layout.addWidget(roi_x); roi_layout.addWidget(roi_y); roi_layout.addWidget(roi_width); roi_layout.addWidget(roi_height)
        advanced_form.addWidget(QtWidgets.QLabel("ROI settings"), adv_row, 0)
        advanced_form.addWidget(roi_widget, adv_row, 1)
        adv_row += 1

        black_level = self._build_slider()
        self._black_level = black_level
        advanced_form.addWidget(QtWidgets.QLabel("Black level"), adv_row, 0)
        advanced_form.addWidget(black_level, adv_row, 1)
        adv_row += 1

        keyframe_interval = QtWidgets.QSpinBox(); keyframe_interval.setRange(1, 240); keyframe_interval.setValue(30)
        self._keyframe_interval = keyframe_interval
        advanced_form.addWidget(QtWidgets.QLabel("Keyframe interval"), adv_row, 0)
        advanced_form.addWidget(keyframe_interval, adv_row, 1)
        adv_row += 1

        force_idr = QtWidgets.QPushButton("Force IDR")
        force_idr.setCursor(QtCore.Qt.PointingHandCursor)
        force_idr.clicked.connect(lambda: QtWidgets.QMessageBox.information(self, "Encoder", "IDR frame forced."))
        advanced_form.addWidget(QtWidgets.QLabel("Encoder"), adv_row, 0)
        advanced_form.addWidget(force_idr, adv_row, 1)
        adv_row += 1

        ai_input_resolution = QtWidgets.QComboBox()
        ai_input_resolution.addItems(["640 × 360", "1280 × 720", "1920 × 1080"])
        self._ai_input_resolution = ai_input_resolution
        advanced_form.addWidget(QtWidgets.QLabel("AI input resolution"), adv_row, 0)
        advanced_form.addWidget(ai_input_resolution, adv_row, 1)
        adv_row += 1

        ai_rate = QtWidgets.QSpinBox(); ai_rate.setRange(1, 30); ai_rate.setValue(1); ai_rate.setPrefix("Every "); ai_rate.setSuffix(" frame")
        self._ai_rate = ai_rate
        advanced_form.addWidget(QtWidgets.QLabel("AI processing rate"), adv_row, 0)
        advanced_form.addWidget(ai_rate, adv_row, 1)
        adv_row += 1

        overlay_toggle = self._build_toggle("On", "Off")
        overlay_toggle.toggled.connect(lambda checked: self._update_toggle_label(overlay_toggle, "On", "Off"))
        self._update_toggle_label(overlay_toggle, "On", "Off")
        self._overlay_toggle = overlay_toggle
        advanced_form.addWidget(QtWidgets.QLabel("Overlay"), adv_row, 0)
        advanced_form.addWidget(overlay_toggle, adv_row, 1)

        layout.addWidget(advanced_section)
        advanced_section.setVisible(False)
        advanced_toggle.toggled.connect(lambda checked: advanced_section.setVisible(checked))

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

        scroll.setWidget(content)
        card_layout.addWidget(scroll)

        self._apply_loaded_settings()

        return card

    @staticmethod
    def _build_slider() -> QtWidgets.QSlider:
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(40)
        return slider

    @staticmethod
    def _build_auto_checkbox() -> QtWidgets.QCheckBox:
        auto_checkbox = QtWidgets.QCheckBox("Auto")
        auto_checkbox.setCursor(QtCore.Qt.PointingHandCursor)
        auto_checkbox.setChecked(True)
        return auto_checkbox

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
    def _update_toggle_label(toggle: QtWidgets.QCheckBox, label_on: str, label_off: str) -> None:
        toggle.setText(label_on if toggle.isChecked() else label_off)

    def _bind_auto_toggle(self, toggle: QtWidgets.QCheckBox, slider: QtWidgets.QSlider) -> None:
        def _sync_state(checked: bool) -> None:
            slider.setEnabled(not checked)

        toggle.setChecked(True)
        _sync_state(toggle.isChecked())
        toggle.toggled.connect(_sync_state)

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
            "mode": "Opptak",
            "fps": "30 FPS",
            "resolution": "1920 × 1080 (HD)",
            "exposure": {"value": 40, "auto": True},
            "gain": {"value": 40, "auto": True},
            "white_balance": {"auto": True, "preset": "Daylight"},
            "bitrate": "8 Mbps",
            "codec": "H.264",
            "aruco": {"enabled": True, "dictionary": "DICT_4X4_50"},
            "advanced": {
                "roi": {"enabled": False, "x": 0, "y": 0, "width": 1280, "height": 720},
                "black_level": 40,
                "encoder": {"keyframe_interval": 30},
                "ai_cv": {
                    "input_resolution": "1280 × 720",
                    "processing_rate_every_n_frames": 1,
                    "overlay": True,
                },
            },
        }

    def _camera_key(self, index: int | None = None) -> str:
        if index is None:
            index = self._current_camera_index
        return f"camera_{index + 1}"

    def _apply_settings(self) -> None:
        self._persist_current_settings()

    def _apply_loaded_settings(self) -> None:
        settings = self._camera_settings.get(self._camera_key(), {})
        if not settings:
            settings = self._default_settings()
        if not settings:
            return
        self._apply_settings_snapshot(settings)
        name = settings.get("name")
        if isinstance(name, str) and name:
            self._camera_names[self._current_camera_index] = name
            if self._current_camera_label is not None:
                self._current_camera_label.setText(name)
            button = self._camera_buttons[self._current_camera_index]
            button.setText(name)
            edit = self._camera_name_edits[self._current_camera_index]
            edit.setText(name)

    def _collect_settings(self, include_name: bool = True) -> dict[str, object]:
        base = {
            "enabled": bool(self._enable_toggle and self._enable_toggle.isChecked()),
            "mode": self._mode_selector.currentText() if self._mode_selector else "Opptak",
            "fps": self._fps_selector.currentText() if self._fps_selector else "30 FPS",
            "resolution": self._resolution_selector.currentText() if self._resolution_selector else "1920 × 1080 (HD)",
            "exposure": {
                "value": self._exposure_slider.value() if self._exposure_slider else 0,
                "auto": bool(self._auto_exposure_toggle and self._auto_exposure_toggle.isChecked()),
            },
            "gain": {
                "value": self._gain_slider.value() if self._gain_slider else 0,
                "auto": bool(self._auto_gain_toggle and self._auto_gain_toggle.isChecked()),
            },
            "white_balance": {
                "auto": bool(self._auto_wb_toggle and self._auto_wb_toggle.isChecked()),
                "preset": self._wb_preset_selector.currentText() if self._wb_preset_selector else "Daylight",
            },
            "bitrate": self._bitrate_selector.currentText() if self._bitrate_selector else "8 Mbps",
            "codec": "H.264",
            "aruco": {
                "enabled": bool(self._aruco_toggle and self._aruco_toggle.isChecked()),
                "dictionary": self._aruco_dict.currentText() if self._aruco_dict else "",
            },
            "advanced": {
                "roi": {
                    "enabled": bool(self._roi_toggle and self._roi_toggle.isChecked()),
                    "x": self._roi_x.value() if self._roi_x else 0,
                    "y": self._roi_y.value() if self._roi_y else 0,
                    "width": self._roi_width.value() if self._roi_width else 1280,
                    "height": self._roi_height.value() if self._roi_height else 720,
                },
                "black_level": self._black_level.value() if self._black_level else 40,
                "encoder": {
                    "keyframe_interval": self._keyframe_interval.value() if self._keyframe_interval else 30,
                },
                "ai_cv": {
                    "input_resolution": self._ai_input_resolution.currentText() if self._ai_input_resolution else "1280 × 720",
                    "processing_rate_every_n_frames": self._ai_rate.value() if self._ai_rate else 1,
                    "overlay": bool(self._overlay_toggle and self._overlay_toggle.isChecked()),
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
        if self._mode_selector is not None:
            self._mode_selector.setCurrentText(str(settings.get("mode", "Opptak")))
        if self._fps_selector is not None:
            self._fps_selector.setCurrentText(str(settings.get("fps", "30 FPS")))
        if self._resolution_selector is not None:
            self._resolution_selector.setCurrentText(str(settings.get("resolution", "1920 × 1080 (HD)")))
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
        if self._auto_wb_toggle is not None:
            self._auto_wb_toggle.setChecked(bool(white_balance.get("auto", True)))
        if self._wb_preset_selector is not None:
            self._wb_preset_selector.setCurrentText(str(white_balance.get("preset", "Daylight")))
        if self._bitrate_selector is not None:
            self._bitrate_selector.setCurrentText(str(settings.get("bitrate", "8 Mbps")))
        aruco = settings.get("aruco", {})
        if self._aruco_toggle is not None:
            self._aruco_toggle.setChecked(bool(aruco.get("enabled", True)))
            self._update_toggle_label(self._aruco_toggle, "On", "Off")
        if self._aruco_dict is not None:
            self._aruco_dict.setCurrentText(str(aruco.get("dictionary", "DICT_4X4_50")))

        advanced = settings.get("advanced", {})
        roi = advanced.get("roi", {}) if isinstance(advanced, dict) else {}
        if self._roi_toggle is not None:
            self._roi_toggle.setChecked(bool(roi.get("enabled", False)))
            self._update_toggle_label(self._roi_toggle, "On", "Off")
        if self._roi_x is not None:
            self._roi_x.setValue(int(roi.get("x", 0)))
        if self._roi_y is not None:
            self._roi_y.setValue(int(roi.get("y", 0)))
        if self._roi_width is not None:
            self._roi_width.setValue(int(roi.get("width", 1280)))
        if self._roi_height is not None:
            self._roi_height.setValue(int(roi.get("height", 720)))
        if self._black_level is not None:
            self._black_level.setValue(int(advanced.get("black_level", 40)) if isinstance(advanced, dict) else 40)

        encoder = advanced.get("encoder", {}) if isinstance(advanced, dict) else {}
        if self._keyframe_interval is not None:
            self._keyframe_interval.setValue(int(encoder.get("keyframe_interval", 30)))

        ai_cv = advanced.get("ai_cv", {}) if isinstance(advanced, dict) else {}
        if self._ai_input_resolution is not None:
            self._ai_input_resolution.setCurrentText(str(ai_cv.get("input_resolution", "1280 × 720")))
        if self._ai_rate is not None:
            self._ai_rate.setValue(int(ai_cv.get("processing_rate_every_n_frames", 1)))
        if self._overlay_toggle is not None:
            self._overlay_toggle.setChecked(bool(ai_cv.get("overlay", True)))
            self._update_toggle_label(self._overlay_toggle, "On", "Off")

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
