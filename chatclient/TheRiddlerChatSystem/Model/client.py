"""
The Riddler Chat System

Author: 1337_TECH DBA. Austin Texas
DATE: 03/04/2022
Client.py for Riddler Chat System
"""
import argparse
import re
import socket
from _thread import start_new_thread
import random
from copy import copy
from threading import Lock
from typing import ByteString
import colorama as color
from queue import Queue

from PyQt5 import pyqtSlot

from chatclient.TheRiddlerChatSystem.Model.qt_elements.Clickable import MessageRecievedMixIn


class CommandParserAndBuilder:
    """
    CommandParserAndBuilder initializes dictionaries that make it convenient to parse and build messages for Lab2 of
    Communication and Networks: Tech/Arch/Protocol
    """

    def __init__(self):
        # format will be tuple of command and keyword arguments
        self.commands_send = {
            b'HELO': (b'HELO', ['screen_name', 'ip', 'port']),
            b'MESG': (b'MESG ', ['screen_name', 'message']),
            b'EXIT': b'EXIT\n',
        }

        self.commands_recv = {
            b'JOIN': (b'JOIN ', ['screen_name', 'ip', 'port']),
            b'MESG': (b'MESG ', ['screen_name', 'message']),
            b'EXIT': (b'EXIT ', ['screen_name']),
            b'ACPT': (b'ACPT ', ['screen_name', 'ip', 'port']),
            b'RJCT': (b'RJCT', ['screen_name']),
        }

        self.parser_mux_recv = {
            b'JOIN': self.join_handle_recv,
            b'MESG': self.mesg_handle_recv,
            b'EXIT': self.exit_handle_recv,
            b'ACPT': self.acpt_handle_recv,
        }

        self.parser_mux_send = {
            b'MESG': self.mesg_send,
            b'EXIT': self.exit_client,
        }

    @staticmethod
    def join_handle_recv(screen_name) -> bool:
        """ receives the RECV command and handles as neccesary"""
        if screen_name:
            result = f"{color.Fore.YELLOW}{screen_name} has entered the room{color.Fore.RESET}"
            print(result)

        return True if screen_name else False

    @staticmethod
    def mesg_handle_recv(**kwargs) -> str:
        """ receives the MESG command and handles as neccesary"""
        message = 'message'
        screen_name = 'screen_name'
        # now go into the builder and build the actual format string
        message_builder = f"{kwargs[screen_name].decode()}: " \
                          + f"{kwargs[message].decode()}"
        return message_builder

    @staticmethod
    def exit_handle_recv(**kwargs) -> str:
        """ receives the EXIT command and handles as neccesary"""
        screen_name = 'screen_name'
        return f'{kwargs[screen_name].decode()} has left the room\n'

    @staticmethod
    def acpt_handle_recv(**kwargs):
        """ receives the ACPT command and handles as neccesary design decesion to implement in the thread"""
        pass

    @staticmethod
    def rejct_handle_recv(**kwargs) -> str:
        """ recieves the REJCT command meaning the screen_name already exists"""
        screen_name = 'screen_name'
        return f'{color.Fore.RED}{kwargs[screen_name]} is already in use please choose another one{color.Fore.RESET}'

    @staticmethod
    def exit_send(**kwargs) -> ByteString:
        return b'EXIT\n'

    @staticmethod
    def mesg_send(**kwargs) -> ByteString:
        screen_name = 'screen_name'
        message = 'message'
        result = F"MESG {kwargs[screen_name]}: {kwargs[message]}\n".encode()
        return result

    @staticmethod
    def exit_client(**kwargs) -> bytes:
        return f'EXIT {kwargs["screen_name"]}\n'.encode()


