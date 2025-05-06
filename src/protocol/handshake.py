# protocol/handshake.py
import socket
from protocol.connection_socket import ConnectionSocket
from utils.logger import Logger

TIMEOUT = 5
MAX_RETRIES = 5

class Handshake:
    @staticmethod
    def client(server_addr=('localhost',8080), mode='download', filename='file.file'):
        """
        mode: 'upload' (cliente envía al servidor) o 'download' (cliente recibe del servidor)
        """
        skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        skt.bind(('',0))
        skt.settimeout(TIMEOUT)
        own = skt.getsockname()
        Logger.debug(who=own, message=f"Client handshake to {server_addr} with mode '{mode}' and filename '{filename}'")

        msg = f"LOGIN:{mode}:{filename}".encode()
        for i in range(MAX_RETRIES):
            Logger.debug(who=own, message=f"Sending {msg!r} to {server_addr} (try {i+1})")
            skt.sendto(msg, server_addr)
            try:
                resp, data_addr = skt.recvfrom(1024)
                prefix, agreed_mode, agreed_filename = resp.decode().split(':')

                if prefix != "ACK":
                    continue

                if agreed_mode != mode:
                    raise Exception(f"Inconsistent modes. recieved {agreed_mode} instead of {mode}")
                if agreed_filename != filename:
                    raise Exception(f"Inconsistent filename. recieved '{agreed_filename}' instead of '{filename}'")
                skt.close()
                conn = ConnectionSocket(data_addr, own)
                # confirm final
                conn.send(b"ALL:OK")
                return conn, agreed_mode, agreed_filename
            except socket.timeout:
                Logger.debug(who=own, message="Timeout waiting ACK, retrying…")
            except Exception as e:
                Logger.error(who=own, message=f"{e}")
                
        skt.close()
        raise Exception("Handshake failed (no ACK)")

    @staticmethod
    def server(own_addr=('localhost',8080), client_addr=None, login_msg=b''):
        Logger.debug(f"Loggin msg recibido: {login_msg!r} from {client_addr}")
        """
        Devuelve (ConnectionSocket, mode) o lanza.
        """
        Logger.debug(who=own_addr, message=f"server handshake from {client_addr} with {login_msg!r}")
        # login_msg == b"LOGIN:<mode>"
        try:
            text = login_msg.decode()
            prefix, mode, filename = text.split(':')

            if prefix!='LOGIN' or mode not in ('upload','download'):
                raise
        except:
            raise Exception(f"Bad handshake msg {login_msg!r}")

        # abrimos nuevo socket efímero
        conn = ConnectionSocket(client_addr)
        # devolvemos ACK:<mode>
        ack = f"ACK:{mode}:{filename}".encode()
        Logger.debug(who=conn.source_address, message=f"Sending {ack!r} to {client_addr}")
        conn.send(ack)

        # ahora recibimos el ALL:OK
        resp = conn.get_message()
        if resp!=b"ALL:OK":
            conn.close()
            raise Exception(f"Expected ALL:OK, got {resp!r}")
        
        Logger.debug(f"Handshake server enviando conn, mode, filename: {conn}, {mode}, {filename}")
        return conn, mode, filename
