from PyQt5 import QApplication
import sys
from chatclient.TheRiddlerChatSystem.Views.MainWindow import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())