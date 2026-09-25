from typing import List

from chatclient.TheRiddlerChatSystem.Model.stateful_messaging.COM.communication_base import CommunicationBase


class SymmetricCryptoMessaging(CommunicationBase):
    def send(self, message: bytes) -> int:
        """
        send is a method in the symmetric crypto messaging that shoudl just send the ciphertext bytes

        @param: message is the bytes message object to send
        @returns: an integer of how many bytes were sent
        """
        NotImplemented(f"Please finish writing the {self.__class__} send method")

    def recv(self, buffer: List[bytes]) -> List[bytes]:
        """
        recv is a method to receive bytes and order them into a list to be processed.

        @buffer:  is  List of bytes where each element is an incoming message of bytes to be processed.
        """
        NotImplemented(f"Please finish writing the {self.__class__} recv method")