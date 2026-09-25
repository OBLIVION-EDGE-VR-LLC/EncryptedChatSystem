"""
DBA 1337_TECH, AUSTIN TEXAS © July 2021
Proof of Concept code, No liabilities or warranties expressed or implied.
"""

from chatclient.TheRiddlerChatSystem.Model.tools.crypto import cryptoutils
from chatclient.TheRiddlerChatSystem.Model.tools.crypto.zka.ZeroKnowledgeAuth import ZeroKnowledgeAuthServer, modexp, ZeroKnowledgeAuthClient

from chatclient.TheRiddlerChatSystem.Controllers import BaseController
from chatclient.TheRiddlerChatSystem.Views import BaseView


class AuthController(BaseController.BaseController):

    def __init__(self, view: BaseView = None):
        super(AuthController, self).__init__(view)
        self.view = view
        self.result = False

    def getUserName(self) -> str:
        self.username = self.view.usernameBox.text()
        return self.username

    def getPassword(self):
        self.password = self.view.passwordBox.text()

    def Authenticate(self):
        logo = '''\t\t ____________ _________________  ___________           .__
        /_   \_____  \\_____  \______  \ \__    ___/___   ____ |  |__
         |   | _(__  <  _(__  <   /    /   |    |_/ __ \_/ ___\|  |  \\
         |   |/       \/       \ /    /    |    |\  ___/\  \___|   Y  \\
         |___/______  /______  //____/     |____| \___  >\___  >___|  /
                    \/       \/                       \/     \/     \/ '''
        print(logo)
        print("\n\n")
        print("Beginning Registration")
        self.result = False
        gknot = 3

        p = 4074071952668972172536891376818756322102936787331872501272280898708762599526673412366794779

        # print(pow(gknot, 256))
        self.getUserName()
        self.getPassword()
        server = ZeroKnowledgeAuthServer()
        crypt = cryptoutils.CryptoTools()
        username = self.username
        x = crypt.Sha256(str(self.password).encode())
        Y = modexp(gknot, int.from_bytes(x, byteorder='little'), p)
        # server.registration(username, Y)
        a = server.SendSession()
        print('a: ' + str(a))
        client = ZeroKnowledgeAuthClient(username, crypt.Sha256(str(self.password).encode()),
                                         a)
        # didweAuth = server.Authenticate(username, client.c, client.zx)

        if server.Authenticate(username, client.c, client.zx):
            print("Did we Authenticate: " + "True")
            self.result = True

        print(f"Did we Authenticate: {self.result}")

        return self.result

        '''
        testpassword: thisIsNotThePasswordYouAreLookingFor
        '''
