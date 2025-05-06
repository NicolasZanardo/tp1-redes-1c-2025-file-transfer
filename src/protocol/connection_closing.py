import socket
from utils import Logger, RetryHandler

class ConnectionConfig:
    TIMEOUT = 10
    MAX_RETRIES = 5

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
            cls._send_fin(sock, peer_address) and
            #cls._wait_ack(sock, peer_address) and 
            cls._wait_peer_fin(sock, peer_address) and
            cls._send_final_ack(sock, peer_address)
        )

    @classmethod
    def _send_fin(cls, sock, addr):
        Logger.debug(who=sock.getsockname(), message=f"===== CLOSING _send_fin to {addr}")
        def send_fin(attempt):
            sock.sendto(cls.FIN, addr)
            Logger.debug(who=sock.getsockname(), message=f"Sent FIN (attempt {attempt})")
            return True

        return retrier.run(
            action=send_fin,
            logger_who=sock.getsockname(),
            action_description="Sending FIN"
        )

    @classmethod
    def _wait_ack(cls, sock, addr):
        Logger.debug(who=sock.getsockname(), message=f"===== CLOSING _wait_ack to {addr}")
        def wait_ack(_):
            data, _ = sock.recvfrom(1024)
            if data != cls.ACK:
                raise socket.timeout()
            Logger.debug(who=sock.getsockname(), message="Received ACKFIN")
            return True

        return retrier.run(
            action=wait_ack,
            logger_who=sock.getsockname(),
            action_description="Waiting for ACKFIN"
        )

    @classmethod
    def _wait_peer_fin(cls, sock, addr):
        Logger.debug(who=sock.getsockname(), message=f"===== CLOSING _wait_peer_fin to {addr}")
        def wait_fin(_):
            while True:
                data, _ = sock.recvfrom(1024)
                if not data.startswith(b"ACK"):
                    break
            if data != cls.FIN:
                raise ValueError(f"Expected FIN, got {data}")
            Logger.debug(who=sock.getsockname(), message="Received peer's FIN")
            return True
        
        return retrier.run(
            action=wait_fin,
            logger_who=sock.getsockname(),
            action_description="Waiting for peer FIN"
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
