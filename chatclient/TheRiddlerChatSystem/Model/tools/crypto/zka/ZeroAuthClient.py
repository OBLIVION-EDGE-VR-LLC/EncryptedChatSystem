"""
DBA 1337_TECH, AUSTIN TEXAS © July 2021
Proof of Concept code, No liabilities or warranties expressed or implied.
"""

import sys
sys.path.insert(0, '../../../../Controllers')
sys.path.insert(1, '../../..')
sys.path.insert(2, '../../../../Views')
import secrets

sys.path.insert(0, '../../../../Controllers')
sys.path.insert(1, '../../..')
sys.path.insert(2, '../../../../Views')
from ExpMath import *
gknot = 3
p = 4074071952668972172536891376818756322102936787331872501272280898708762599526673412366794779

me = '[ZeroAuthClient]'
class ZeroAuthClient():

    def __init__(self, username, x, randomToken):
        G = "4074071952668972172536891376818756322102936787331872501272280898708762599526673412366794779"
        self.gknot = 3
        self.crypt = CryptoTools.CryptoTools()
        self.x = x #sha256(pwd)
        self.Y = modexp(gknot, int.from_bytes(self.x, byteorder='little'), p)
        self.r = int(secrets.choice(G))
        self.T1 = modexp(gknot, self.r, p)
        self.a = randomToken
        self.c = self.CalculateC()
        self.zx = self.r - (self.c*(int.from_bytes(self.x, 'little')))


    def init():
        #TODO: Nothing is to be done here since Registration and Proving is done
        #On second thought this will be used to gain the random token or at least
        #sending a packet of info to request the random key
        return

    def CalculateC(self):
        self.c = int.from_bytes(self.crypt.Sha256(str(self.Y).encode() + str(self.T1).encode() + str(self.a).encode()), byteorder='little')
        return self.c

    def SendZeroKnowledgeAuth(self):
        #TODO: send self.c, self.zx
        return self.c, self.zx

    def IsItAuthenticated(self,Data):
        #TODO: Find the incoming packet and determine if True or False was sent
        return
