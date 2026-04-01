import sys
from pathlib import Path

from PySide6 import QtWidgets

from .settings import load_settings
from .logic.proactive import ProactiveTalker
from .ui.bubble import BubbleWindow
from .ui.pet_window import PetWindow
from .ui.tray import TrayController


def main() -> int:
    base_dir = Path(__file__).resolve().parent.parent
    settings = load_settings(base_dir)

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    pet = PetWindow(settings)
    pet.show()

    bubble = BubbleWindow()

    # Active app getter (Windows-only; safe fallback)
    if sys.platform == "win32":
        from .logic.observer_windows import WindowsActiveAppObserver

        observer = WindowsActiveAppObserver()
        active_app_getter = observer.get_active_app
    else:
        active_app_getter = lambda: None

    talker = ProactiveTalker(settings=settings, active_app_getter=active_app_getter)
    talker.say.connect(lambda text: bubble.show_text_near(text, pet))
    # talker.debug.connect(print)  # uncomment for debug
    talker.start()

    tray = TrayController(settings=settings, pet_window=pet, proactive_talker=talker)
    tray.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
