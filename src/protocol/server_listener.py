import socket
from src.protocol.connection_socket import ConnectionSocket
from src.protocol.handshake import Handshake
from src.utils.logger import Logger


class ServerManager:
    @staticmethod
    def start_server(host='localhost', port=8080):
        server = ServerListener(host, port)
        server.start()
        return server

    @staticmethod
    def connect_to_server(own_addr=('localhost', 8080), server_addr=('localhost', 8080)):
        return Handshake.client(own_addr, server_addr)

class ServerListener:
    def __init__(self, host='localhost', port=8080):
        self.door_address = (host, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(self.door_address)
        self.socket.settimeout(2)
        self.connections = {}
        self.running = False
        Logger.debuglog(self.door_address, f"Server setup on {self.door_address}")

    def start(self):
        self.running = True
        Logger.debuglog(self.door_address, f"Server started on {self.door_address}")
            
    def get_client(self):
        # If the server is not running, raise an exception
        if not self.running:
            raise Exception("Server is not running.")
        
        # Create a new socket for the client
        # Wait for incoming data
        try:
            data, addr = self.socket.recvfrom(1024)
        except socket.timeout:
            Logger.debuglog(self.door_address, "Timeout waiting for new connection")
            return get_client()  # Timeout if no data received
        except Exception as e:
            Logger.debuglog(self.door_address, f"Error receiving data: {e}")
            return None

        try:
            valid_connection = Handshake.server(self.door_address, addr, data)
            self.connections[addr] = valid_connection

            Logger.debuglog(self.door_address, f"New connection established with {addr} using {valid_connection.source_address}")
            return valid_connection
        except Exception as e:
            Logger.debuglog(self.door_address, f"Handshake failed: {e}")
        return None
    
    

    def stop(self):
        self.running = False
        self.socket.close()
        Logger.debuglog(self.door_address, f"Server stopped on {self.door_address}")
        
        for conn in self.connections.values():
            conn.close()
        
        
        self.connections.clear()

