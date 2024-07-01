import socket
import sys
import select

from select import EPOLLIN, EPOLLPRI, EPOLLERR

class Connection:
    def __init__(self, path):
        # Create a Unix Domain socket and connect
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(path)
        except socket.error as msg:
            print(msg)
            sys.exit(1)

        self.sock = sock

        # initialize poll interface and register socket
        epoll = select.epoll()
        epoll.register(sock, EPOLLIN | EPOLLPRI | EPOLLERR)
        self.epoll = epoll

    def recv(self, timeout):
        '''
        timeout as float in seconds
        returns:
            - None on error or disconnection
            - bytes() (empty) on timeout
        '''

        events = self.epoll.poll(timeout)
        for ev in events:
            (fd, event) = ev
            if fd != self.sock.fileno():
                continue

            # check for socket error
            if event & EPOLLERR:
                return None

            # EPOLLIN or EPOLLPRI, just read the message
            msg = self.sock.recv(4096)

            # socket disconnected
            if len(msg) == 0:
                return None

            return msg

        return bytes()

    def send(self, msg):
        self.sock.send(msg)
