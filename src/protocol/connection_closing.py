import socket
from utils import Logger, RetryHandler, ConnectionConfig

retrier = RetryHandler(
    retries=ConnectionConfig.MAX_RETRIES,
)

class ConnectionClosingProtocol:
    FIN = b"FIN"
    ACK = b"ACKFIN"

    @classmethod
    def start_closing_handshake(cls, sock: socket.socket, peer_address: tuple):
        sock.settimeout(ConnectionConfig.TIMEOUT)
        return (
            cls._send_fin_and_wait_peer(sock, peer_address) and
            cls._send_final_ack(sock, peer_address)
        )

    @classmethod
    def _send_fin_and_wait_peer(cls, sock, addr):
        Logger.debug(who=sock.getsockname(), message=f"===== CLOSING _send_fin_and_wait_peer to {addr}")
        def send_fin(attempt):
            sock.sendto(cls.FIN, addr)
            Logger.debug(who=sock.getsockname(), message=f"Sent FIN to {addr} (attempt {attempt})")
            
            data, _ = sock.recvfrom(1024)
            if data != cls.FIN:
                raise socket.timeout()
            Logger.debug(who=sock.getsockname(), message="Received FIN from peer")
            return True

        return retrier.run(
            action=send_fin,
            logger_who=sock.getsockname(),
            action_description="Sending FIN"
        )

    @classmethod
    def _send_final_ack(cls, sock, addr):
        Logger.debug(who=sock.getsockname(), message=f"===== CLOSING _send_final_ack to {addr}")
        try:
            sock.sendto(cls.ACK, addr)
            Logger.debug(who=sock.getsockname(), message="Sent final ACKFIN")
            return True
        except Exception as e:
            Logger.error(who=sock.getsockname(), message=f"Failed to send final ACK: {e}")
        
        return False
