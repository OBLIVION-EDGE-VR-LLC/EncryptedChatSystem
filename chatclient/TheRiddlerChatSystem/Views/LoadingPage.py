"""
DBA 1337_TECH, AUSTIN TEXAS © July 2021
Proof of Concept code, No liabilities or warranties expressed or implied.
"""
from .AuthenticationView import AuthenticateView

'''
Although it is titled the Landing page it is being treated more like the initial
Setup.  Luckily this is just a view so it is subject to change, the Developer can
always make a view called GameBoard (as an example) which inherits the BaseView
'''

from PyQt5 import Qt

from chatclient.TheRiddlerChatSystem.Controllers.ViewSwitcher import ViewSwitcher
from chatclient.TheRiddlerChatSystem.Model.qt_elements.CustomLabel import *
from chatclient.TheRiddlerChatSystem.Model.qt_elements.Overlay import Overlay
from chatclient.TheRiddlerChatSystem.Views.BaseView import BaseView
# from TheRiddlerChatSystem.Views.MainWindow import MainWindow


class LoadingPage(BaseView):

    def __init__(self, window= None):
        super(LoadingPage, self).__init__()
        self.ctrl = None
        self.components = []
        self.p = None
        self.p2 = None
        self.mw = window
        print(window)
        self.initUI()

    def initUI(self):
        self.p = QPixmap(os.getcwd() + '/images/1337_Tech_Skull.png')
        self.p.scaled(900, 900)
        self.logo = QPixmap(os.getcwd() + '/images/1337_Tech_Skull.png')
        self.logo.scaled(1000,1000)

        # self.setGeometry(300, 300, 250, 150)
        # self.setWindowTitle('Password Complexity UI')
        # self.folderitems = QDockWidget("Enter Password", self)
        # self.fileitems = QDockWidget("Password Complexity", self)
        # self.pwdController = PwdComplexController.PwdComplexController(self)
        #
        # self.dockWidget1 = self.pwdController.progressBar
        # self.dockWidget2 = self.pwdController.pwdText
        #
        # self.fileitems.setWidget(self.dockWidget1)
        # self.fileitems.setFloating(False)
        #
        # self.folderitems.setWidget(self.dockWidget2)
        # self.folderitems.setFloating(False)
        #
        hbox = QHBoxLayout(self)
        #
        # splitter1 = QSplitter(self)
        # splitter1.setOrientation(Qt.Horizontal)
        #
        #
        # splitter2 = QSplitter(splitter1)
        # sizePolicy = splitter2.sizePolicy()
        # sizePolicy.setHorizontalStretch(1)
        #
        # splitter2.setSizePolicy(sizePolicy)
        # splitter2.setOrientation(Qt.Vertical)
        #
        # top_right = QFrame(splitter2)
        # top_right.setFrameShape(QFrame.StyledPanel)
        # splitter2.addWidget(self.fileitems)
        # #splitter2.addWidget(logo)
        # bottom_right = QFrame(splitter2)
        # bottom_right.setFrameShape(QFrame.StyledPanel)
        # splitter2.addWidget(self.folderitems)
        # splitter2.setGeometry(0,0,20,700)
        # #hbox.addWidget(splitter1)
        # #hbox.addWidget(top_right)
        # self.setGeometry(250, 250, 405, 405)
        self.m_label = LoadingLabel(alignment=Qt.AlignCenter)
        self.m_label.setPixmap(self.p)
        self.m_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.logo_label = LogoLabel(self.m_label)
        self.logo_label.setPixmap(self.logo)
        self.logo_label.setGeometry(-self.width() / 2 + self.width(),
                                    -self.height() / 2 + self.height() - 25,
                                    self.logo.width(), self.logo.height())
        self.logo_label.setAttribute(Qt.WA_TranslucentBackground, True)

        hbox.addWidget(self.m_label)
        # hbox.addWidget(self.logo_label)

        self.setGeometry(300, 300, 250, 405)
        #
        pallete = QPalette()
        pallete.setColor(QPalette.Background, Qt.gray)
        #  #pallete.setColor(QPalette.Background, Qt.green)
        self.setAutoFillBackground(True)
        self.setPalette(pallete)

        self.overlay = Overlay(self.m_label)
        # self.m_label.clicked.connect(self.overlay.show)
        self.logo_label.clicked.connect(self.overlay.show)

        self.controller = ViewSwitcher(self, AuthenticateView)
        self.m_label.clicked.connect(self.controller.SwitchOnClick)

        # self.show()
