from pathlib import Path
import sys

from PySide6 import QtGui, QtWidgets

from zimo.app.shell import ZiMOShell


def configure_native_ui(app: QtWidgets.QApplication) -> None:
    """Use platform-native styling and palette."""
    app.setStyleSheet("")
    app.setPalette(app.style().standardPalette())


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("ZiMO Suite")
    app.setOrganizationName("ZiMO Suite")
    icon_path = Path(__file__).with_name("logo.ico")
    app.setWindowIcon(QtGui.QIcon(str(icon_path)))
    configure_native_ui(app)

    window = ZiMOShell()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
