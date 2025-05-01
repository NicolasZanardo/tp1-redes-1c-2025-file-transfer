from abc import ABC, abstractmethod

class Packetizer(ABC):
    @abstractmethod
    def make_data_packet(self, seq: int, data: bytes) -> bytes:
        pass

    @abstractmethod
    def make_ack_packet(self, seq: int) -> bytes:
        pass

    @abstractmethod
    def make_terminate_packet(self) -> bytes:
        pass

    @abstractmethod
    def is_ack(self, packet: bytes) -> bool:
        pass

    @abstractmethod
    def extract_seq(self, packet: bytes) -> int:
        pass

class DefaultPacketizer(Packetizer):

    def make_data_packet(self, seq, data):
        return bytes([0x01, seq]) + data

    def make_ack_packet(self, seq):
        return bytes([0x02, seq])

    def make_terminate_packet(self):
        return bytes([0x03])

    def is_ack(self, packet):
        return bool(packet) and packet[0] == 0x02

    def extract_seq(self, packet):
        return packet[1] if len(packet) > 1 else None