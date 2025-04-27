import socket
from src.utils.logger import Logger

class ConnectionSocket:
    def __init__(self, source_address, destination_address):
        self.source_address = source_address
        self.destination_address = destination_address
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(source_address)
        Logger.verboselog(self.source_address, f"Socket created from {self.source_address} to {self.destination_address}")

    def send(self, data: bytes):
        self.socket.sendto(data, self.destination_address)
        
        if data != b'ACK':
            Logger.verboselog(self.source_address, f"Sent: {data} to {self.destination_address}")

    def send_and_wait(self, data: bytes):
        self.socket.sendto(data, self.destination_address)
        
        if data != b'ACK':
            Logger.verboselog(self.source_address, f"Sent: {data} to {self.destination_address}")
            


    def receive(self):
        data, addr = self.socket.recvfrom(1024)

        if addr != self.destination_address:
            Logger.verboselog(self.source_address, f"Received data from unexpected address: {addr}")
            return self.receive()

        elif data == b'ACK':
            Logger.verboselog(self.source_address, f"ACK received from {addr}")
            return self.receive()

        else:
            self.send(b'ACK')
            Logger.verboselog(self.source_address, f"ACK sent to {addr} for data: {data}")
        
        Logger.verboselog(self.source_address, f"Received {data} from {addr}")
        return data, addr

    def close(self):
        self.socket.close()
        Logger.verboselog(self.source_address, f"Socket closed from {self.source_address} to {self.destination_address}")
        self.socket = None

    def get_message(self):
        data, addr = self.receive()
        return data