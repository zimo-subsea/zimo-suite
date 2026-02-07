import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from zimo.app.shell import ZiMOShell


def load_stylesheet(app: QApplication) -> None:
    theme_path = Path(__file__).with_name("theme.qss")
    app.setStyleSheet(theme_path.read_text(encoding="utf-8"))


def main() -> int:
    app = QApplication(sys.argv)
    load_stylesheet(app)
    shell = ZiMOShell()
    shell.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
