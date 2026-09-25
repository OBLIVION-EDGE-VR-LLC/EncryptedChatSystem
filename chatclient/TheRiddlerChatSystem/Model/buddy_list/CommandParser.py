from typing import ByteString
import colorama as color

class CommandParserAndBuilder:
    """
    CommandParserAndBuilder initializes dictionaries that make it convenient to parse and build messages
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