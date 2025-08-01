import sys
import logging

from PyQt6.QtWidgets import QApplication

from app import AppWindow


def main() -> None:
    try:
        app = QApplication(sys.argv)
        window = AppWindow()
        app.exec()
    except Exception as e:
        logging.exception(e)


if __name__ == "__main__":
   main()