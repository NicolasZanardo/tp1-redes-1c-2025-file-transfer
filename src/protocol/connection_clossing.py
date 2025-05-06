from utils.logger import Logger

class ConnectionClossing:
    @classmethod
    def begin_close(cls, socket, peer_address):
        """Initiate connection closure by sending a CLOSE message and waiting for ACK."""
        try:
            socket.sendto(b'CLOSE', peer_address)
            Logger.debug(who=socket.getsockname(), message="Sent CLOSE message")
            socket.settimeout(1.0)
            data, _ = socket.recvfrom(1024)
            if data == b'CLOSE_ACK':
                Logger.debug(who=socket.getsockname(), message="Received CLOSE_ACK")
                data2, _ = socket.recvfrom(1024)
                if data2 == b'FIN':
                    socket.sendto(b'FIN_ACK', peer_address)
                    socket.settimeout(30.0)
                    return True
            else:
                Logger.error("Failed to receive CLOSE_ACK")
                return False
        except Exception as e:
            Logger.error(f"Error in begin_close: {e}")
            return False

    @classmethod
    def respond_to_clossing(cls, socket, addr):
        """Respond to a CLOSE message by sending CLOSE_ACK."""
        try:
            data, addr = socket.recvfrom(1024)
            if data != b'CLOSE':
                raise Exception("Error receiving CLOSE: Received {data}")
            Logger.debug(who=socket.getsockname(), message="Received CLOSE, sending CLOSE_ACK")
            socket.sendto(b'CLOSE_ACK', addr)
            socket.settimeout(1.0)
            socket.sendto(b'FIN', addr)
            socket.settimeout(2.0)
            data, addr = socket.recvfrom(1024)
            Logger.debug(message=f"Received {data}")
            if data == b'FIN_ACK':
                return True
            else:
                raise Exception("Error recieving FIN_ACK")
            
        except Exception as e:
            Logger.error(f"Error in respond_to_clossing: {e}")
            return False
