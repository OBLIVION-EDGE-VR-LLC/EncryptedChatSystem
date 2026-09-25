"""
DBA 1337_TECH, AUSTIN TEXAS © July 2021
Proof of Concept code, No liabilities or warranties expressed or implied.
"""

from PyQt5 import pyqtSignal
from PyQt5 import QLineEdit


class SecretTextBox(QLineEdit):
    clicked = pyqtSignal()

    def __init__(self, parent=None, **kwargs):
        super(SecretTextBox, self).__init__(parent, **kwargs)
        s = self.size()
        print(self.size())
        print(parent.size())
        print(self.geometry())
        self.setGeometry(parent.width() / 2 - s.width() / 2,
                         parent.height() / 2 - s.height() / 2,
                         s.width(),
                         s.height()
                         )

    def mousePressEvent(self, ev):
        self.clicked.emit()
