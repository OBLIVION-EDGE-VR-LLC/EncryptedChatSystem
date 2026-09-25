# /usr/env/python3.7

from chatclient.TheRiddlerChatSystem.Controllers import BaseController
from chatclient.TheRiddlerChatSystem.Model.qt_elements.Clickable import clickable

me = '[ButtonController]'


class ButtonController(BaseController.BaseController):

    def __init__(self, view, component):
        super(ButtonController, self).__init__(view)
        self.checkbox = component
        self.checkbox.clicked.connect(self.changeTitle)
        clickable(self.view.label).connect(self.ClickedTheMap)
        self.view = view
        self.clicks = 0

    def changeTitle(self, state):

        if self.checkbox.isChecked():
            self.view.setWindowTitle('QCheckBox')
        else:
            self.view.setWindowTitle(' ')

    def ClickedTheMap(self):
        self.clicks += 1
        print(self.view.label.curiousposition)