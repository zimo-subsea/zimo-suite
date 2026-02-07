from pathlib import Path
import sys

from PySide6 import QtGui, QtWidgets

from zimo.app.shell import ZiMOShell


def load_theme(app: QtWidgets.QApplication) -> None:
    theme_path = Path(__file__).with_name("theme.qss")
    app.setStyleSheet(theme_path.read_text(encoding="utf-8"))


def load_app_icon() -> QtGui.QIcon:
    app_dir = Path(__file__).parent
    ico_path = app_dir / "logo.ico"
    png_path = app_dir / "logo.png"
    if sys.platform.startswith("win") and ico_path.exists():
        return QtGui.QIcon(str(ico_path))
    if png_path.exists():
        return QtGui.QIcon(str(png_path))
    if ico_path.exists():
        return QtGui.QIcon(str(ico_path))
    return QtGui.QIcon()


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("ZiMO")
    app.setOrganizationName("ZiMO")
    app_icon = load_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    load_theme(app)

    window = ZiMOShell()
    if not app_icon.isNull():
        window.setWindowIcon(app_icon)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
