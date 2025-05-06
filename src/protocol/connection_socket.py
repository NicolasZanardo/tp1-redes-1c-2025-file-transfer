import socket
from utils.logger import Logger
from .connection_clossing import ConnectionClossingProtocol

class ConnectionSocket:
    def __init__(self, destination_address, source_address=None):
        if source_address is None:
            source_address = ('localhost', 0)

        self.destination_address = destination_address
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(source_address)
        self.source_address = self.socket.getsockname()
        Logger.debug(who=self.source_address, message=f"Socket created from {self.source_address} to {self.destination_address}")
        self.is_closing = False

    def send(self, data: bytes):
        self.socket.sendto(data, self.destination_address)
        if data != b'ACK':
            Logger.debug(who=self.source_address, message=f"Sent: {data} to {self.destination_address}")

    def send_and_wait(self, data: bytes):
        self.send(data)  # Just reuse the send() method

    def receive(self):
        data, addr = self.socket.recvfrom(1024)

        if addr != self.destination_address:
            Logger.debug(who=self.source_address, message=f"Ignored data from unknown address: {addr}")
            return self.receive()

        if data == b'FIN':
            self.close()
            return None, None  # Continue receiving until closure is complete

        elif data == b'ACK':
            Logger.debug(who=self.source_address, message="Received ACK")
            return self.receive()  # Skip ACKs during normal communication

        else:
            self.send(b'ACK')
            Logger.debug(who=self.source_address, message=f"Received data: {data}, sent ACK")
            return data, addr

    def close(self):
        if self.socket is None:
            Logger.debug(who=self.source_address, message="Socket already closed")
            return
        

        if self.is_closing:
            return 

        self.is_closing = True
        ConnectionClossingProtocol.start_clossing_handshake(self.socket, self.destination_address)
        Logger.debug(who=self.source_address, message="Received FIN, starting closure handshake")

        try:
            self.socket.close()
            Logger.debug(who=self.source_address, message=f"Socket closed from {self.source_address}")
        except Exception as e:
            Logger.error(who=self.source_address, message=f"Error while closing socket: {e}")
        self.socket = None

    def get_message(self, timeout=2, max_retries=5):
        self.socket.settimeout(timeout)
        for attempt in range(max_retries):
            try:
                data, _ = self.receive()
                return data
            except socket.timeout:
                Logger.debug(who=self.source_address, message=f"[Attempt {attempt+1}] Timeout waiting for message, retrying...")
        raise TimeoutError("Failed to receive message after retries.")
