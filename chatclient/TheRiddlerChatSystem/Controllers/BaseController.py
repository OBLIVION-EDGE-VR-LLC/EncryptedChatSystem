# /usr/env/python3.7

from chatclient.TheRiddlerChatSystem.Views import BaseView

me = '[BaseController]'


class BaseController(object):

    def __init__(self, view):
        self.components = []

        if isinstance(view, BaseView.BaseView):
            self.view = view
        else:
            self.view = None
            print(me + 'ERROR>We are not a BaseView')

    def ActiveListener(self):
        print('called from the Base controller')
