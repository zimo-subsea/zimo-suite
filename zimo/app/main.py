from pathlib import Path
import sys

from PySide6 import QtGui, QtWidgets

from zimo.app.shell import ZiMOShell


def load_theme(app: QtWidgets.QApplication) -> None:
    theme_path = Path(__file__).with_name("theme.qss")
    app.setStyleSheet(theme_path.read_text(encoding="utf-8"))


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("ZiMO Suite")
    app.setOrganizationName("ZiMO Suite")
    icon_path = Path(__file__).with_name("logo.ico")
    app.setWindowIcon(QtGui.QIcon(str(icon_path)))
    load_theme(app)

    window = ZiMOShell()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
