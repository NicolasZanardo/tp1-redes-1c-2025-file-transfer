import unittest
import threading
import time

class UtilsFunction(unittest.TestCase):
    def setup_test_threads(self, server_function, client_function, timeout=3):
        server_thread = threading.Thread(target=server_function)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.125)  # Give it a moment to start properly

        client_thread = threading.Thread(target=client_function)
        client_thread.daemon = True
        client_thread.start()

        client_thread.join(timeout = timeout)
        server_thread.join(timeout = timeout)

        if client_thread.is_alive() and server_thread.is_alive():
            self.fail("Client and server threads did not finish in time")

        if client_thread.is_alive():
            self.fail("Client thread did not finish in time")
        if server_thread.is_alive():
            self.fail("Server thread did not finish in time")

import random
import socket as std_socket
from utils import Logger

class SocketTestParams:
    LOSS_RATE = 0.2  # 20% packet loss
    LOSS_PERIOD = 3  # Every 3rd packet is lost
    NEW = std_socket.socket

# Custom socket wrapper to simulate packet loss
class LossySocket:
    def __init__(self, inet=None, dgram=None, sock=None, loss_rate=None):
        if sock is not None:
            self.sock = sock
        else:
            self.sock = SocketTestParams.NEW(inet, dgram)
        
        if loss_rate is not None:
            self.loss_rate = loss_rate
        else:
            self.loss_rate = SocketTestParams.LOSS_RATE

        self.stored = []

    def sendto(self, data, addr):
        if random.random() >= self.loss_rate:
            self.sock.sendto(data, addr)
        else:
            Logger.info(who=f"================== [Lossy-Socket {self.sock.getsockname()}]", message=f"I didn't sent the data to {addr} ==================")
            Logger.debug(who=f"======== [Lossy-Socket {self.sock.getsockname()}]", message=f"[{data}] ==================")

    def recvfrom(self, bufsize):
        return self.sock.recvfrom(bufsize)

    def bind(self, addr):
        self.sock.bind(addr)

    def close(self):
        self.sock.close()

    def settimeout(self, timeout):
        self.sock.settimeout(timeout)
    
    def getsockname(self):
        return self.sock.getsockname()


# Custom socket wrapper to simulate packet loss
class ConsistentlyLossySocket:
    def __init__(self, inet=None, dgram=None, sock=None, loss_period=None):
        if sock is not None:
            self.sock = sock
        else:
            self.sock = SocketTestParams.NEW(inet, dgram)
        
        if loss_period is not None:
            self.loss_period = loss_period
        else:
            self.loss_period = SocketTestParams.LOSS_PERIOD

        self.sent = 0
        self.stored = []

    def sendto(self, data, addr):
        self.sent += 1
        if self.sent % self.loss_period != 0:
            self.sock.sendto(data, addr)
        else:
            Logger.debug(who=f"[Lossy-Socket {self.sock.getsockname()}]", message=f"I didn't sent the data to {addr}")

    def recvfrom(self, bufsize):
        self.sent += 1
        try:
            if self.stored:
                return self.stored.pop(0)
            else:
                data, addr = self.sock.recvfrom(bufsize)
                if self.sent % self.loss_period == 0:
                    Logger.debug(
                        who=f"[Lossy-Socket {self.sock.getsockname()}]", 
                        message=f"I changed the order of the packets sent to {addr}, I stored [{data}]"
                    )
                    self.stored.append((data, addr))
                    return self.sock.recvfrom(bufsize)
                return data, addr
        except std_socket.timeout:
            if self.stored:
                return self.stored.pop(0)
            else:
                raise std_socket.timeout("Simulated packet loss")

    def bind(self, addr):
        self.sock.bind(addr)

    def close(self):
        self.sock.close()

    def settimeout(self, timeout):
        self.sock.settimeout(timeout)
    
    def getsockname(self):
        return self.sock.getsockname()