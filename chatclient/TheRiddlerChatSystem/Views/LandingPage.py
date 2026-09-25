'''
Although it is titled the Landing page it is being treated more like the initial
GameBoard.  Luckily this is just a view so it is subject to change, I can always
make a view called GameBoard which inherits the BaseView
'''

from PyQt5 import Qt
# from StenographyController import StenographyController
from PyQt5 import QFont
from PyQt5 import QFrame, QSplitter, QLabel, QHBoxLayout, QDockWidget, QPushButton

from chatclient.TheRiddlerChatSystem.Controllers.MessageController import MessageController
from chatclient.TheRiddlerChatSystem.Controllers.VillainController import VillainController
from chatclient.TheRiddlerChatSystem.Model.qt_elements.CustomLabel import *
from chatclient.TheRiddlerChatSystem.Controllers.ReceiveController import ReceiveController
from chatclient.TheRiddlerChatSystem.Model.qt_elements.MsgChatBox import MsgChatBox
from chatclient.TheRiddlerChatSystem.Model.qt_elements.RecvChatBox import RecvChatBox
from chatclient.TheRiddlerChatSystem.Model.qt_elements.VillainList import VillainList
from chatclient.TheRiddlerChatSystem.Views import BaseView

sys.path.insert(0, '../Controllers')
sys.path.insert(1, '../Model')
sys.path.insert(2, '../Views')

me = '[LandingPage]'

green = '#669933'
purple = '#CC663399'
darkRed = '#8B0000'
background_role = 'background-color: '
text_role = 'color: '


class LandingPage(BaseView.BaseView):

    def __init__(self):
        super(LandingPage, self).__init__()
        self.ctrl = None
        self.components = []
        self.controllers = []
        self.p = None
        self.p2 = None

        self.initUI()

    def initUI(self):
        """Initializes the UI Landing Page"""
        receive_chat_box = RecvChatBox(self)
        message_chat_box = MsgChatBox("TheRiddlerChatSystem Message Here", self)
        password_protect_button = QPushButton("Click to Password Protect", self)
        villain_list = VillainList(self)
        go_baby_go = QPushButton("SEND", self)

        # format the buttons to look differently
        password_protect_button.setStyleSheet(background_role + purple + '; ' + text_role + green + ';')
        villain_list.setStyleSheet(background_role + purple + '; ' + text_role + green + ';')
        message_chat_box.setStyleSheet(background_role + green + '; ' + text_role + purple + ';')
        receive_chat_box.setStyleSheet(background_role + purple + '; ' + text_role + green + ';')
        go_baby_go.setStyleSheet(background_role + green + '; ' + text_role + purple + ';')

        fileItems = QDockWidget("Chat Messages", self)
        BuddyList = QDockWidget("Fellow Users", self)
        fileItems.setFeatures(QDockWidget.NoDockWidgetFeatures)
        folderItems = QDockWidget("Type a Message to be sent", self)
        viewOne = QPixmap(os.getcwd() + '/images/Transparent_Logo_Blog_Orange_green.png')
        viewOne = viewOne.scaled(150, 150)

        # Adjust the Font
        options_font = QFont('Courier', 14, QFont.ExtraBold)

        receive_chat_box.setFont(options_font)
        message_chat_box.setFont(options_font)

        password_protect_button.setFont(options_font)

        go_baby_go.setFont(options_font)

        self.p2 = viewOne

        self.setWindowTitle('TheRiddlerChatSystem')

        fileItems.setWidget(receive_chat_box)
        fileItems.setFloating(False)

        folderItems.setWidget(message_chat_box)
        folderItems.setFloating(False)

        hbox = QHBoxLayout(self)

        splitter1 = QSplitter(self)
        splitter1.setOrientation(Qt.Horizontal)
        sizePolicyOne = splitter1.sizePolicy()
        sizePolicyOne.setHorizontalStretch(1)

        logo = QLabel()
        logo.setPixmap(self.p2)
        logo.resize(50, 50)

        top_left = QFrame(splitter1)
        top_left.setFrameShape(QFrame.StyledPanel)

        splitter2 = QSplitter(splitter1)
        sizePolicy = splitter2.sizePolicy()
        sizePolicy.setHorizontalStretch(1)

        splitter1.setOrientation(Qt.Vertical)
        splitter1.addWidget(BuddyList)
        splitter1.addWidget(villain_list)
        splitter1.addWidget(logo)

        splitter2.setSizePolicy(sizePolicy)
        splitter2.setOrientation(Qt.Vertical)

        top_right = QFrame(splitter2)
        top_right.setFrameShape(QFrame.StyledPanel)
        splitter2.addWidget(fileItems)

        bottom_right = QFrame(splitter2)
        bottom_right.setFrameShape(QFrame.StyledPanel)
        splitter2.addWidget(folderItems)
        splitter2.addWidget(password_protect_button)
        splitter2.addWidget(go_baby_go)

        hbox.addWidget(splitter1)
        hbox.addWidget(splitter2)
        self.setGeometry(0, 0, 250, 405)
        self.resize(405, 250)

        self.setAutoFillBackground(False)

        self.setStyleSheet(background_role + darkRed + ';')

        ####
        #
        # Register The Controllers to link The Functionality Together
        #
        ####
        recv = ReceiveController(self, receive_chat_box)
        mesg_send = MessageController(self, message_chat_box, go_baby_go)
        villains = VillainController(self, villain_list)
        self.controllers.append(recv)
        self.controllers.append(mesg_send)
        self.controllers.append(villains)

        self.app = None

        self.show()
