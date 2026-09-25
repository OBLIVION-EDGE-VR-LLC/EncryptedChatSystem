"""
DBA 1337_TECH, AUSTIN TEXAS © July 2021
Proof of Concept code, No liabilities or warranties expressed or implied.
"""

import sys
from typing import Any

sys.path.insert(0, '../../../../Controllers')
sys.path.insert(1, '../../..')
sys.path.insert(2, '../../../../Views')
from chatclient.TheRiddlerChatSystem.Model.tools.crypto.cryptoutils import CryptoTools
import secrets
import json
from chatclient.TheRiddlerChatSystem.Model import Constants

from ExpMath import *

p = 4074071952668972172536891376818756322102936787331872501272280898708762599526673412366794779
gknot = 3

me = ['ZeroAuthServer']


def del_users_RAM(obj: Any):
    del obj


class ZeroAuthServer():

    # Clients sends username and (c,z)
    # the server calculates T=Y^c g^z and verifies that c = H(Y,T',a)
    def __init__(self):
        self.crypt = CryptoTools.CryptoTools()
        self.session = self.GenerateSession()
        self.gknot = 3

    def registration(self, username, Y):
        # get json dictionary called users
        try:
            usersFile = FileInterface.FileInterface(Constants.USERS_FILE)
        except OSError as error:
            print(str(usersFile))
            if 'No such file or directory' in usersFile:
                # create the first user and the infrastructure on the server
                usersFile = open(Constants.USERS_FILE, 'w+')
                usersFile.close()
        try:
            usersFile = FileInterface.FileInterface(Constants.USERS_FILE)
        except OSError as error:
            if 'No such file or directory' in str(error):
                print("SOMETHING MESSED UP AND NO USER FILES, ERROR")
                return
        try:
            jsonUsers = usersFile.ReadFile()
            print("USERS" + str(jsonUsers))
            if 'No such file or directory' in str(jsonUsers):
                # create the first user and the infrastructure on the server
                print('ABOUT TO WRITE TO a FILE \n\n\n')
                usersFile = open(Constants.USERS_FILE, 'w+')
                usersFile.close()
        except OSError as err:
            print('[ZeroKnowledgeServer] ERROR' + str(err))
        usersFile = FileInterface.FileInterface(Constants.USERS_FILE)
        jsonUsers = usersFile.ReadFile()
        if username == None or username == '':
            print('FAILING> USER CANNOT BE NONE OR NULL')
            return False
        if username in jsonUsers:
            print('FAILING> USER ALREADY EXISTS')
            return False
        if not (username in jsonUsers):
            if (jsonUsers != ''):
                jsonimage = json.loads(jsonUsers)
                # 1)store Y
            else:
                jsonimage = {}
            jsonimage[username] = Y
            usersFile.CloseFile()
            fd = FileInterface.FileInterface(Constants.USERS_FILE)
            fd.WriteFile(json.JSONEncoder(ensure_ascii=False).encode(jsonimage))

        # 2)Create folder and allocate storage for Y
        # 3)return back successful or not
        return True

    def GenerateSession(self):
        self.session = secrets.randbelow(p)
        return self.session

    def SendSession(self):
        if self.session == 0 or self.session == None:
            return False
        else:
            return self.session

    def Authenticate(self, username, c, z):
        self.a = self.session
        self.c = c
        self.z = z
        self.u = username
        self.Y = self.LookupPublicKey(self.u)
        t1 = natural_modexp((natural_modexp(self.Y, self.c, p) * natural_modexp(gknot, self.z, p)), 1, p)
        digest = int.from_bytes(self.crypt.Sha256(str(self.Y).encode() + str(t1).encode() + str(self.a).encode()),
                                byteorder='little')

        if c == digest:
            return True
        else:
            print(c)
            print('digest: ' + str(digest))
            return False

    def LookupPublicKey(self, u):
        # TODO:Implement this
        usersFile = FileInterface.FileInterface(Constants.USERS_FILE)
        jsonUsers = usersFile.ReadFile()
        jsonimage = json.loads(jsonUsers)
        y = None
        try:
            y = jsonimage[u]
            del_users_RAM(jsonUsers)
            del_users_RAM(jsonimage)
        except KeyError:
            print(f"There is no user {str(u)}")
            del_users_RAM(jsonUsers)
            del_users_RAM(jsonimage)

        usersFile.CloseFile()
        return y
