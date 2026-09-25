from chatclient.TheRiddlerChatSystem.Controllers import BaseController
from chatclient.TheRiddlerChatSystem.Model.qt_elements.VillainList import VillainList

me = '[VillainController]'


class VillainController(BaseController.BaseController):

    def __init__(self, view, component):
        super(VillainController, self).__init__(view)
        self.villains: VillainList = component
        self.villains.clickable.connect(self.receive_and_print)
        self.view = view
        self.clicks = 0

    def receive_and_print(self):
        print(me + "clicked the List Box from VillainController")
