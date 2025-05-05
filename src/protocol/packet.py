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
    @abstractmethod
    def is_data(self, packet: bytes) -> bool:
        pass

    @abstractmethod
    def extract_data(self, packet: bytes) -> bytes:
        pass

    @abstractmethod
    def is_terminate(self, packet: bytes) -> bool:
        pass

class DefaultPacketizer(Packetizer):

    TYPE_DATA = 0x01
    TYPE_ACK = 0x02
    TYPE_TERM = 0x03

    def make_data_packet(self, seq, data):
        return bytes([self.TYPE_DATA]) + seq.to_bytes(4, byteorder='big') + data

    def make_ack_packet(self, seq):
        return bytes([self.TYPE_ACK]) + seq.to_bytes(4, byteorder='big')

    def make_terminate_packet(self):
        return bytes([self.TYPE_TERM])

    def is_ack(self, packet):
        return bool(packet) and packet[0] == self.TYPE_ACK

    def extract_seq(self, packet):
        return int.from_bytes(packet[1:5], byteorder='big') if len(packet) > 1 else None

    def is_data(self, packet):
        return bool(packet) and packet[0] == self.TYPE_DATA and len(packet) > 5

    def extract_data(self, packet):
        return packet[5:]

    def is_terminate(self, packet):
        return bool(packet) and packet[0] == self.TYPE_TERM