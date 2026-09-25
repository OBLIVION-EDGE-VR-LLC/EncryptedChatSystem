# !/usr/bin/python3
"""
Author: Blake De Garza

LabPartner: TBD
UTeid: bd6225
Date: 02-18-2021
Description: Project 2 assignment for the Server Side of the Chat Application, Partner with someone from class

"""
import argparse
import socket
from _thread import start_new_thread
from threading import Lock
import re


class TcpMux:
    @staticmethod
    def helo_recv(**kwargs) -> bytes:
        """
        A Chatter client sends this to enter the chatroom; [TCP]

        :param kwargs:
        :return:
        """
        # do some thinking and make sure that the username isn't already taken
        screen_name = kwargs['screen_name']
        identity = (kwargs['ip'], kwargs['port'])

        if not MembershipServer.MembershipList.get(screen_name.decode()):
            MembershipServer.update_members(MembershipServer.MembershipList, MembershipServer.buddy_list_lock,
                                            kwargs['tcp_identity'], kwargs['full_command'])
        else:
            return TcpMux.rjct_send(screen_name, identity[0])

        if len(MembershipServer.MembershipList.keys()) > 1:
            result = TcpMux.acpt_send()
            return result

        else:
            return f'ACPT {screen_name.decode()} {identity[0].decode()} {identity[1].decode()}\n'.encode()

    @staticmethod
    def exit_send(**kwargs) -> bytes:
        """
        A Chatter client sends this to indicate exit from the chatroom; [TCP]

        :param kwargs:
        :return: bytes of the EXIT\n command
        """
        screen_name = kwargs['screen_name']
        return f"EXIT {screen_name}\n".encode()

    @staticmethod
    def acpt_send() -> bytes:
        """
        The server sends this message in response to the Greeting, to acknowledge the validity of the screen name and to
        inform the Chatter Client of the Identities of the ALL Chatters (including yourself).
        Each identity is separated by a “:”. [TCP]

        :return: bytes of the formatted string to send
        """
        result = f'ACPT '
        if len(MembershipServer.MembershipList.keys()) > 1:
            for k_name, iden in MembershipServer.MembershipList.items():
                result += f'{k_name} {iden[0][0]} {iden[0][1]}:'

            result = result[:-1] + f'\n'
            result = result.encode()

        return result

    @staticmethod
    def rjct_send(screen_name, identity):
        """
        Meaning same as in Iteration 1 [TCP]: The server sends this message in response to the Greeting, to let the Chat
        Client know that the screen_nameisalreadyinuse. [TCP]

        :param kwargs:
        :return:
        """
        return f'RJCT {screen_name.decode()} {identity[0].decode()} {identity[1].decode()}\n'.encode()


class UdpMux:
    @staticmethod
    def join_send(**kwargs):
        """
        Notification sent to ALL Chatter clients over their UDP ports to let them know that a new member has entered the
        chatroom. [UDP]

        :param kwargs:
        :return:
        """
        screen_name = kwargs['screen_name']
        identity = (kwargs['ip'], kwargs['port'])

        result = f'JOIN {screen_name.decode()} {identity[0].decode()} {identity[1].decode()}\n'.encode()

        return result

    @staticmethod
    def exit_send(**kwargs):
        """
        Notification sent to ALL Chatter clients over their UDP ports to let them know that a member has left. [UDP]

        :param kwargs:
        :return:
        """
        screen_name = kwargs['screen_name']
        return f'EXIT {screen_name}\n'.encode()


