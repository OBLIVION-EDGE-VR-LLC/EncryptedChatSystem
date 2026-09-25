from queue import Queue


class PostOfficeBox(object):
    def __init__(self, recv_udp_queue: Queue, send_udp_queue: Queue):
        self._recv_udp_queue: Queue = recv_udp_queue  # messages from socket should be processed by the controller
        self._send_udp_queue: Queue = send_udp_queue  # messages from client UI should be put into this by the controller
        self.nick_name = None # nick_name of po_box holder of this client

    def read_from_mailbox(self):
        return self._recv_udp_queue.get(False)  # non-blocking queue

    def send_to_mailbox(self, message: bytes):
        return self._send_udp_queue.put(message, block=True)  # I will however block to ensure it's not jammed

    @property
    def send_udp_queue(self):
        return self._send_udp_queue

    @property
    def recv_udp_queue(self):
        return self._recv_udp_queue
