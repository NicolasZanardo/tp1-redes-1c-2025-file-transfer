import socket
from utils import Logger, FileWriter
from protocol.packet import Packetizer
from .utils import PacketReceiver

class SelectiveRepeatReceiver:
    def __init__(self, sock: socket.socket, file_writer: FileWriter,
                 packetizer: Packetizer, timeout: float = 1.0, window_size: int = 4):
        self.sock = sock
        self.file_writer = file_writer
        self.packetizer = packetizer
        self.timeout = timeout
        self.window_size = window_size
        self.expected_seq = 0
        self.buffer = {}
        self._running = True
        self.packet_receiver = PacketReceiver(sock, packetizer)
        self.sock.settimeout(timeout + 0.1)
        Logger.debug(who=self.sock.getsockname(), message=f"[SR-Receiver] Initialized with window size {window_size}")

    def start(self) -> None:
        Logger.info("[SR-Receiver] Receiver started.")
        while self._running:
            try:
                packet, addr, is_valid = self.packet_receiver.receive_packet()
                if not self._running:
                    break
                if not is_valid:
                    continue
                if self.packetizer.is_terminate(packet):
                    Logger.info("[SR-Receiver] Received terminate.")
                    self._running = False
                    self.stop()  # Explicitly stop to close socket
                    break
                seq = self.packetizer.extract_seq(packet)
                Logger.debug(who=self.sock.getsockname(), message=f"[SR-Receiver] Received DATA seq={seq} from {addr}")
                Logger.debug(who=self.sock.getsockname(), message=f"[SR-Receiver] In window: expected={self.expected_seq}, got={seq}")
                if self.expected_seq <= seq < self.expected_seq + self.window_size:
                    self.packet_receiver.send_ack(seq, addr)
                    Logger.debug(who=self.sock.getsockname(), message=f"[SR-Receiver] Sent ACK for seq={seq}")
                    if seq not in self.buffer:
                        self.buffer[seq] = self.packetizer.extract_data(packet)
                    while self.expected_seq in self.buffer:
                        self.file_writer.write_chunk(self.buffer.pop(self.expected_seq))
                        Logger.debug(who=self.sock.getsockname(), message=f"[SR-Receiver] Wrote and advanced expected_seq={self.expected_seq}")
                        self.expected_seq += 1
                else:
                    last_ack = self.expected_seq - 1
                    if last_ack >= 0:
                        self.packet_receiver.send_ack(last_ack, addr)
                        Logger.debug(who=self.sock.getsockname(), message=f"[SR-Receiver] Out-of-window seq={seq}, resent ACK for seq={last_ack}")
            except socket.timeout:
                continue
            except OSError:
                break
        self.file_writer.close()
        Logger.info("[SR-Receiver] File saved.")

    def stop(self) -> None:
        self._running = False
        try:
            self.sock.close()
        except OSError:
            pass
        
        try:
            self.file_writer.close()
        except OSError:
            pass

        Logger.debug(message="[SR-Receiver] Socket closed.")