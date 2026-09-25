"""
DBA 1337_TECH, AUSTIN TEXAS © July 2021
Proof of Concept code, No liabilities or warranties expressed or implied.
"""
from chatclient.TheRiddlerChatSystem.Controllers.AuthAndSwitchController import AuthAndSwitchController
from chatclient.TheRiddlerChatSystem.Controllers.ViewSwitcher import ViewSwitcher
from chatclient.TheRiddlerChatSystem.Views.LandingPage import LandingPage

# from chatclient.TheRiddlerChatSystem.Views.MainWindow import MainWindow

'''
Although it is titled the Landing page it is being treated more like the initial
Setup.  Luckily this is just a view so it is subject to change, the Developer can
always make a view called GameBoard (as an example) which inherits the BaseView
'''

from PyQt5 import Qt

from chatclient.TheRiddlerChatSystem.Model.qt_elements.TextBoxes import SecretTextBox

from chatclient.TheRiddlerChatSystem.Model.qt_elements.CustomLabel import *


class AuthenticateView(BaseView):

    def __init__(self, window=None):
        super(AuthenticateView, self).__init__()
        self.ctrl = None
        self.components = []
        self.p = None
        self.p2 = None
        self.mw = window
        self.controller = None

        self.initUI()

    def initUI(self):
        self.p = QPixmap(os.getcwd() + '/images/1337_Tech_Skull.png')

        hbox = QHBoxLayout(self)

        self.main_label = LoadingLabel(alignment=Qt.AlignCenter)
        self.main_label.setPixmap(self.p)
        self.main_label.setAttribute(Qt.WA_TranslucentBackground, True)

        self.passwordBox = SecretTextBox(self.main_label, text='password')
        self.usernameBox = SecretTextBox(self.main_label, text='username')
        self.usernameBox.move(self.main_label.size().width() // 5 - 25, self.main_label.size().height() // 5 - 50)
        self.usernameBox.setStyleSheet('background-color: rgb(0,249,243); border-radius: 2;')

        self.passwordBox.setEchoMode(QLineEdit.Password)
        self.passwordBox.setStyleSheet('background-color: rgb(0,249,243); border-radius: 2;')
        print(self.main_label.size().width()//5)
        self.passwordBox.move(self.main_label.size().width() // 5 - 25, self.main_label.size().height() // 5 + 100)

        self.usernameBox.setFont(QFont("Helvetica", 14, QFont.ExtraBold))

        hbox.addWidget(self.main_label)


        # self.viewswitch_controller: ViewSwitcher = ViewSwitcher(self, LandingPage)
        self.controller: AuthAndSwitchController = AuthAndSwitchController(self, LandingPage, ViewSwitcher)

        # self.passwordBox.clicked.connect(self.controller.auth_controller.Authenticate)

