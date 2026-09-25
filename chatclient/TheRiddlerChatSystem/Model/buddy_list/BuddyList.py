from threading import Lock
from chatclient.TheRiddlerChatSystem.Model.buddy_list.CommandParser import CommandParserAndBuilder
import colorama as color


class BuddyList:
    """
    Bringing it back AIM style with the buddy_list class name
    """
    def __init__(self):
        self.buddy_list = {}  # fil in order of {nick_name: (ip, port),}
        self.buddy_list_lock = Lock()
        self.parse_and_build = CommandParserAndBuilder()

    def update_buddy_list(self, full_command, **kwargs):
        self.buddy_list_lock.acquire()
        if full_command:
            try:
                port = int(full_command.pop().decode().replace("\n", ""))
                ip = full_command.pop().decode()
                screen_name = full_command.pop().decode()
                if not self.buddy_list.get(screen_name):
                    self.parse_and_build.join_handle_recv(screen_name)
                    self.buddy_list[screen_name] = (ip, port)
            finally:
                self.buddy_list_lock.release()
        else:
            try:
                for screen_name, identity in kwargs.items():
                    if not self.buddy_list.get(screen_name):
                        self.parse_and_build.join_handle_recv(screen_name)
                        self.buddy_list[screen_name] = identity
            finally:
                self.buddy_list_lock.release()

    def delete_buddy_from_list(self, full_command):
        try:
            self.buddy_list_lock.acquire()
            if full_command:
                try:
                    full_command.pop().decode()  # discard the cmd we assume it is b'EXIT <screenname>'
                    screen_name = full_command.pop().decode()
                    if self.buddy_list.get(screen_name):
                        print(f"{color.Fore.RED}{screen_name} has been deleted from the list{color.Fore.RESET}")
                        self.buddy_list.pop(screen_name)
                finally:
                    pass
            else:
                print('full_command is false, i.e. null or None')
        finally:
            self.buddy_list_lock.release()
