import sys

from PyQt5 import pyqtSignal
from PyQt5 import QMouseEvent
from PyQt5 import QListWidget

from chatclient.TheRiddlerChatSystem.Model.qt_elements.Clickable import ClickMixIn

sys.path.insert(0, '../../Controllers')
sys.path.insert(1, '..')
sys.path.insert(2, '../../Views')


class RecvChatBox(ClickMixIn, QListWidget):
    """
    RecvChatBox is an extension of QTextEdit to allow it to accept the click event
    """
    clickable = pyqtSignal()

    def __init__(self, view):
        super(RecvChatBox, self).__init__(view)

    def mousePressEvent(self, mouse_event: QMouseEvent):
        self.clickable.emit()
