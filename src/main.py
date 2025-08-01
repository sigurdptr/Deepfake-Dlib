import sys
import logging
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from app import AppWindow


def main(working_dir: Path) -> None:
    try:
        app = QApplication(sys.argv)
        window = AppWindow(working_dir)
        app.exec()
    except Exception as e:
        logging.exception(e)


if __name__ == "__main__":
   working_dir = Path(__file__).resolve().parent.parent
   main(working_dir)