from __future__ import annotations

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
        self._camera_names = [f"Camera {index}" for index in range(1, 9)]
        self._camera_connected = [True, True, False, True, False, True, True, False]
        self._camera_buttons: list[QtWidgets.QPushButton] = []
        self._camera_name_edits: list[QtWidgets.QLineEdit] = []
        self._current_camera_index = 0
        self._current_camera_label: QtWidgets.QLabel | None = None
        self._camera_pen_buttons: list[QtWidgets.QPushButton] = []

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        header = QtWidgets.QLabel("Camera Overview")
        header.setObjectName("PageTitle")
        subtitle = QtWidgets.QLabel("Monitor the machine vision feed and adjust capture settings.")
        subtitle.setObjectName("PageSubtitle")

        layout.addWidget(header)
        layout.addWidget(subtitle)
        layout.addWidget(self._build_status_legend())

        body_layout = QtWidgets.QHBoxLayout()
        body_layout.setSpacing(16)

        left_column = QtWidgets.QVBoxLayout()
        left_column.setSpacing(16)

        selection_card = self._build_selection_card()
        status_card = self._build_status_card()

        left_column.addWidget(selection_card, 1)
        left_column.addWidget(status_card, 1)

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
        layout.addWidget(current_label)

        form = QtWidgets.QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        row = 0

        enable_toggle = self._build_toggle("On")
        form.addWidget(QtWidgets.QLabel("Enable / Disable camera"), row, 0)
        form.addWidget(enable_toggle, row, 1)
        row += 1

        auto_exposure_toggle = self._build_toggle("Auto")
        form.addWidget(QtWidgets.QLabel("Auto Exposure"), row, 0)
        form.addWidget(auto_exposure_toggle, row, 1)
        row += 1

        auto_gain_toggle = self._build_toggle("Auto")
        form.addWidget(QtWidgets.QLabel("Auto Gain"), row, 0)
        form.addWidget(auto_gain_toggle, row, 1)
        row += 1

        auto_wb_toggle = self._build_toggle("Auto")
        form.addWidget(QtWidgets.QLabel("Auto WB"), row, 0)
        form.addWidget(auto_wb_toggle, row, 1)
        row += 1

        exposure_slider = self._build_slider()
        form.addWidget(QtWidgets.QLabel("Exposure"), row, 0)
        form.addWidget(exposure_slider, row, 1)
        row += 1

        gain_slider = self._build_slider()
        form.addWidget(QtWidgets.QLabel("Gain"), row, 0)
        form.addWidget(gain_slider, row, 1)
        row += 1

        wb_slider = self._build_slider()
        form.addWidget(QtWidgets.QLabel("White balance"), row, 0)
        form.addWidget(wb_slider, row, 1)
        row += 1

        reset_button = QtWidgets.QPushButton("Reset to defaults")
        reset_button.setCursor(QtCore.Qt.PointingHandCursor)
        form.addWidget(QtWidgets.QLabel("Defaults"), row, 0)
        form.addWidget(reset_button, row, 1)
        row += 1

        advanced_button = QtWidgets.QPushButton("Advanced settings")
        advanced_button.setCursor(QtCore.Qt.PointingHandCursor)
        form.addWidget(QtWidgets.QLabel("Advanced"), row, 0)
        form.addWidget(advanced_button, row, 1)
        row += 1

        aruco_toggle = self._build_toggle("On")
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
        form.addWidget(QtWidgets.QLabel("ArUco dictionary"), row, 0)
        form.addWidget(aruco_dict, row, 1)
        row += 1

        layout.addLayout(form)
        layout.addStretch()

        return card

    @staticmethod
    def _build_slider() -> QtWidgets.QSlider:
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(40)
        return slider

    @staticmethod
    def _build_toggle(label: str) -> QtWidgets.QPushButton:
        toggle = QtWidgets.QPushButton(label)
        toggle.setCheckable(True)
        toggle.setCursor(QtCore.Qt.PointingHandCursor)
        toggle.setChecked(True)
        return toggle

    @staticmethod
    def _build_status_dot(is_online: bool) -> QtWidgets.QLabel:
        dot = QtWidgets.QLabel("●")
        dot.setObjectName("StatusDot")
        dot.setProperty("severity", "success" if is_online else "danger")
        return dot

    def _build_status_legend(self) -> QtWidgets.QWidget:
        legend = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(legend)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QtWidgets.QLabel("Status legend:")
        title.setObjectName("CardMeta")

        online_dot = self._build_status_dot(True)
        online_label = QtWidgets.QLabel("Connected")
        online_label.setObjectName("CardMeta")

        offline_dot = self._build_status_dot(False)
        offline_label = QtWidgets.QLabel("Disconnected")
        offline_label.setObjectName("CardMeta")

        layout.addWidget(title)
        layout.addWidget(online_dot)
        layout.addWidget(online_label)
        layout.addWidget(offline_dot)
        layout.addWidget(offline_label)
        layout.addStretch()
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


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    panel = CameraPanel(ApiClient())
    panel.resize(800, 600)
    panel.show()
    sys.exit(app.exec())
