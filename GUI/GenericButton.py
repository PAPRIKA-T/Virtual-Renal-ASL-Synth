from PyQt6.QtWidgets import QPushButton


class GenericButton(QPushButton):
    def __init__(self, parent):
        super(GenericButton, self).__init__(parent)
        self.__init_self()

    def __init_self(self):
        self.setFixedSize(50, 50)
        # self.setFixedHeight(50)