class MembershipServer:
    udp_switch = UdpMux()  # set up a global UDP Switch Statement
    tcp_switch = TcpMux()  # set up a global TCP Switch Statement

    UDP_SWITCH = {
        b'ACPT': (udp_switch.join_send, ['port', 'ip', 'screen_name']),
        b'EXIT': (udp_switch.exit_send, ['port', 'ip', 'screen_name']),
    }

    TCP_SWITCH = {
        b'HELO': (tcp_switch.helo_recv, ['port', 'ip', 'screen_name']),
        b'ACPT': (None, ['port', 'ip', 'screen_name']),
        b'RJCT': (None, ['port', 'ip', 'screen_name']),
        b'EXIT': (tcp_switch.exit_send, []),
    }

    MembershipList = {}  # initialize the Membership list on every new server object
    buddy_list_lock = Lock()

    def __init__(self, port: int = 7575):
        try:
            self.server_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # create a UDP socket (DGRAM)
            self.server_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # create a TCP socket (STREAM)
            self.port = port
            self.start_thread()
            try:
                while True:
                    pass
            except KeyboardInterrupt:
                self.server_TCP.close()
                self.server_UDP.close()
                del self.MembershipList  # make sure we don't burn anyone
                exit()
        except Exception as e:
            print(e)
            exit()

    def start_thread(self):
        start_new_thread(self.tcp_thread, (self.server_TCP, self.server_UDP), )

    def tcp_thread(self, server_tcp: socket = None, server_udp: socket = None):
        self.init_tcp_socket(server_tcp)
        thread_count = 0
        try:
            while True:
                connection, client_address = server_tcp.accept()
                start_new_thread(self.tcp_mux, (connection, client_address))
                thread_count += 1
        except (OSError, KeyboardInterrupt) as e:
            server_tcp.close()

    def tcp_mux(self, connection: socket, client_address: tuple):
        while True:
            try:
                buff = b''
                while buff.find(b'\n') == -1:
                    buff += connection.recv(1048)
                response = self.process_buff_tcp(buff, client_address)
                if response:
                    try:
                        connection.sendall(response[0]) # send the TCP response only
                    except Exception as e:
                        print(e)
                        continue
            except OSError as e:
                connection.close()
                break

    def udp_mux(self):
        pass

    @staticmethod
    def update_members(MembershipList, buddy_list_lock, tcp_identity, full_command, **kwargs):
        buddy_list_lock.acquire()

        if full_command:
            try:
                port = int(full_command.pop().decode().replace("\n", ""))
                ip = full_command.pop().decode()
                screen_name = full_command.pop().decode()
                if not MembershipList.get(screen_name):
                    MembershipList[screen_name] = [(ip, port), tcp_identity]
            finally:
                buddy_list_lock.release()
        else:
            try:
                for screen_name, identity in kwargs.items():
                    if not MembershipList.get(screen_name):
                        MembershipList[screen_name] = identity
            finally:
                buddy_list_lock.release()

    def delete_members(self, full_command):
        try:
            self.buddy_list_lock.acquire()
            if full_command:
                try:
                    full_command.pop().decode()  # discard the cmd we assume it is b'EXIT <screenname>'
                    screen_name = full_command.pop().decode()
                    if self.MembershipList.get(screen_name):
                        self.MembershipList.pop(screen_name)
                finally:
                    pass
            else:
                print('full_command is false, i.e. null or None')
        finally:
            self.buddy_list_lock.release()

    def add_members(self):
        pass

    def init_tcp_socket(self, server_tcp: socket):
        server_address = ('0.0.0.0', self.port)
        server_tcp.bind(server_address)
        server_tcp.listen(1)

    def init_udp_socket(self, server_udp: socket):
        server_address = ('localhost', self.port + 1)
        server_udp.bind(server_address)
        server_udp.listen(25)

    def process_buff_tcp(self, buff, client_address):
        buff = buff.replace(b'\n', b' ')
        buff = (re.sub(b':', b' ', buff)).split(b' ')
        # buff.reverse()
        # a part of parsing make sure it's a valid command before we parse
        handle_TCP = self.TCP_SWITCH[buff[0]][0]
        handle_UDP = None

        response_TCP = None
        response_UDP = None
        cpy_command = buff.copy()
        if handle_TCP:
            keyword_args = self.TCP_SWITCH[buff[0]][1]
            arguments = {}
            some_null = buff.pop()
            for key in keyword_args:
                arguments[key] = buff.pop()
            arguments['tcp_identity'] = client_address
            arguments['full_command'] = cpy_command[:-1]
            if b'EXIT' in buff[0]:
                identity = client_address
                screen_name_args = ''
                try:
                    self.buddy_list_lock.acquire()
                    for screen_name, i in self.MembershipList.items():
                        if i[1] == identity:
                            screen_name_args = screen_name
                finally:
                    self.buddy_list_lock.release()
                arguments['screen_name'] = screen_name_args
                arguments['identity'] = identity
                arguments['full_command'] = [f'{screen_name_args}'.encode(), f'EXIT'.encode()]
                response_TCP = handle_TCP(**arguments)
                self.delete_members(arguments['full_command'])
            else:
                response_TCP = handle_TCP(**arguments)

        if b'ACPT' in response_TCP or b'EXIT' in buff[0]: # very messy right now hack right now
            if b'ACPT' in response_TCP:
                handle_UDP = self.UDP_SWITCH[b'ACPT'][0]
            else:
                handle_UDP = self.UDP_SWITCH[buff[0]][0]


        if handle_UDP:
            response_UDP = handle_UDP(**arguments)
            if b'ACPT' in response_TCP:
                try:
                    self.buddy_list_lock.acquire()
                    for nick, identity in self.MembershipList.items():
                        self.server_UDP.sendto(response_UDP, identity[0])
                finally:
                    self.buddy_list_lock.release()
            if b'EXIT' in response_TCP:
                try:
                    self.buddy_list_lock.acquire()
                    for nick, identity in self.MembershipList.items():
                        self.server_UDP.sendto(response_UDP, identity[0])
                finally:
                    self.buddy_list_lock.release()

        return (response_TCP, response_UDP)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('server_port', metavar='server_port', type=int)
    args = parser.parse_args()

    if isinstance(args.server_port, int):
        client = MembershipServer(args.server_port)
    else:
        print("Your arguments are off")
        exit()
