from utils.logger import Logger
import socket

class ConnectionClossing:
    FIN = b"FIN"
    ACK = b"ACK"
    TIMEOUT = 5  # seconds

    @classmethod
    def begin_handshake(cls, sock: socket.socket, peer_address: tuple):
        Logger.debug(who=sock.getsockname(), message="Starting four-way handshake")
        try:
            # Step 1: Send FIN
            sock.sendto(cls.FIN, peer_address)
            Logger.debug(who=sock.getsockname(), message="Sent FIN")

            # Step 2: Wait for ACK
            sock.settimeout(cls.TIMEOUT)
            data, addr = sock.recvfrom(1024)
            if data != cls.ACK:
                Logger.error(who=sock.getsockname(), message="Expected ACK, got something else")
                return False
            Logger.debug(who=sock.getsockname(), message="Received ACK")

            # Step 3: Wait for FIN
            data, addr = sock.recvfrom(1024)
            if data != cls.FIN:
                Logger.error(who=sock.getsockname(), message="Expected FIN from peer, got something else")
                return False
            Logger.debug(who=sock.getsockname(), message="Received peer's FIN")

            # Step 4: Send ACK
            sock.sendto(cls.ACK, peer_address)
            Logger.debug(who=sock.getsockname(), message="Sent final ACK")
            return True
        except socket.timeout:
            Logger.error(who=sock.getsockname(), message="Timeout during handshake")
            return False
        finally:
            sock.settimeout(None)

    @classmethod
    def respond_to_handshake(cls, sock: socket.socket, peer_address: tuple):
        Logger.debug(who=sock.getsockname(), message="Responding to FIN from peer")
        try:
            # Step 1: Send ACK
            sock.sendto(cls.ACK, peer_address)
            Logger.debug(who=sock.getsockname(), message="Sent ACK to peer")

            # Step 2: Send FIN
            sock.sendto(cls.FIN, peer_address)
            Logger.debug(who=sock.getsockname(), message="Sent FIN to peer")

            # Step 3: Wait for final ACK
            sock.settimeout(cls.TIMEOUT)
            data, addr = sock.recvfrom(1024)
            if data != cls.ACK:
                Logger.error(who=sock.getsockname(), message="Expected final ACK, got something else")
                return False
            Logger.debug(who=sock.getsockname(), message="Received final ACK, handshake complete")
            return True
        except socket.timeout:
            Logger.error(who=sock.getsockname(), message="Timeout during handshake response")
            return False
        finally:
            sock.settimeout(None)


class ConnectionClossingProtocol:
    FIN = b"FIN"
    ACK = b"ACKFIN"
    TIMEOUT = 5  # seconds

    @classmethod
    def start_clossing_handshake(cls, sock: socket.socket, peer_address: tuple):
        try:
            # Step 1: Send FIN
            sock.sendto(cls.FIN, peer_address)
            Logger.debug(who=sock.getsockname(), message="Sent FIN")

            # Process lingering ACKS
            data = b"ACK"
            while data == b"ACK":
                data, addr = sock.recvfrom(1024)
            
            # Step 3: Wait for FIN
            if data != cls.FIN:
                Logger.error(who=sock.getsockname(), message=f"Expected FIN from peer, got ({data})")
                return False
            Logger.debug(who=sock.getsockname(), message="Received peer's FIN")

            # Step 4: Send ACK
            sock.sendto(cls.ACK, peer_address)
            Logger.debug(who=sock.getsockname(), message="Sent final ACK")

            # Step 2: Wait for ACK
            sock.settimeout(cls.TIMEOUT)
            data, addr = sock.recvfrom(1024)
            if data != cls.ACK:
                Logger.error(who=sock.getsockname(), message="Expected ACK, got ({data})")
                return False
            Logger.debug(who=sock.getsockname(), message="Received ACK")
            return True
        except socket.timeout:
            Logger.error(who=sock.getsockname(), message="Timeout during handshake")
            return False
        finally:
            sock.settimeout(None)