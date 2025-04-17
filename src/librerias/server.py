import socket

class Server:
    def __init__(self, host, port, algorithm):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.clients = {}
        self.queues = {}
        self.running = True
        self.algorithm = algorithm

    def start(self):
        print("se bindea la conexion y se reciben los bytes(serializar/deserealizar)")
    