from utils.logger import Logger
import socket

TIMEOUT = 10
MAX_RETRIES = 5

class ConnectionClosing:
    @classmethod
    def begin_close(cls, sock: socket.socket, peer_address):
        """Cliente inicia el cierre con un 4-way handshake"""

        for i in range(MAX_RETRIES):
            try:
                sock.sendto(b'CLOSE', peer_address)
                Logger.debug(who=sock.getsockname(), message=f"Sent CLOSE (attempt {i+1})")
                sock.settimeout(TIMEOUT)
                data, _ = sock.recvfrom(1024)
                if data == b'CLOSE_ACK':
                    Logger.debug(who=sock.getsockname(), message="Received CLOSE_ACK")
                    break
            except socket.timeout:
                Logger.debug(who=sock.getsockname(), message="Timeout waiting CLOSE_ACK, retrying...")
        else:
            Logger.error("Failed to receive CLOSE_ACK after retries")
            return False

        for i in range(MAX_RETRIES):
            try:
                sock.settimeout(TIMEOUT)
                data, _ = sock.recvfrom(1024)
                if data == b'FIN':
                    Logger.debug(who=sock.getsockname(), message="Received FIN")
                    break
            except socket.timeout:
                Logger.debug(who=sock.getsockname(), message="Timeout waiting FIN, retrying...")
        else:
            Logger.error("Failed to receive FIN after retries")
            return False

        for i in range(MAX_RETRIES):
            try:
                sock.sendto(b'FIN_ACK', peer_address)
                Logger.debug(who=sock.getsockname(), message=f"Sent FIN_ACK (attempt {i+1})")
                return True
            except socket.timeout:
                Logger.debug(who=sock.getsockname(), message="Timeout sending FIN_ACK, retrying...")
        Logger.error("Failed to send FIN_ACK after retries")
        return False

    @classmethod
    def respond_to_closing(cls, sock: socket.socket, addr):
        """Servidor responde al close"""

        try:
            sock.settimeout(None)
            data, client_addr = sock.recvfrom(1024)
            if data != b'CLOSE':
                raise Exception(f"Expected CLOSE, got {data!r}")
            Logger.debug(who=sock.getsockname(), message="Received CLOSE")
        except Exception as e:
            Logger.error(f"Error waiting CLOSE: {e}")
            return False

        for i in range(MAX_RETRIES):
            try:
                sock.sendto(b'CLOSE_ACK', client_addr)
                Logger.debug(who=sock.getsockname(), message=f"Sent CLOSE_ACK (attempt {i+1})")
                sock.sendto(b'FIN', client_addr)
                Logger.debug(who=sock.getsockname(), message=f"Sent FIN (attempt {i+1})")
                
                sock.settimeout(TIMEOUT)

                ack, _ = sock.recvfrom(1024)
                if ack == b'FIN_ACK':  
                    Logger.debug(who=sock.getsockname(), message="Received FIN_ACK")
                    
                    return True
            except socket.timeout:
                Logger.debug(who=sock.getsockname(), message="Timeout waiting echo of CLOSE_ACK, retrying...")
        else:
            Logger.error("Failed to confirm CLOSE_ACK echo")
        
        return False
