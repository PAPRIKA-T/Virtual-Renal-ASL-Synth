from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene)


class GenericGraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super(GenericGraphicsScene, self).__init__(parent)