class WrappedSocketClient(MessageRecievedMixIn):
    """
    WrappedSocket aims to take in only the needed parameters and create a TLS protocol SSL wrapped socket using only
    """
    end_of_command = b'\n'
    commands_send = {
        b'HELO': b'HELO ',
        b'MESG': b'MESG ',
        b'EXIT': b'EXIT\n',
        b'ACPT': b'ACPT '
    }

    commands_recv = {
        b'JOIN': b'JOIN ',
        b'MESG': b'MESG ',
        b'EXIT': b'EXIT ',
        b'ACPT': b'ACPT ',
    }

    buddy_list = {}  # fill in order of {nick_name:(ip, port),}
    buddy_list_lock = Lock()
    parse_and_build = CommandParserAndBuilder()

    def __init__(self, nickname: str, ip: str, server_port: int,
                 buffer: Queue = None, buff_slot: pyqtSlot = None,
                 send_buffer: Queue = None):
        self.nick = nickname
        self.hostname = ip
        self.port = server_port

        self.buff_queue = buffer
        self.send_queue = send_buffer
        try:
            self.registration()
        except Exception as e:
            print(e)
            exit()

        # use Object Oriented Design
        self.socket_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # create our TCP socket used for
        self.socket_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # create our UDP socket
        # initialization

        # Establishment of UDP and TCP
        self.udp_port = random.randint(self.port + 1, 2 ** 16 - 1)
        self.socket_UDP.bind((self.hostname, self.udp_port))
        connection_str = self.commands_send[b'HELO'] + self.nick.encode() + b' ' + self.hostname.encode() \
                         + b' ' + str(self.udp_port).encode() + self.end_of_command
        # print(f"udp port: {self.udp_port}")
        # print(f"{connection_str}")
        self.socket_TCP.connect((self.hostname, self.port))

        # 2
        self.socket_TCP.send(connection_str)
        self.response = ""

        self.client_Thread_Start()
        self.received_message = buff_slot
        try:
            while True:
                pass
        except KeyboardInterrupt:
            try:
                self.socket_TCP.send(b'EXIT\n')
                print(f'{self.nick} "ELVIS" - HAS LEFT THE BUILDING')
                exit()
            except Exception as error:
                print(f"something went wrong while exiting: {error}")

    def registration(self):
        # Sanity Checks before connection to server
        if not self.check_for_correct_ip() and self.hostname != "localhost":
            print("ERROR INCORRECT FORMAT IDENTIFIER IP")
            raise Exception("Cannot move forward as the ip address is not of correct format %2x.%2x.%2x.%2x format")

        if not isinstance(self.port, int):
            print("port is not a integer")
            raise Exception("port is not an integer")

        if self.port > 2 ** 16 or self.port <= 0:
            print("port number is out of range")
            raise Exception("port is out of range")

        if self.nick.find(' ') >= 0:
            print("nickname cannot include ASCII spaces")
            raise Exception("nickname has a space")

    def check_for_correct_ip(self) -> bool:
        regex_compile = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        x = regex_compile.match(self.hostname)
        if x:
            result = True
        else:
            result = False

        return result

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
                    full_command.pop().decode() # discard the cmd we assume it is b'EXIT <screenname>'
                    screen_name = full_command.pop().decode()
                    if self.buddy_list.get(screen_name):
                        # print(f"{color.Fore.RED}{screen_name} has been deleted from the list{color.Fore.RESET}")
                        self.buddy_list.pop(screen_name)
                finally:
                    pass
            else:
                print('full_command is false, i.e. null or None')
        finally:
            self.buddy_list_lock.release()

    def client_Thread_Start(self, clientSocket: socket = None):
        start_new_thread(self.client_Thread_Send, (self.socket_UDP,), )
        start_new_thread(self.client_Thread_Read, (self.socket_UDP,), )
        start_new_thread(self.client_Thread_TCP, (self.socket_TCP,), )

    def client_Thread_Send(self, clientSocket: socket = None):
        while True:
            message = f"{self.send_queue.get(True)}"
            try:
                self.buddy_list_lock.acquire()
                for screen_name, identity in self.buddy_list.items():
                    clientSocket.sendto(self.commands_send[b'MESG'] + self.nick.encode() + b':'
                                        + message.encode() + b'\n', identity)
            except Exception as e:
                print(e)
            finally:
                self.buddy_list_lock.release()

    def client_Thread_TCP(self, clientSocket: socket = None):
        try:
            while True:
                full_command = b''
                # read in a message from the Read Thread
                while full_command.find(b'\n') == -1:
                    full_command += clientSocket.recv(1048)

                # parse that message

                full_command = full_command.replace(b'\n', b' ')
                full_command = (re.sub(b':', b' ', full_command)).split(b' ')
                # full_command.reverse()
                # a part of parsing make sure it's a valid command before we parse
                if full_command[0] == b'EXIT':
                    continue
                handle = self.parse_and_build.parser_mux_recv[full_command[0]]

                if handle:
                    keyword_args = self.parse_and_build.commands_recv[full_command[0]][1]
                    arguments = {}
                    full_command.reverse()
                    cmd = full_command.pop()
                    full_command = full_command[1:]
                    while len(full_command) > 1:
                        if cmd != b'ACPT':
                            for key in keyword_args:
                                arguments[key] = full_command.pop()
                        else:
                            kwar = {}
                            while len(full_command) > 0:
                                screen_name = full_command.pop().decode()
                                ip = full_command.pop().decode()
                                port = int(str(full_command.pop().decode()))
                                kwar[screen_name] = (ip, port)
                            if len(kwar.items()) > 0:
                                self.update_buddy_list(None, **kwar)


        except KeyboardInterrupt as e:
            clientSocket.send(b'EXIT\n')
            print(f'{self.nick} "ELVIS" - HAS LEFT THE BUILDING')

    def client_Thread_Read(self, clientSocket: socket = None):
        try:
            while True:
                full_command = b''
                # read in a message from the Read Thread
                while full_command.find(b'\n') == -1:
                    full_command += clientSocket.recvfrom(1048)[0]

                # parse that message
                if self.commands_recv[b'MESG'][0] in full_command:
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

                elif self.commands_recv[b'ACPT'] in full_command:
                    full_command = re.sub(b'\n', b'', full_command)
                    full_command.replace(b'ACPT ', b'')

                    parse_full_command = full_command.split(b':')
                    if len(parse_full_command) == 1:
                        parse_full_command = full_command.split(b' ')
                    self.update_buddy_list(parse_full_command)
                    continue

                elif self.commands_recv[b'JOIN'] in full_command:
                    full_command.replace(b'JOIN ', b'')
                    full_command.replace(b'\n', b'')

                    pop_full_command = full_command.split(b' ')
                    self.update_buddy_list(pop_full_command)
                    continue
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
                    clientSocket.sendto(exit_msg, identity)
            except Exception as e:
                print(e)
            finally:
                self.buddy_list_lock.release()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('nickname', metavar='nickname', type=str,
                        help='Chatter Arguments are in form client.py <nickname> <ip> <server_port>')
    parser.add_argument('ip', metavar='ip', type=str)
    parser.add_argument('server_port', metavar='server_port', type=int)
    args = parser.parse_args()

    if isinstance(args.nickname, str) and isinstance(args.ip, str) and isinstance(args.server_port, int):
        client = WrappedSocketClient(args.nickname, args.ip, args.server_port)
    else:
        print("Your arguments are off")
        exit()
