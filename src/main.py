import sys
from pathlib import Path

from PySide6 import QtWidgets, QtCore

from .settings import load_settings
from .ui.pet_window import PetWindow
from .ui.tray import TrayController


def main() -> int:
    base_dir = Path(__file__).resolve().parent.parent
    settings = load_settings(base_dir)

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    pet = PetWindow(settings)
    pet.show()

    tray = TrayController(settings=settings, pet_window=pet)
    tray.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
