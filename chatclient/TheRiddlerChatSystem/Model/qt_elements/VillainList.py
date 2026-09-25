from PyQt5 import pyqtSignal
from PyQt5 import QMouseEvent
from PyQt5 import QListWidget


class VillainList(QListWidget):
    """
    VillainList identical to a buddy list
    """
    clickable = pyqtSignal()

    def __init__(self, view):
        super(VillainList, self).__init__(view)

    def mousePressEvent(self, mouse_event: QMouseEvent):
        self.clickable.emit()
