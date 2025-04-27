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
        Logger.debug(who=self.door_address, message=f"Server setup on {self.door_address}")

    def start(self):
        self.running = True
        Logger.debug(who=self.door_address, message=f"Server started on {self.door_address}")
            
    def get_client(self):
        # If the server is not running, raise an exception
        if not self.running:
            raise Exception("Server is not running.")
        
        # Create a new socket for the client
        # Wait for incoming data
        try:
            data, addr = self.socket.recvfrom(1024)
        except socket.timeout:
            Logger.debug(who=self.door_address, message="Timeout waiting for new connection")
            return get_client()  # Timeout if no data received
        except Exception as e:
            Logger.debug(who=self.door_address, message=f"Error receiving data: {e}")
            return None

        try:
            valid_connection = Handshake.server(self.door_address, addr, data)
            self.connections[addr] = valid_connection

            Logger.debug(who=self.door_address, message=f"New connection established with {addr} using {valid_connection.source_address}")
            return valid_connection
        except Exception as e:
            Logger.debug(who=self.door_address, message=f"Handshake failed: {e}")
        return None
    
    

    def stop(self):
        self.running = False
        self.socket.close()
        Logger.debug(who=self.door_address, message=f"Server stopped on {self.door_address}")
        
        for conn in self.connections.values():
            conn.close()
        
        
        self.connections.clear()

