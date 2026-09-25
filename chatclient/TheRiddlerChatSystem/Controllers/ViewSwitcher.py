"""
DBA 1337_TECH, AUSTIN TEXAS © July 2021
Proof of Concept code, No liabilities or warranties expressed or implied.
"""

from chatclient.TheRiddlerChatSystem.Controllers import BaseController
from chatclient.TheRiddlerChatSystem.Model.tools.crypto.cryptoutils import CryptoTools
from chatclient.TheRiddlerChatSystem.Model.tools.crypto.zka.ZeroKnowledgeAuth import ZeroKnowledgeAuthServer, modexp, ZeroKnowledgeAuthClient
from chatclient.TheRiddlerChatSystem.Views import BaseView
from chatclient.TheRiddlerChatSystem.Views import LandingPage


class ViewSwitcher(BaseController.BaseController):

    def __init__(self, view: BaseView = None, view_to_switch: BaseView = None):
        super(ViewSwitcher, self).__init__(view)
        self.view = view
        self.view_to_switch = view_to_switch
        #self.view.m_label.clicked.connect(self.SwitchOnClick)


    def SwitchOnClick(self):
        newView = self.view_to_switch(window=self.view.mw)
        self.view.mw.setCentralWidget(newView)
        self.newview = newView
        self.view.mw.show()
        self.view = newView

        print("MADE IT TO SWITCHONECLICK, END")

    def HandOffToRiddlerChatSystem(self):
        newView = LandingPage.LandingPage()
        self.view.mw.setCentralWidget(newView)
        self.newview = newView
        self.view.mw.statusBar().showMessage("StatusBar: Authenticated -- PlainText Mode")
        self.view.mw.statusBar().setStyleSheet("background-color: yellow;color: black;")
        newView.mw = self.view.mw
        del self.view
        self.view = newView
        self.view.mw.setMinimumSize(550, 405)
        self.view.mw.resize(self.view.mw.minimumSizeHint())

        self.view.mw.show()
        self.view.show()

    def getUserName(self):
        self.username = self.newview.usernameBox.text()

    def getPassword(self):
        self.password = self.newview.passwordBox.text()

    def Authenticate(self):
        logo = ''' ____________ _________________  ___________           .__
        /_   \_____  \\_____  \______  \ \__    ___/___   ____ |  |__
         |   | _(__  <  _(__  <   /    /   |    |_/ __ \_/ ___\|  |  \\
         |   |/       \/       \ /    /    |    |\  ___/\  \___|   Y  \\
         |___/______  /______  //____/     |____| \___  >\___  >___|  /
                    \/       \/                       \/     \/     \/ '''
        print(logo)
        print("\n\n")
        print("Beginning Registration")
        gknot = 3

        p = 4074071952668972172536891376818756322102936787331872501272280898708762599526673412366794779

        #print(pow(gknot, 256))
        self.getUserName()
        self.getPassword()
        server = ZeroKnowledgeAuthServer()
        crypt = CryptoTools.CryptoTools()
        username = self.username
        x = crypt.Sha256(str(self.password).encode())
        Y = modexp(gknot, int.from_bytes(x, byteorder='little'), p)
        server.registration(username, Y)
        a = server.SendSession()
        print('a: ' + str(a))
        client = ZeroKnowledgeAuthClient(username, crypt.Sha256(str(self.password).encode()),
                                         a)
        didweAuth = server.Authenticate(username, client.c, client.zx)
        print("Did we Authenticate: " + str(didweAuth))
        if didweAuth:
            print("TODO: HandOff to TheRiddlerChatSystem!")


        '''
        testpassword: thisIsNotThePasswordYouAreLookingFor
        '''

