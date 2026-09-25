from abc import ABC
from queue import Queue
from typing import List
from socket import socket

from chatclient.TheRiddlerChatSystem.Model.stateful_messaging.COM.communication_base import CommunicationBase


class PlainTextCOMM(CommunicationBase):
    def __init__(self, send_queue: Queue, recv_queue: Queue, tcp_socket: socket, udp_socket: socket, buff_queue: Queue):
        super(PlainTextCOMM, self).__init__(send_queue, recv_queue)
        self.tcp_socket = tcp_socket
        self.udp_socket = udp_socket
        self.buff_queue = buff_queue

    def handle_cmd(self, buffer: bytes):
        pass

    def send(self, message: bytes) -> int:
        # TODO
        try:
            self.send_queue.put(message)
            self.client_udp_send(self.udp_socket)
            return len(message)
        except Exception as e:
            print(e)

    def recv(self, buffer: List[bytes]) -> List[bytes]:
        # TODO
        try:
            self.recv_queue.get(buffer)
            self.client_Thread_Read(self.udp_socket)
            print("started processsing the recv")
            return [b"processed_successfully",]
        except Exception as e:
            print(e)

