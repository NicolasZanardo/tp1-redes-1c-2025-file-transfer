from utils.logger import Logger

class ConnectionClossing:
    @classmethod
    def begin_close(cls, socket, peer_address):
        """Initiate connection closure by sending a CLOSE message and waiting for ACK."""
        try:
            socket.sendto(b'CLOSE', peer_address)
            Logger.debug(who=socket.getsockname(), message="Sent CLOSE message")
            socket.settimeout(1.0)
            data, addr = socket.recvfrom(1024)
            if data == b'CLOSE_ACK':
                Logger.debug(who=socket.getsockname(), message="Received CLOSE_ACK")
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
            Logger.debug(who=socket.getsockname(), message="Received CLOSE, sending CLOSE_ACK")
            socket.sendto(b'CLOSE_ACK', addr)
            return True
        except Exception as e:
            Logger.error(f"Error in respond_to_clossing: {e}")
            return False
