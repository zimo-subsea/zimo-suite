from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets

from zimo.core.api_client import ApiClient
from zimo.core.module_base import ModuleBase

CAMERA_COUNT = 8
FPS_OPTIONS = [30, 60]
RESOLUTION_OPTIONS = ["1920x1080", "1280x720"]
WHITE_BALANCE_PRESETS = ["auto", "daylight", "cloudy", "incandescent", "fluorescent"]
ARUCO_DICTIONARIES = ["DICT_4X4_50", "DICT_4X4_100", "DICT_5X5_50", "DICT_6X6_100", "DICT_7X7_250"]
AI_INPUT_RES_OPTIONS = ["640x360", "960x540"]


class VpuModule(ModuleBase):
    title = "Vision Processing Unit"

    def create_panel(self, api: ApiClient) -> QtWidgets.QWidget:
        return VpuPanel(api)


class VpuPanel(QtWidgets.QWidget):
    """VPU settings panel with explicit customer-safe controls.

    Units:
    - exposure.value uses microseconds (us)
    - gain.value uses dB
    """

    def __init__(self, api: ApiClient) -> None:
        super().__init__()
        self._api = api
        self._settings_file = Path(__file__).with_name("config.json")

        self._config: dict[str, Any] = self._load_or_default_config()
        self._current_camera_id = int(self._config["ui"]["selected_camera_id"])

        self._camera_buttons: list[QtWidgets.QPushButton] = []
        self._is_loading_ui = False

        self._enabled_toggle: QtWidgets.QCheckBox | None = None
        self._fps_selector: QtWidgets.QComboBox | None = None
        self._resolution_selector: QtWidgets.QComboBox | None = None

        self._exposure_auto_toggle: QtWidgets.QCheckBox | None = None
        self._exposure_value: QtWidgets.QSpinBox | None = None
        self._gain_auto_toggle: QtWidgets.QCheckBox | None = None
        self._gain_value: QtWidgets.QDoubleSpinBox | None = None

        self._wb_auto_toggle: QtWidgets.QCheckBox | None = None
        self._wb_mode: QtWidgets.QComboBox | None = None

        self._streaming_enabled: QtWidgets.QCheckBox | None = None
        self._bitrate_mbps: QtWidgets.QSpinBox | None = None

        self._aruco_enabled: QtWidgets.QCheckBox | None = None
        self._aruco_dictionary: QtWidgets.QComboBox | None = None
        self._aruco_dictionary_label: QtWidgets.QLabel | None = None

        self._destination_ip: QtWidgets.QLineEdit | None = None
        self._base_port: QtWidgets.QSpinBox | None = None
        self._allow_save_load: QtWidgets.QCheckBox | None = None

        self._roi_enabled: QtWidgets.QCheckBox | None = None
        self._roi_x: QtWidgets.QSpinBox | None = None
        self._roi_y: QtWidgets.QSpinBox | None = None
        self._roi_width: QtWidgets.QSpinBox | None = None
        self._roi_height: QtWidgets.QSpinBox | None = None
        self._black_level: QtWidgets.QSpinBox | None = None
        self._keyframe_interval: QtWidgets.QSpinBox | None = None

        self._ai_input_resolution: QtWidgets.QComboBox | None = None
        self._process_every_n_frames: QtWidgets.QSpinBox | None = None
        self._overlay_enabled: QtWidgets.QCheckBox | None = None
        self._cv_advanced_box: QtWidgets.QGroupBox | None = None

        self._save_button: QtWidgets.QPushButton | None = None
        self._load_button: QtWidgets.QPushButton | None = None

        self._build_ui()
        self._select_camera(self._current_camera_id)

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("Camera Overview")
        title.setObjectName("PageTitle")
        subtitle = QtWidgets.QLabel("Configure per-camera settings and apply changes to active pipelines.")
        subtitle.setObjectName("PageSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        body = QtWidgets.QHBoxLayout()
        body.setSpacing(16)

        left = self._build_camera_selector()
        right = self._build_settings_panel()

        body.addWidget(left, 1)
        body.addWidget(right, 2)

        layout.addLayout(body)

    def _build_camera_selector(self) -> QtWidgets.QWidget:
        card = QtWidgets.QWidget()
        card.setObjectName("Card")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(8)

        label = QtWidgets.QLabel("Camera Selection")
        label.setObjectName("CardTitle")
        card_layout.addWidget(label)

        button_group = QtWidgets.QButtonGroup(self)
        button_group.setExclusive(True)

        for camera_id in range(1, CAMERA_COUNT + 1):
            button = QtWidgets.QPushButton(f"Camera {camera_id}")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked, cid=camera_id: self._select_camera(cid))
            self._camera_buttons.append(button)
            button_group.addButton(button)
            card_layout.addWidget(button)

        card_layout.addStretch()
        return card

    def _build_settings_panel(self) -> QtWidgets.QWidget:
        card = QtWidgets.QWidget()
        card.setObjectName("Card")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title_row = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Settings (General + Advanced)")
        title.setObjectName("CardTitle")
        title_row.addWidget(title)
        title_row.addStretch()
        docs_button = QtWidgets.QPushButton("Open VPU documentation")
        docs_button.clicked.connect(
            lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://docs.zimo.no/products/vpu/"))
        )
        title_row.addWidget(docs_button)
        layout.addLayout(title_row)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_body = QtWidgets.QWidget()
        form = QtWidgets.QVBoxLayout(scroll_body)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(12)

        form.addWidget(self._build_general_group())
        form.addWidget(self._build_global_group())
        form.addWidget(self._build_advanced_group())

        controls_row = QtWidgets.QHBoxLayout()
        apply_button = QtWidgets.QPushButton("Apply")
        apply_button.clicked.connect(self._apply_settings)

        self._save_button = QtWidgets.QPushButton("Save setup")
        self._save_button.clicked.connect(self._save_preset)

        self._load_button = QtWidgets.QPushButton("Load preset")
        self._load_button.clicked.connect(self._load_preset)

        controls_row.addWidget(apply_button)
        controls_row.addWidget(self._save_button)
        controls_row.addWidget(self._load_button)
        controls_row.addStretch()

        form.addLayout(controls_row)
        form.addStretch()

        scroll.setWidget(scroll_body)
        layout.addWidget(scroll)
        return card

    def _build_general_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("General settings (per selected camera)")
        form = QtWidgets.QFormLayout(group)

        self._enabled_toggle = self._build_toggle("On", "Off")
        form.addRow("Camera", self._enabled_toggle)

        self._fps_selector = QtWidgets.QComboBox()
        self._fps_selector.addItems([str(v) for v in FPS_OPTIONS])
        form.addRow("FPS (restart required)", self._fps_selector)

        self._resolution_selector = QtWidgets.QComboBox()
        self._resolution_selector.addItems(RESOLUTION_OPTIONS)
        form.addRow("Resolution (restart required)", self._resolution_selector)

        exposure_row = QtWidgets.QHBoxLayout()
        self._exposure_auto_toggle = self._build_toggle("Auto", "Manual")
        self._exposure_value = QtWidgets.QSpinBox()
        self._exposure_value.setRange(1, 1_000_000)
        self._exposure_value.setSuffix(" us")
        exposure_row.addWidget(self._exposure_auto_toggle)
        exposure_row.addWidget(self._exposure_value)
        exposure_row.addStretch()
        exposure_widget = QtWidgets.QWidget()
        exposure_widget.setLayout(exposure_row)
        form.addRow("Exposure", exposure_widget)

        gain_row = QtWidgets.QHBoxLayout()
        self._gain_auto_toggle = self._build_toggle("Auto", "Manual")
        self._gain_value = QtWidgets.QDoubleSpinBox()
        self._gain_value.setRange(0.0, 48.0)
        self._gain_value.setSingleStep(0.1)
        self._gain_value.setDecimals(1)
        self._gain_value.setSuffix(" dB")
        gain_row.addWidget(self._gain_auto_toggle)
        gain_row.addWidget(self._gain_value)
        gain_row.addStretch()
        gain_widget = QtWidgets.QWidget()
        gain_widget.setLayout(gain_row)
        form.addRow("Gain", gain_widget)

        wb_row = QtWidgets.QHBoxLayout()
        self._wb_auto_toggle = self._build_toggle("Auto", "Manual")
        self._wb_mode = QtWidgets.QComboBox()
        self._wb_mode.addItems(WHITE_BALANCE_PRESETS)
        wb_row.addWidget(self._wb_auto_toggle)
        wb_row.addWidget(self._wb_mode)
        wb_row.addStretch()
        wb_widget = QtWidgets.QWidget()
        wb_widget.setLayout(wb_row)
        form.addRow("White balance (preset mode)", wb_widget)

        streaming_row = QtWidgets.QHBoxLayout()
        self._streaming_enabled = self._build_toggle("On", "Off")
        self._bitrate_mbps = QtWidgets.QSpinBox()
        self._bitrate_mbps.setRange(1, 200)
        self._bitrate_mbps.setSuffix(" Mbps")
        transport_label = QtWidgets.QLabel("transport = rtp_udp (locked)")
        transport_label.setObjectName("CardMeta")
        streaming_row.addWidget(self._streaming_enabled)
        streaming_row.addWidget(self._bitrate_mbps)
        streaming_row.addWidget(transport_label)
        streaming_row.addStretch()
        streaming_widget = QtWidgets.QWidget()
        streaming_widget.setLayout(streaming_row)
        form.addRow("Streaming", streaming_widget)

        cv_row = QtWidgets.QHBoxLayout()
        self._aruco_enabled = self._build_toggle("On", "Off")
        self._aruco_dictionary_label = QtWidgets.QLabel("ArUco dictionary")
        self._aruco_dictionary = QtWidgets.QComboBox()
        self._aruco_dictionary.addItems(ARUCO_DICTIONARIES)
        cv_row.addWidget(self._aruco_enabled)
        cv_row.addWidget(self._aruco_dictionary_label)
        cv_row.addWidget(self._aruco_dictionary)
        cv_row.addStretch()
        cv_widget = QtWidgets.QWidget()
        cv_widget.setLayout(cv_row)
        form.addRow("CV", cv_widget)

        self._connect_general_signals()
        return group

    def _build_global_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Global settings")
        form = QtWidgets.QFormLayout(group)

        self._destination_ip = QtWidgets.QLineEdit()
        self._base_port = QtWidgets.QSpinBox()
        self._base_port.setRange(1, 65535)
        self._allow_save_load = self._build_toggle("Enabled", "Disabled")

        form.addRow("Destination IP", self._destination_ip)
        form.addRow("Base port", self._base_port)
        form.addRow("Presets save/load", self._allow_save_load)

        self._destination_ip.editingFinished.connect(self._sync_current_camera_from_ui)
        self._base_port.valueChanged.connect(self._sync_current_camera_from_ui)
        self._allow_save_load.toggled.connect(self._sync_current_camera_from_ui)
        return group

    def _build_advanced_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Advanced settings")
        outer = QtWidgets.QVBoxLayout(group)

        sensor_box = QtWidgets.QGroupBox("Sensor")
        sensor_form = QtWidgets.QFormLayout(sensor_box)
        self._roi_enabled = self._build_toggle("On", "Off")
        sensor_form.addRow("ROI enabled (restart required)", self._roi_enabled)

        roi_row = QtWidgets.QHBoxLayout()
        self._roi_x = QtWidgets.QSpinBox()
        self._roi_y = QtWidgets.QSpinBox()
        self._roi_width = QtWidgets.QSpinBox()
        self._roi_height = QtWidgets.QSpinBox()
        for spin in [self._roi_x, self._roi_y, self._roi_width, self._roi_height]:
            spin.setRange(0, 8192)
            spin.setFixedWidth(90)
        self._roi_width.setMinimum(1)
        self._roi_height.setMinimum(1)

        roi_row.addWidget(QtWidgets.QLabel("x"))
        roi_row.addWidget(self._roi_x)
        roi_row.addWidget(QtWidgets.QLabel("y"))
        roi_row.addWidget(self._roi_y)
        roi_row.addWidget(QtWidgets.QLabel("w"))
        roi_row.addWidget(self._roi_width)
        roi_row.addWidget(QtWidgets.QLabel("h"))
        roi_row.addWidget(self._roi_height)
        roi_row.addStretch()

        roi_widget = QtWidgets.QWidget()
        roi_widget.setLayout(roi_row)
        sensor_form.addRow("ROI", roi_widget)

        self._black_level = QtWidgets.QSpinBox()
        self._black_level.setRange(0, 4095)
        sensor_form.addRow("Black level", self._black_level)

        encoder_box = QtWidgets.QGroupBox("Encoder")
        encoder_form = QtWidgets.QFormLayout(encoder_box)

        self._keyframe_interval = QtWidgets.QSpinBox()
        self._keyframe_interval.setRange(1, 300)
        encoder_form.addRow("Keyframe interval (GOP)", self._keyframe_interval)

        force_idr = QtWidgets.QPushButton("Force IDR")
        force_idr.clicked.connect(self._force_idr)
        encoder_form.addRow("Action", force_idr)

        self._cv_advanced_box = QtWidgets.QGroupBox("CV advanced")
        cv_adv_form = QtWidgets.QFormLayout(self._cv_advanced_box)

        self._ai_input_resolution = QtWidgets.QComboBox()
        self._ai_input_resolution.addItems(AI_INPUT_RES_OPTIONS)

        self._process_every_n_frames = QtWidgets.QSpinBox()
        self._process_every_n_frames.setRange(1, 32)

        self._overlay_enabled = self._build_toggle("On", "Off")

        cv_adv_form.addRow("AI input resolution", self._ai_input_resolution)
        cv_adv_form.addRow("Process every N frames", self._process_every_n_frames)
        cv_adv_form.addRow("Overlay", self._overlay_enabled)

        outer.addWidget(sensor_box)
        outer.addWidget(encoder_box)
        outer.addWidget(self._cv_advanced_box)

        self._connect_advanced_signals()
        return group

    def _connect_general_signals(self) -> None:
        for signal, handler in [
            (self._enabled_toggle.toggled, self._sync_current_camera_from_ui),
            (self._fps_selector.currentTextChanged, self._sync_current_camera_from_ui),
            (self._resolution_selector.currentTextChanged, self._sync_current_camera_from_ui),
            (self._exposure_auto_toggle.toggled, self._sync_current_camera_from_ui),
            (self._exposure_value.valueChanged, self._sync_current_camera_from_ui),
            (self._gain_auto_toggle.toggled, self._sync_current_camera_from_ui),
            (self._gain_value.valueChanged, self._sync_current_camera_from_ui),
            (self._wb_auto_toggle.toggled, self._sync_current_camera_from_ui),
            (self._wb_mode.currentTextChanged, self._sync_current_camera_from_ui),
            (self._streaming_enabled.toggled, self._sync_current_camera_from_ui),
            (self._bitrate_mbps.valueChanged, self._sync_current_camera_from_ui),
            (self._aruco_enabled.toggled, self._sync_current_camera_from_ui),
            (self._aruco_dictionary.currentTextChanged, self._sync_current_camera_from_ui),
        ]:
            signal.connect(handler)

    def _connect_advanced_signals(self) -> None:
        for signal, handler in [
            (self._roi_enabled.toggled, self._sync_current_camera_from_ui),
            (self._roi_x.valueChanged, self._sync_current_camera_from_ui),
            (self._roi_y.valueChanged, self._sync_current_camera_from_ui),
            (self._roi_width.valueChanged, self._sync_current_camera_from_ui),
            (self._roi_height.valueChanged, self._sync_current_camera_from_ui),
            (self._black_level.valueChanged, self._sync_current_camera_from_ui),
            (self._keyframe_interval.valueChanged, self._sync_current_camera_from_ui),
            (self._ai_input_resolution.currentTextChanged, self._sync_current_camera_from_ui),
            (self._process_every_n_frames.valueChanged, self._sync_current_camera_from_ui),
            (self._overlay_enabled.toggled, self._sync_current_camera_from_ui),
        ]:
            signal.connect(handler)

    @staticmethod
    def _build_toggle(label_on: str, label_off: str) -> QtWidgets.QCheckBox:
        toggle = QtWidgets.QCheckBox(label_on)
        toggle.setProperty("label_on", label_on)
        toggle.setProperty("label_off", label_off)
        toggle.setChecked(True)

        def _sync_label(checked: bool) -> None:
            toggle.setText(label_on if checked else label_off)

        toggle.toggled.connect(_sync_label)
        _sync_label(True)
        return toggle

    def _camera_key(self, camera_id: int | None = None) -> str:
        cid = camera_id if camera_id is not None else self._current_camera_id
        return f"camera_{cid}"

    def _load_or_default_config(self) -> dict[str, Any]:
        base = self._default_config()
        if not self._settings_file.exists():
            return base
        try:
            raw = json.loads(self._settings_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return base
        return self._merge_with_defaults(raw, base)

    def _default_config(self) -> dict[str, Any]:
        config: dict[str, Any] = {
            "network": {"destination_ip": "239.0.0.1", "base_port": 5000},
            "ui": {"selected_camera_id": 1},
            "presets": {"allow_save_load": True},
            "cameras": {},
        }
        for camera_id in range(1, CAMERA_COUNT + 1):
            config["cameras"][self._camera_key(camera_id)] = self._default_camera_settings()
        return config

    @staticmethod
    def _default_camera_settings() -> dict[str, Any]:
        return {
            "enabled": True,
            "fps": 30,
            "resolution": "1920x1080",
            "exposure": {"auto": True, "value": 10000},
            "gain": {"auto": True, "value": 8.0},
            "white_balance": {"auto": True, "mode": "auto"},
            "streaming": {"enabled": True, "bitrate_mbps": 8, "transport": "rtp_udp"},
            "cv": {"aruco_enabled": True, "aruco_dictionary": "DICT_4X4_50"},
            "sensor": {
                "roi_enabled": False,
                "roi": {"x": 0, "y": 0, "width": 1920, "height": 1080},
                "black_level": 16,
            },
            "encoder": {"keyframe_interval": 30},
            "cv_advanced": {
                "ai_input_resolution": "640x360",
                "process_every_n_frames": 1,
                "overlay_enabled": True,
            },
        }

    def _merge_with_defaults(self, source: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
        merged = copy.deepcopy(defaults)
        for key, value in source.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._merge_with_defaults(value, merged[key])
            else:
                merged[key] = value

        camera_nodes = merged.get("cameras", {})
        for camera_id in range(1, CAMERA_COUNT + 1):
            cam_key = self._camera_key(camera_id)
            if cam_key not in camera_nodes:
                camera_nodes[cam_key] = self._default_camera_settings()
        merged["cameras"] = camera_nodes

        selected_id = int(merged.get("ui", {}).get("selected_camera_id", 1))
        merged["ui"]["selected_camera_id"] = min(max(selected_id, 1), CAMERA_COUNT)
        return merged

    def _select_camera(self, camera_id: int) -> None:
        self._sync_current_camera_from_ui()
        self._current_camera_id = camera_id
        self._config["ui"]["selected_camera_id"] = camera_id

        for index, button in enumerate(self._camera_buttons, start=1):
            button.setChecked(index == camera_id)

        self._load_camera_into_ui(camera_id)

    def _load_camera_into_ui(self, camera_id: int) -> None:
        camera = self._config["cameras"][self._camera_key(camera_id)]
        self._is_loading_ui = True

        self._enabled_toggle.setChecked(bool(camera["enabled"]))
        self._fps_selector.setCurrentText(str(camera["fps"]))
        self._resolution_selector.setCurrentText(str(camera["resolution"]))

        self._exposure_auto_toggle.setChecked(bool(camera["exposure"]["auto"]))
        self._exposure_value.setValue(int(camera["exposure"]["value"]))
        self._exposure_value.setEnabled(not self._exposure_auto_toggle.isChecked())

        self._gain_auto_toggle.setChecked(bool(camera["gain"]["auto"]))
        self._gain_value.setValue(float(camera["gain"]["value"]))
        self._gain_value.setEnabled(not self._gain_auto_toggle.isChecked())

        self._wb_auto_toggle.setChecked(bool(camera["white_balance"]["auto"]))
        self._wb_mode.setCurrentText(str(camera["white_balance"]["mode"]))

        self._streaming_enabled.setChecked(bool(camera["streaming"]["enabled"]))
        self._bitrate_mbps.setValue(int(camera["streaming"]["bitrate_mbps"]))

        self._aruco_enabled.setChecked(bool(camera["cv"]["aruco_enabled"]))
        self._aruco_dictionary.setCurrentText(str(camera["cv"]["aruco_dictionary"]))

        roi = camera["sensor"]["roi"]
        self._roi_enabled.setChecked(bool(camera["sensor"]["roi_enabled"]))
        self._roi_x.setValue(int(roi["x"]))
        self._roi_y.setValue(int(roi["y"]))
        self._roi_width.setValue(int(roi["width"]))
        self._roi_height.setValue(int(roi["height"]))
        self._black_level.setValue(int(camera["sensor"]["black_level"]))

        self._keyframe_interval.setValue(int(camera["encoder"]["keyframe_interval"]))

        self._ai_input_resolution.setCurrentText(str(camera["cv_advanced"]["ai_input_resolution"]))
        self._process_every_n_frames.setValue(int(camera["cv_advanced"]["process_every_n_frames"]))
        self._overlay_enabled.setChecked(bool(camera["cv_advanced"]["overlay_enabled"]))

        self._destination_ip.setText(str(self._config["network"]["destination_ip"]))
        self._base_port.setValue(int(self._config["network"]["base_port"]))
        self._allow_save_load.setChecked(bool(self._config["presets"]["allow_save_load"]))

        self._sync_dynamic_visibility(camera)
        self._is_loading_ui = False

    def _sync_dynamic_visibility(self, camera: dict[str, Any] | None = None) -> None:
        if camera is None:
            camera = self._config["cameras"][self._camera_key()]

        exposure_auto = bool(camera["exposure"]["auto"])
        gain_auto = bool(camera["gain"]["auto"])
        aruco_enabled = bool(camera["cv"]["aruco_enabled"])
        allow_presets = bool(self._config["presets"]["allow_save_load"])

        self._exposure_value.setEnabled(not exposure_auto)
        self._gain_value.setEnabled(not gain_auto)
        self._aruco_dictionary.setVisible(aruco_enabled)
        self._aruco_dictionary_label.setVisible(aruco_enabled)
        self._cv_advanced_box.setVisible(aruco_enabled)

        self._save_button.setEnabled(allow_presets)
        self._load_button.setEnabled(allow_presets)

    def _sync_current_camera_from_ui(self, *_args: object) -> None:
        if self._is_loading_ui:
            return

        camera = self._config["cameras"][self._camera_key()]
        camera["enabled"] = bool(self._enabled_toggle.isChecked())
        camera["fps"] = int(self._fps_selector.currentText())
        camera["resolution"] = self._resolution_selector.currentText()

        camera["exposure"]["auto"] = bool(self._exposure_auto_toggle.isChecked())
        camera["exposure"]["value"] = int(self._exposure_value.value())

        camera["gain"]["auto"] = bool(self._gain_auto_toggle.isChecked())
        camera["gain"]["value"] = float(self._gain_value.value())

        camera["white_balance"]["auto"] = bool(self._wb_auto_toggle.isChecked())
        camera["white_balance"]["mode"] = self._wb_mode.currentText()

        camera["streaming"]["enabled"] = bool(self._streaming_enabled.isChecked())
        camera["streaming"]["bitrate_mbps"] = int(self._bitrate_mbps.value())
        camera["streaming"]["transport"] = "rtp_udp"

        camera["cv"]["aruco_enabled"] = bool(self._aruco_enabled.isChecked())
        camera["cv"]["aruco_dictionary"] = self._aruco_dictionary.currentText()

        camera["sensor"]["roi_enabled"] = bool(self._roi_enabled.isChecked())
        camera["sensor"]["roi"] = {
            "x": int(self._roi_x.value()),
            "y": int(self._roi_y.value()),
            "width": int(self._roi_width.value()),
            "height": int(self._roi_height.value()),
        }
        camera["sensor"]["black_level"] = int(self._black_level.value())

        camera["encoder"]["keyframe_interval"] = int(self._keyframe_interval.value())

        camera["cv_advanced"]["ai_input_resolution"] = self._ai_input_resolution.currentText()
        camera["cv_advanced"]["process_every_n_frames"] = int(self._process_every_n_frames.value())
        camera["cv_advanced"]["overlay_enabled"] = bool(self._overlay_enabled.isChecked())

        self._config["network"]["destination_ip"] = self._destination_ip.text().strip()
        self._config["network"]["base_port"] = int(self._base_port.value())
        self._config["presets"]["allow_save_load"] = bool(self._allow_save_load.isChecked())
        self._config["ui"]["selected_camera_id"] = self._current_camera_id

        self._sync_dynamic_visibility(camera)

    def _apply_settings(self) -> None:
        self._sync_current_camera_from_ui()
        self._settings_file.write_text(json.dumps(self._config, indent=2, ensure_ascii=False), encoding="utf-8")
        self._api.apply_vpu_configuration(self._config)

    def _force_idr(self) -> None:
        self._api.force_idr(self._current_camera_id)

    def _presets_dir(self) -> Path:
        return Path(__file__).with_name("presets")

    def _save_preset(self) -> None:
        self._sync_current_camera_from_ui()
        if not self._config["presets"]["allow_save_load"]:
            return

        preset_name, ok = QtWidgets.QInputDialog.getText(self, "Save preset", "Preset name:")
        if not ok or not preset_name.strip():
            return

        safe_name = preset_name.strip().replace("/", "-")
        preset_path = self._presets_dir() / f"{safe_name}.json"
        preset_path.parent.mkdir(parents=True, exist_ok=True)
        preset_path.write_text(json.dumps(self._config, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load_preset(self) -> None:
        if not self._config["presets"]["allow_save_load"]:
            return

        presets_dir = self._presets_dir()
        if not presets_dir.exists():
            QtWidgets.QMessageBox.information(self, "Load preset", "No presets found.")
            return

        files = sorted(presets_dir.glob("*.json"))
        if not files:
            QtWidgets.QMessageBox.information(self, "Load preset", "No presets found.")
            return

        names = [f.stem for f in files]
        selected, ok = QtWidgets.QInputDialog.getItem(self, "Load preset", "Choose preset:", names, 0, False)
        if not ok or not selected:
            return

        try:
            loaded = json.loads((presets_dir / f"{selected}.json").read_text(encoding="utf-8"))
            self._config = self._merge_with_defaults(loaded, self._default_config())
        except (json.JSONDecodeError, OSError):
            QtWidgets.QMessageBox.warning(self, "Load preset", "Preset could not be loaded.")
            return

        self._current_camera_id = int(self._config["ui"]["selected_camera_id"])
        self._select_camera(self._current_camera_id)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    panel = VpuPanel(ApiClient())
    panel.resize(1200, 900)
    panel.show()
    sys.exit(app.exec())
