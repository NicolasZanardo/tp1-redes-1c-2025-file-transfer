import socket
from protocol.connection_socket import ConnectionSocket
from utils.logger import Logger

class Handshake:
    @staticmethod
    def client(server_addr=('localhost', 8080)):
        skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        skt.bind(('', 0))
        own_addr = skt.getsockname()
        Logger.debug(who=own_addr, message=f"Connecting to server {server_addr}")
        

        # Send handshake to the server
        Logger.debug(who=own_addr, message=f"Sending LOGIN to {server_addr}")
        skt.sendto(b'LOGIN', server_addr)

        Logger.debug(who=own_addr, message=f"Waiting ACK of ('UNKNOWN', unknown)")
        resp, new_serv_addr = skt.recvfrom(1024)

        if resp != b'ACK':
            skt.close()
            Logger.debug(who=own_addr, message=f"Failed to receive ACK from server.")
            raise Exception("Failed to receive ACK from server.")
        skt.close()

        valid_connection = ConnectionSocket(new_serv_addr, own_addr)
        valid_connection.send(b'all ok')


        return valid_connection

    @staticmethod
    def server(own_addr=('localhost', 8080), client_addr=('localhost', 8080), client_msg=b'NO LOGIN'):
        if client_msg != b'LOGIN':
            raise Exception("Failed to receive LOGIN from client.")

        host = own_addr[0]
        valid_connection = get_free_connection(host, client_addr)

        if valid_connection is None:
            raise Exception("No free connection available")
        
        Logger.debug(who=valid_connection.source_address, message=f"Sending ACK to {client_addr}")
        valid_connection.send(b'ACK')
        
        recieved = valid_connection.get_message()
        if recieved != b'all ok':
            Logger.debug(who=valid_connection.source_address, message=f"Failed to receive b'all ok' from client, instead recieved {recieved}.")
            valid_connection.close()
            raise Exception(f"New port '{valid_connection.source_address[1]}' Failed to receive b'all ok' from client, instead recieved {recieved}.")

        return valid_connection
     
def get_free_connection(host, addr):
    return ConnectionSocket(addr)