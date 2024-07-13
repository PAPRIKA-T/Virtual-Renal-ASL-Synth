"""
Used for pix2pix
@Author: Guts
"""

import sys
from PyQt6.QtWidgets import QApplication
from GUI.MainWindow import MainWindow


class QSSLoader:
    def __init__(self):
        pass

    @staticmethod
    def read_qss_file(qss_file_name):
        with open(qss_file_name, 'r',  encoding='UTF-8') as file:
            return file.read()


def main():
    app = QApplication(sys.argv)
    # init window
    w = MainWindow()
    w.resize(1100, 750)
    # set style
    style_file = './Resource/DefaultStyle.qss'
    style_sheet = QSSLoader.read_qss_file(style_file)
    w.setStyleSheet(style_sheet)
    # show the window
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
