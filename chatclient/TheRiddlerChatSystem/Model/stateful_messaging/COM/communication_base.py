"""
DBA 1337_TECH, AUSTIN TEXAS © July 2021
Proof of Concept Proprietary code, No liabilities or warranties expressed or implied.
All Rights Reserved by 1337_TECH, DBA held in AUSTIN TEXAS
"""
import re
from abc import ABC, abstractmethod
from copy import copy
from queue import Queue
from socket import socket
from typing import List, ByteString
from chatclient.TheRiddlerChatSystem.Model.buddy_list.BuddyList import BuddyList
from chatclient.TheRiddlerChatSystem.Model.Constants import BuddyList
from chatclient.TheRiddlerChatSystem.Model.buddy_list.CommandParser import CommandParserAndBuilder


class CommunicationBase(ABC):

    def __init__(self, send_queue: Queue, recv_queue: Queue):
        self.identity = None
        self.parse_and_build: CommandParserAndBuilder = CommandParserAndBuilder()
        self.send_queue = None
        self.recv_queue = None
        self._init(send_queue, recv_queue)
        self.buddy_list_obj: BuddyList = BuddyList

    def _init(self, send_queue, recv_queue):
        self._init_recv_queue(recv_queue)
        self._init_send_queue(send_queue)

    def _init_recv_queue(self, recv_queue: Queue) -> bool:
        try:
            self.recv_queue: Queue = recv_queue
            return True
        except TypeError as e:
            return False

    def _init_send_queue(self, send_queue: Queue) -> bool:
        try:
            self.send_queue: Queue = send_queue
            return True
        except TypeError as e:
            return False

    @abstractmethod
    def send(self, message: bytes) -> int:
        raise NotImplemented("Please override the base send method")

    @abstractmethod
    def recv(self, buffer: List[bytes]) -> List[bytes]:
        raise NotImplemented("Please override the base recv method")

    @abstractmethod
    def handle_cmd(self, buffer: bytes):
        raise NotImplemented("Please override the base handle_cmd method")

    def client_udp_send(self, client_socket: socket = None):
        message = f"{self.send_queue.get(True)}"
        try:
            self.buddy_list_obj.buddy_list_lock.acquire()
            for screen_name, identity in self.buddy_list_obj.buddy_list.items():
                client_socket.sendto(self.parse_and_build.commands_send[b'MESG'] + nick_name.encode() + b':'
                                     + message.encode() + b'\n', identity)
        except Exception as e:
            print(e)
        finally:
            self.buddy_list_obj.buddy_list_lock.release()

    def client_Thread_Read(self, client_socket: socket = None):
        try:
            full_command = b''
            # read in a message from the Read Thread
            while full_command.find(b'\n') == -1:
                full_command += client_socket.recvfrom(1048)[0]

            # parse that message
            if self.parse_and_build.commands_recv[b'MESG'][0] in full_command:
                full_command = (re.sub(b':', b' ', full_command)).replace(b'\n', b'').split(b' ')
                full_command.reverse()
                # a part of parsing make sure it's a valid command before we parse
                command = full_command.pop()
                screen_name = full_command.pop()
                handle = self.parse_and_build.parser_mux_recv[command]
                full_command.reverse()
                result = []
                result.append(b' '.join(full_command))
                result.append(screen_name)
                result.append(command)
                full_command = result

            elif self.parse_and_build.commands_recv[b'ACPT'] in full_command:
                full_command = re.sub(b'\n', b'', full_command)
                full_command.replace(b'ACPT ', b'')

                parse_full_command = full_command.split(b':')
                if len(parse_full_command) == 1:
                    parse_full_command = full_command.split(b' ')
                self.buddy_list_obj.update_buddy_list(parse_full_command)


            elif self.parse_and_build.commands_recv[b'JOIN'] in full_command:
                full_command.replace(b'JOIN ', b'')
                full_command.replace(b'\n', b'')

                pop_full_command = full_command.split(b' ')
                self.parse_and_build.update_buddy_list(pop_full_command)

            else:
                full_command = (re.sub(b'\n', b'', full_command)).split(b' ')
                full_command.reverse()

                # a part of parsing make sure it's a valid command before we parse
                handle = self.parse_and_build.parser_mux_recv[full_command[-1]]

            if handle:
                keyword_args = self.parse_and_build.commands_recv[full_command[-1]][1]
                arguments = {}
                cpy_command = full_command.copy()
                cmd = full_command.pop()
                while len(full_command) >= 1:
                    if cmd != b'ACPT':
                        for key in keyword_args:
                            arguments[key] = full_command.pop()
                        arguments['full_message'] = cpy_command
                    else:
                        kwar = {}
                        while len(full_command) > 0:
                            screen_name = full_command.pop().decode()
                            ip = full_command.pop().decode()
                            port = int(full_command.pop().decode())
                            kwar[screen_name] = (ip, port)

                        if len(kwar.items()) > 0:
                            self.update_buddy_list(None, **kwar)

                self.response = ""

                if cmd != b'ACPT' and cmd:
                    self.response = handle(**arguments)

                if self.response:
                    if handle == self.parse_and_build.parser_mux_recv[b'EXIT']:
                        # special case to remove a buddy from the list
                        self.delete_buddy_from_list(arguments['full_message'])

                    print(self.response)
                    cpy = copy(self.response)
                    self.buff_queue.put_nowait(cpy)
                    self.received_message.emit(cpy)

        except KeyboardInterrupt as e:
            do_something = {"screen_name": self.nick}
            exit_msg = self.parse_and_build.exit_client(**do_something)
            try:
                self.buddy_list_lock.acquire()
                for screen_name, identity in self.buddy_list.items():
                    client_socket.sendto(exit_msg, identity)
            except Exception as e:
                print(e)
            finally:
                self.buddy_list_lock.release()
