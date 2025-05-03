import socket
import time
from protocol.connection_socket import ConnectionSocket
from utils.logger import Logger

TIMEOUT = 2
MAX_RETRIES = 5

class Handshake:
    @staticmethod
    def client(server_addr=('localhost', 8080)):
        skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        skt.bind(('', 0))
        skt.settimeout(TIMEOUT)
        own_addr = skt.getsockname()
        Logger.debug(who=own_addr, message=f"Connecting to server {server_addr}")

        # === Envío de LOGIN con retry ===
        for attempt in range(MAX_RETRIES):
            try:
                Logger.debug(who=own_addr, message=f"Sending LOGIN to {server_addr} (attempt {attempt+1})")
                skt.sendto(b'LOGIN', server_addr)
                Logger.debug(who=own_addr, message=f"Waiting ACK of ('UNKNOWN', unknown)")
                resp, new_serv_addr = skt.recvfrom(1024)
                if resp == b'ACK':
                    break
            except socket.timeout:
                Logger.debug(who=own_addr, message=f"Timeout waiting ACK, retrying...")
        else:
            skt.close()
            raise Exception("Failed to receive ACK from server after retries.")
        
        skt.close()

        valid_connection = ConnectionSocket(new_serv_addr, own_addr)
        for attempt in range(MAX_RETRIES):
            try:
                Logger.debug(who=own_addr, message=f"Sent: b'all ok' to {new_serv_addr} (attempt {attempt+1})")
                valid_connection.send(b'all ok')
                return valid_connection
            except socket.timeout:
                Logger.debug(who=own_addr, message=f"Timeout sending all ok, retrying...")

        valid_connection.close()
        raise Exception("Failed to send 'all ok' after retries.")

    @staticmethod
    def server(own_addr=('localhost', 8080), client_addr=('localhost', 8080), client_msg=b'NO LOGIN'):
        if client_msg != b'LOGIN':
            raise Exception("Failed to receive LOGIN from client.")

        #host = own_addr[0]
        valid_connection = ConnectionSocket(client_addr)
        Logger.debug(
                who=valid_connection.source_address,
                message=f"Sending ACK to {client_addr}"
            )
        if valid_connection is None:
            raise Exception("No free connection available")

        for attempt in range(MAX_RETRIES):
            try:
                Logger.debug(who=valid_connection.source_address, message=f"Sending ACK to {client_addr} (attempt {attempt+1})")
                valid_connection.send(b'ACK')
                recieved = valid_connection.get_message()
                if recieved == b'all ok':
                    break
                else:
                    Logger.debug(who=valid_connection.source_address, message=f"Expected b'all ok' but got {recieved}")
            except socket.timeout:
                Logger.debug(who=valid_connection.source_address, message=f"Timeout waiting all ok, retrying...")
        else:
            valid_connection.close()
            raise Exception("Failed to receive 'all ok' after retries.")

        return valid_connection
