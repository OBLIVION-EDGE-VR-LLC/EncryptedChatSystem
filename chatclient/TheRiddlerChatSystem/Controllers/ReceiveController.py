# /usr/env/python3.7
from queue import Queue

from chatclient.TheRiddlerChatSystem.Controllers import BaseController
from chatclient.TheRiddlerChatSystem.Model.qt_elements.RecvChatBox import RecvChatBox
me = '[ReceiveController]'


class ReceiveController(BaseController.BaseController):

    def __init__(self, view, component):
        super(ReceiveController, self).__init__(view)
        self.ChatRecv: RecvChatBox = component
        self.ChatRecv.clickable.connect(self.receive_and_print)
        self.view = view
        self.clicks = 0

    def receive_and_print(self):
        print(me + "clicked the Receive Chat Box from ReceiveController")


