from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from zimo.app.shell import ZimoShell


def load_theme(app: QApplication) -> None:
    theme_path = Path(__file__).with_name("theme.qss")
    app.setStyleSheet(theme_path.read_text(encoding="utf-8"))


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ZiMO")
    load_theme(app)

    window = ZimoShell()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
