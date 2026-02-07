from __future__ import annotations

import json
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from zimo.core.api_client import ApiClient
from zimo.core.module_base import ModuleBase


class CameraModule(ModuleBase):
    title = "Vision Processing Unit"

    def create_panel(self, api: ApiClient) -> QtWidgets.QWidget:
        return CameraPanel(api)


class CameraPanel(QtWidgets.QWidget):
    def __init__(self, api: ApiClient) -> None:
        super().__init__()
        self._api = api
        self._camera_settings = [self._default_settings(index) for index in range(1, 9)]
        self._load_settings_from_disk()
        self._camera_names = [camera["name"] for camera in self._camera_settings]
        self._camera_connected = [True, True, False, True, False, True, True, False]
        self._camera_buttons: list[QtWidgets.QPushButton] = []
        self._camera_name_edits: list[QtWidgets.QLineEdit] = []
        self._current_camera_index = 0
        self._current_camera_label: QtWidgets.QLabel | None = None
        self._camera_pen_buttons: list[QtWidgets.QPushButton] = []
        self._enable_toggle: QtWidgets.QCheckBox | None = None
        self._fps_selector: QtWidgets.QComboBox | None = None
        self._resolution_selector: QtWidgets.QComboBox | None = None
        self._exposure_slider: QtWidgets.QSlider | None = None
        self._auto_exposure_toggle: QtWidgets.QCheckBox | None = None
        self._gain_slider: QtWidgets.QSlider | None = None
        self._auto_gain_toggle: QtWidgets.QCheckBox | None = None
        self._wb_slider: QtWidgets.QSlider | None = None
        self._auto_wb_toggle: QtWidgets.QCheckBox | None = None
        self._aruco_toggle: QtWidgets.QCheckBox | None = None
        self._aruco_dict: QtWidgets.QComboBox | None = None

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
        self._apply_settings_to_ui(self._current_camera_index)

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
        enable_toggle.toggled.connect(lambda checked: self._update_current_setting("enabled", checked))
        self._update_toggle_label(enable_toggle, "On", "Off")
        header_row.addWidget(enable_toggle)
        self._enable_toggle = enable_toggle
        layout.addLayout(header_row)

        form = QtWidgets.QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        form.setColumnStretch(1, 1)

        row = 0

        fps_selector = QtWidgets.QComboBox()
        fps_selector.addItems(["24 FPS", "30 FPS", "60 FPS", "90 FPS", "120 FPS"])
        fps_selector.currentTextChanged.connect(lambda value: self._update_current_setting("fps", value))
        form.addWidget(QtWidgets.QLabel("FPS"), row, 0)
        form.addWidget(fps_selector, row, 1)
        row += 1
        self._fps_selector = fps_selector

        resolution_selector = QtWidgets.QComboBox()
        resolution_selector.addItems(["1280 × 720", "1920 × 1080", "2560 × 1440", "3840 × 2160 (4K)"])
        resolution_selector.currentTextChanged.connect(
            lambda value: self._update_current_setting("resolution", value)
        )
        form.addWidget(QtWidgets.QLabel("Resolution"), row, 0)
        form.addWidget(resolution_selector, row, 1)
        row += 1
        self._resolution_selector = resolution_selector

        exposure_slider = self._build_slider()
        auto_exposure_toggle = self._build_toggle("Auto", "Manual")
        self._bind_auto_toggle(auto_exposure_toggle, exposure_slider, "exposure_auto")
        exposure_slider.valueChanged.connect(lambda value: self._update_current_setting("exposure", value))
        form.addWidget(QtWidgets.QLabel("Exposure"), row, 0)
        form.addWidget(exposure_slider, row, 1)
        form.addWidget(auto_exposure_toggle, row, 2)
        row += 1
        self._exposure_slider = exposure_slider
        self._auto_exposure_toggle = auto_exposure_toggle

        gain_slider = self._build_slider()
        auto_gain_toggle = self._build_toggle("Auto", "Manual")
        self._bind_auto_toggle(auto_gain_toggle, gain_slider, "gain_auto")
        gain_slider.valueChanged.connect(lambda value: self._update_current_setting("gain", value))
        form.addWidget(QtWidgets.QLabel("Gain"), row, 0)
        form.addWidget(gain_slider, row, 1)
        form.addWidget(auto_gain_toggle, row, 2)
        row += 1
        self._gain_slider = gain_slider
        self._auto_gain_toggle = auto_gain_toggle

        wb_slider = self._build_slider()
        auto_wb_toggle = self._build_toggle("Auto", "Manual")
        self._bind_auto_toggle(auto_wb_toggle, wb_slider, "white_balance_auto")
        wb_slider.valueChanged.connect(lambda value: self._update_current_setting("white_balance", value))
        form.addWidget(QtWidgets.QLabel("White balance"), row, 0)
        form.addWidget(wb_slider, row, 1)
        form.addWidget(auto_wb_toggle, row, 2)
        row += 1
        self._wb_slider = wb_slider
        self._auto_wb_toggle = auto_wb_toggle

        reset_button = QtWidgets.QPushButton("Reset to defaults")
        reset_button.setCursor(QtCore.Qt.PointingHandCursor)
        reset_button.clicked.connect(self._reset_current_camera)
        form.addWidget(QtWidgets.QLabel("Defaults"), row, 0)
        form.addWidget(reset_button, row, 1)
        row += 1
        self._reset_button = reset_button

        aruco_toggle = self._build_toggle("On", "Off")
        aruco_toggle.toggled.connect(lambda checked: self._update_toggle_label(aruco_toggle, "On", "Off"))
        aruco_toggle.toggled.connect(lambda checked: self._update_current_setting("aruco_enabled", checked))
        self._update_toggle_label(aruco_toggle, "On", "Off")
        form.addWidget(QtWidgets.QLabel("Enable ArUco"), row, 0)
        form.addWidget(aruco_toggle, row, 1)
        row += 1
        self._aruco_toggle = aruco_toggle

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
        aruco_dict.currentTextChanged.connect(lambda value: self._update_current_setting("aruco_dict", value))
        form.addWidget(QtWidgets.QLabel("ArUco dictionary"), row, 0)
        form.addWidget(aruco_dict, row, 1)
        row += 1
        self._aruco_dict = aruco_dict

        layout.addLayout(form)

        gear_row = QtWidgets.QHBoxLayout()
        advanced_button = QtWidgets.QPushButton("⚙")
        advanced_button.setObjectName("GearButton")
        advanced_button.setCursor(QtCore.Qt.PointingHandCursor)
        advanced_label = QtWidgets.QLabel("Advanced settings")
        advanced_label.setObjectName("CardMeta")
        gear_row.addStretch()
        gear_row.addWidget(advanced_label)
        gear_row.addWidget(advanced_button)
        layout.addLayout(gear_row)

        presets_row = QtWidgets.QHBoxLayout()
        save_button = QtWidgets.QPushButton("Save setup")
        save_button.setCursor(QtCore.Qt.PointingHandCursor)
        load_button = QtWidgets.QPushButton("Load preset")
        load_button.setCursor(QtCore.Qt.PointingHandCursor)
        save_button.clicked.connect(self._save_settings)
        load_button.clicked.connect(self._reload_settings_from_disk)
        presets_row.addWidget(save_button)
        presets_row.addWidget(load_button)
        presets_row.addStretch()
        layout.addLayout(presets_row)
        layout.addStretch()

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
    def _update_toggle_label(toggle: QtWidgets.QCheckBox, label_on: str, label_off: str) -> None:
        toggle.setText(label_on if toggle.isChecked() else label_off)

    def _bind_auto_toggle(
        self, toggle: QtWidgets.QCheckBox, slider: QtWidgets.QSlider, setting_key: str
    ) -> None:
        def _sync_state(checked: bool) -> None:
            toggle.setText("Auto" if checked else "Manual")
            slider.setEnabled(not checked)
            self._update_current_setting(setting_key, checked)

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

    @staticmethod
    def _default_settings(index: int) -> dict:
        return {
            "name": f"Camera {index}",
            "enabled": True,
            "fps": "24 FPS",
            "resolution": "1280 × 720",
            "exposure": 40,
            "exposure_auto": True,
            "gain": 40,
            "gain_auto": True,
            "white_balance": 40,
            "white_balance_auto": True,
            "aruco_enabled": True,
            "aruco_dict": "DICT_4X4_50",
        }

    @staticmethod
    def _settings_path() -> Path:
        settings_dir = Path.home() / ".zimo"
        settings_dir.mkdir(parents=True, exist_ok=True)
        return settings_dir / "camera_settings.json"

    def _load_settings_from_disk(self) -> None:
        path = self._settings_path()
        if not path.exists():
            return
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        if not isinstance(payload, list) or len(payload) != 8:
            return
        for index, settings in enumerate(payload):
            if not isinstance(settings, dict):
                continue
            for key, value in settings.items():
                if key in self._camera_settings[index]:
                    self._camera_settings[index][key] = value

    def _save_settings(self) -> None:
        path = self._settings_path()
        path.write_text(json.dumps(self._camera_settings, indent=2), encoding="utf-8")

    def _reload_settings_from_disk(self) -> None:
        self._load_settings_from_disk()
        self._camera_names = [camera["name"] for camera in self._camera_settings]
        for index, name in enumerate(self._camera_names):
            self._camera_buttons[index].setText(name)
            self._camera_name_edits[index].setText(name)
        if self._current_camera_label is not None:
            self._current_camera_label.setText(self._camera_names[self._current_camera_index])
        self._apply_settings_to_ui(self._current_camera_index)

    def _update_current_setting(self, key: str, value: object) -> None:
        if getattr(self, "_is_applying_settings", False):
            return
        self._camera_settings[self._current_camera_index][key] = value
        self._save_settings()

    def _reset_current_camera(self) -> None:
        default = self._default_settings(self._current_camera_index + 1)
        name = self._camera_settings[self._current_camera_index]["name"]
        default["name"] = name
        self._camera_settings[self._current_camera_index] = default
        self._apply_settings_to_ui(self._current_camera_index)
        self._save_settings()

    def _apply_settings_to_ui(self, index: int) -> None:
        self._is_applying_settings = True
        try:
            settings = self._camera_settings[index]
            if self._enable_toggle is not None:
                self._enable_toggle.blockSignals(True)
                self._enable_toggle.setChecked(settings["enabled"])
                self._enable_toggle.blockSignals(False)
                self._update_toggle_label(self._enable_toggle, "On", "Off")
            if self._fps_selector is not None:
                self._fps_selector.blockSignals(True)
                self._fps_selector.setCurrentText(settings["fps"])
                self._fps_selector.blockSignals(False)
            if self._resolution_selector is not None:
                self._resolution_selector.blockSignals(True)
                self._resolution_selector.setCurrentText(settings["resolution"])
                self._resolution_selector.blockSignals(False)
            if self._exposure_slider is not None:
                self._exposure_slider.blockSignals(True)
                self._exposure_slider.setValue(int(settings["exposure"]))
                self._exposure_slider.blockSignals(False)
            if self._auto_exposure_toggle is not None:
                self._auto_exposure_toggle.blockSignals(True)
                self._auto_exposure_toggle.setChecked(bool(settings["exposure_auto"]))
                self._auto_exposure_toggle.blockSignals(False)
                self._auto_exposure_toggle.setText("Auto" if settings["exposure_auto"] else "Manual")
                if self._exposure_slider is not None:
                    self._exposure_slider.setEnabled(not settings["exposure_auto"])
            if self._gain_slider is not None:
                self._gain_slider.blockSignals(True)
                self._gain_slider.setValue(int(settings["gain"]))
                self._gain_slider.blockSignals(False)
            if self._auto_gain_toggle is not None:
                self._auto_gain_toggle.blockSignals(True)
                self._auto_gain_toggle.setChecked(bool(settings["gain_auto"]))
                self._auto_gain_toggle.blockSignals(False)
                self._auto_gain_toggle.setText("Auto" if settings["gain_auto"] else "Manual")
                if self._gain_slider is not None:
                    self._gain_slider.setEnabled(not settings["gain_auto"])
            if self._wb_slider is not None:
                self._wb_slider.blockSignals(True)
                self._wb_slider.setValue(int(settings["white_balance"]))
                self._wb_slider.blockSignals(False)
            if self._auto_wb_toggle is not None:
                self._auto_wb_toggle.blockSignals(True)
                self._auto_wb_toggle.setChecked(bool(settings["white_balance_auto"]))
                self._auto_wb_toggle.blockSignals(False)
                self._auto_wb_toggle.setText("Auto" if settings["white_balance_auto"] else "Manual")
                if self._wb_slider is not None:
                    self._wb_slider.setEnabled(not settings["white_balance_auto"])
            if self._aruco_toggle is not None:
                self._aruco_toggle.blockSignals(True)
                self._aruco_toggle.setChecked(settings["aruco_enabled"])
                self._aruco_toggle.blockSignals(False)
                self._update_toggle_label(self._aruco_toggle, "On", "Off")
            if self._aruco_dict is not None:
                self._aruco_dict.blockSignals(True)
                self._aruco_dict.setCurrentText(settings["aruco_dict"])
                self._aruco_dict.blockSignals(False)
        finally:
            self._is_applying_settings = False

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
        self._apply_settings_to_ui(index)

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
        self._camera_settings[index]["name"] = new_name
        self._camera_buttons[index].setText(new_name)
        edit.setText(new_name)
        edit.setVisible(False)
        self._camera_buttons[index].setVisible(True)
        if self._current_camera_label is not None and index == self._current_camera_index:
            self._current_camera_label.setText(new_name)
        self._save_settings()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    panel = CameraPanel(ApiClient())
    panel.resize(800, 600)
    panel.show()
    sys.exit(app.exec())
