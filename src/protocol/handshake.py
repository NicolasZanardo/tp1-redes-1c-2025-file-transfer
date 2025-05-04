# protocol/handshake.py
import socket
from protocol.connection_socket import ConnectionSocket
from utils.logger import Logger

TIMEOUT = 2
MAX_RETRIES = 5

class Handshake:
    @staticmethod
    def client(server_addr=('localhost',8080), mode='download'):
        """
        mode: 'upload' (cliente envía al servidor) o 'download' (cliente recibe del servidor)
        """
        skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        skt.bind(('',0))
        skt.settimeout(TIMEOUT)
        own = skt.getsockname()

        msg = f"LOGIN:{mode}".encode()
        for i in range(MAX_RETRIES):
            Logger.debug(who=own, message=f"Sending {msg!r} to {server_addr} (try {i+1})")
            skt.sendto(msg, server_addr)
            try:
                resp, data_addr = skt.recvfrom(1024)
                if resp.startswith(b"ACK:"):
                    _, agreed_mode = resp.decode().split(':',1)
                    if agreed_mode != mode:
                        raise Exception(f"Inconsistent modes. recieved {agreed_mode} instead of {mode}")
                    skt.close()
                    conn = ConnectionSocket(data_addr, own)
                    # confirm final
                    conn.send(b"ALL:OK")
                    return conn, agreed_mode
            except socket.timeout:
                Logger.debug(who=own, message="Timeout waiting ACK, retrying…")
            except Exception as e:
                Logger.error(who=own, message=f"{e}")
                
        skt.close()
        raise Exception("Handshake failed (no ACK)")

    @staticmethod
    def server(own_addr=('localhost',8080), client_addr=None, login_msg=b''):
        """
        Devuelve (ConnectionSocket, mode) o lanza.
        """
        # login_msg == b"LOGIN:<mode>"
        try:
            text = login_msg.decode()
            prefix, mode = text.split(':',1)
            if prefix!='LOGIN' or mode not in ('upload','download'):
                raise
        except:
            raise Exception(f"Bad handshake msg {login_msg!r}")

        # abrimos nuevo socket efímero
        conn = ConnectionSocket(client_addr)
        # devolvemos ACK:<mode>
        ack = f"ACK:{mode}".encode()
        Logger.debug(who=conn.source_address, message=f"Sending {ack!r} to {client_addr}")
        conn.send(ack)

        # ahora recibimos el ALL:OK
        resp = conn.get_message()
        if resp!=b"ALL:OK":
            conn.close()
            raise Exception(f"Expected ALL:OK, got {resp!r}")
        return conn, mode
