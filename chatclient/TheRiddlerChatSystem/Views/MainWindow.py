import os
import sys

from PyQt5 import Qt, QPoint
from PyQt5 import QIcon, QPainter, QPen
from PyQt5 import QApplication, QMainWindow, QStyle, QGraphicsOpacityEffect, QDesktopWidget

from chatclient.TheRiddlerChatSystem.Views import LoadingPage

me = '[MainWindow]'


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ctrl = None
        self.components = []
        self.view = None

        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        edit_menu = menubar.addMenu('Edit')
        help_menu = menubar.addMenu('Help')

        # icons
        open_icon = self.style().standardIcon(QStyle.SP_DirOpenIcon)
        save_icon = self.style().standardIcon(QStyle.SP_DriveHDIcon)
        undo_icon = self.style().standardIcon(QStyle.SP_ArrowBack)
        redo_icon = self.style().standardIcon(QStyle.SP_ArrowForward)

        self.about_menu = help_menu.addAction('&About')

        self.undo_menu = edit_menu.addAction('&undo')
        self.undo_menu.setIcon(undo_icon)
        self.redo_menu = edit_menu.addAction('&redo')
        self.redo_menu.setIcon(redo_icon)

        self.open_action = file_menu.addAction('&Open')
        self.open_action.setIcon(open_icon)
        self.save_action = file_menu.addAction('&Save')
        self.save_action.setIcon(save_icon)

        self.initUI()

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.center()
        #setup movement for frameless container
        self.oldPos = self.pos()
        self.show()


    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def paintEvent(self, event=None):
        painter = QPainter(self)

        painter.setOpacity(0.01)
        painter.setBrush(Qt.white)
        painter.setPen(QPen(Qt.white))
        painter.drawRect(self.childrenRect())

    def initUI(self) -> object:
        # self.view = LandingPage.LandingPage()
        self.view = LoadingPage.LoadingPage(window=self)

        self.statusBar().showMessage('StatusBar: Initialized')

        self.setCentralWidget(self.view)

        # self.setGeometry(300, 300, 796, 650)

        self.setWindowTitle('The Riddler Chat System')

        self.setWindowIcon(QIcon(os.getcwd() + '/images/1337_Logo_small.png'))

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        # self.setWindowOpacity(0.35)

        op = QGraphicsOpacityEffect(self.view)

        self.setWindowOpacity(1.0)

        self.setGraphicsEffect(op)
        self.paintEvent()
        self.statusBar().setStyleSheet("background-color: red;color: white;")
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
