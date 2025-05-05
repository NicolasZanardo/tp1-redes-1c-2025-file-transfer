import socket
from utils.logger import Logger
from .connection_clossing import ConnectionClossing

class ConnectionSocket:
    def __init__(self, destination_address, source_address=None):
        if source_address is None:
            source_address = ('localhost', 0)

        self.destination_address = destination_address
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.socket.bind(source_address)  # Bind to any available port
        self.source_address = self.socket.getsockname()
        Logger.debug(who=self.source_address, message=f"Socket created from {self.source_address} to {self.destination_address}")

    def send(self, data: bytes):
        self.socket.sendto(data, self.destination_address)
        
        if data != b'ACK':
            Logger.debug(who=self.source_address, message=f"Sent: {data} to {self.destination_address}")

    def send_and_wait(self, data: bytes):
        self.socket.sendto(data, self.destination_address)
        
        if data != b'ACK':
            Logger.debug(who=self.source_address, message=f"Sent: {data} to {self.destination_address}")

    def receive(self):
        data, addr = self.socket.recvfrom(1024)

        if addr != self.destination_address:
            Logger.debug(who=self.source_address, message=f"Received data from unexpected address: {addr}")
            return self.receive()

        if data == b'CLOSE':
            Logger.debug(who=self.source_address, message=f"Received CLOSE from {addr}, sending CLOSE_ACK")
            ConnectionClossing.respond_to_clossing(self.socket, addr)
            self.is_closing = True
            raise ConnectionClosedError("Connection closed by remote side")

        elif data == b'ACK':
            Logger.debug(who=self.source_address, message=f"ACK received from {addr}")
            return self.receive()

        else:
            self.send(b'ACK')
            Logger.debug(who=self.source_address, message=f"ACK sent to {addr} for data: {data}")
        
        Logger.debug(who=self.source_address, message=f"Received {data} from {addr}")
        return data, addr

    def close(self):
        if self.socket is None:
            Logger.debug(who=self.source_address, message="Socket already closed")
            return
        
        try:
            if ConnectionClossing.begin_close(self.socket, self.destination_address):
                Logger.debug(who=self.source_address, message="Closing handshake completed")
            else:
                Logger.error(who=self.source_address, message="Closing handshake failed")
        except Exception as e:
            Logger.error(who=self.source_address, message=f"Error during closing handshake: {e}")
        finally:
            try:
                self.socket.close()
                Logger.debug(who=self.source_address, message=f"Socket closed from {self.source_address} to {self.destination_address}")
            except Exception as e:
                Logger.error(who=self.source_address, message=f"Error closing socket: {e}")
            self.socket = None


    def get_message(self, timeout=2, max_retries=5):
        self.socket.settimeout(timeout)
        for attempt in range(max_retries):
            try:
                data, addr = self.receive()
                return data
            except socket.timeout:
                Logger.debug(who=self.source_address, message=f"[Attempt {attempt+1}] Timeout waiting for message, retrying...")
        raise TimeoutError("Failed to receive message after retries.")