import socket
from protocol.packet import Packetizer
from utils.logger import Logger

class PacketSender:
    def __init__(self, sock: socket.socket, dest: tuple, packetizer: Packetizer):
        self.sock = sock
        self.dest = dest
        self.packetizer = packetizer

    def send_packet(self, seq: int, data: bytes) -> None:
        packet = self.packetizer.make_data_packet(seq, data)
        self.sock.sendto(packet, self.dest)
        Logger.debug(who=self.sock.getsockname(), message=f"[PACKET-Sender] Sent seq={seq}")

    def send_terminate(self) -> None:
        term = self.packetizer.make_terminate_packet()
        self.sock.sendto(term, self.dest)
        Logger.debug(who=self.sock.getsockname(), message="[PACKET-Sender] Sent terminate")


class PacketReceiver:
    def __init__(self, sock: socket.socket, packetizer: Packetizer):
        self.sock = sock
        self.packetizer = packetizer

    def receive_packet(self) -> tuple[bytes, tuple, bool]:
        packet, addr = self.sock.recvfrom(2048)
        is_data = self.packetizer.is_data(packet)
        is_terminate = self.packetizer.is_terminate(packet)
        Logger.debug(who=self.sock.getsockname(), message=f"[PACKET-Receiver] Recieved packet from {addr}")
        return packet, addr, is_data or is_terminate

    def send_ack(self, seq: int, addr: tuple) -> None:
        ack = self.packetizer.make_ack_packet(seq)
        self.sock.sendto(ack, addr)
        Logger.debug(who=self.sock.getsockname(), message=f"[PACKET-Receiver] Sent ACK seq={seq}")