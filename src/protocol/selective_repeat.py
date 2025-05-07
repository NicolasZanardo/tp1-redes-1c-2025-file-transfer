# protocol/selective_repeat.py
import socket
import threading
from protocol.packet import Packetizer, DefaultPacketizer
from utils.logger import Logger

class SelectiveRepeatProtocol:
    def __init__(self, sock: socket.socket, dest: tuple, file_path: str,
                 packetizer: Packetizer = None, timeout: float = 10.0, window_size: int = 1000):
        self.sock = sock
        self.dest = dest
        self.file_path = file_path
        self.timeout = timeout
        self.window_size = window_size
        self.base = 0
        self.next_seq = 0
        self.timers = {}              
        self.acked = {}               
        self.lock = threading.Lock()
        self.packetizer = packetizer or DefaultPacketizer()
        self.packets = list(self._file_reader())
        self.total = len(self.packets)
        self.send_event = threading.Event()
        self.sock.settimeout(timeout + 0.1)
        Logger.debug(who=self.sock.getsockname(), message=f"SR init for {dest}, file:{file_path}, win:{window_size}")

    def _file_reader(self, chunk_size=1024):
        with open(self.file_path, 'rb') as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                yield data

    def start(self):
        Logger.info(f"[SR] Starting transfer to {self.dest}")
        threading.Thread(target=self._receive_acks, daemon=True).start()
        with self.lock:
            while self.next_seq < self.base + self.window_size and self.next_seq < self.total:
                self._send(self.next_seq)
                self.next_seq += 1
        self.send_event.wait()
        term = self.packetizer.make_terminate_packet()
        self.sock.sendto(term, self.dest)
        Logger.info("[SR] Transfer completed.")

    def _send(self, seq):
        packet = self.packetizer.make_data_packet(seq, self.packets[seq])
        self.sock.sendto(packet, self.dest)
        Logger.debug(who=self.sock.getsockname(), message=f"[SR] Sent seq={seq}")
        timer = threading.Timer(self.timeout, self._timeout, args=(seq,))
        self.timers[seq] = timer
        timer.start()

    def _timeout(self, seq):
        with self.lock:
            if not self.acked.get(seq, False):
                Logger.debug(who=self.sock.getsockname(), message=f"[SR] Timeout seq={seq}, retransmitting")
                self._send(seq)

    def _receive_acks(self):
        while True:
            try:
                packet, _ = self.sock.recvfrom(2048)
                if self.packetizer.is_ack(packet):
                    seq = self.packetizer.extract_seq(packet)
                    Logger.debug(who=self.sock.getsockname(), message=f"[SR] Received ACK seq={seq}")
                    with self.lock:
                        if self.base <= seq < self.base + self.window_size:
                            self.acked[seq] = True
                            if seq in self.timers:
                                self.timers[seq].cancel()
                                del self.timers[seq]
                            while self.acked.get(self.base, False):
                                del self.acked[self.base]
                                self.base += 1
                                if self.next_seq < self.total:
                                    self._send(self.next_seq)
                                    self.next_seq += 1
                            if self.base == self.total:
                                self.send_event.set()
                                return
            except socket.timeout:
                continue

    def close(self):
        for t in self.timers.values():
            t.cancel()
        try:
            self.sock.close()
        except OSError:
            pass
        self.sock.close()
        Logger.debug(who=self.dest, message="Socket closed.")


class SelectiveRepeatReceiver:
    def __init__(self, sock: socket.socket, output_path: str,
                 packetizer: Packetizer = None, timeout: float = 1.0, window_size: int = 1000):
        self.sock = sock
        self.output_path = output_path
        self.packetizer = packetizer or DefaultPacketizer()
        self.timeout = timeout
        self.window_size = window_size
        self.expected_seq = 0
        self.buffer = {}  
        self.running = True
        self.sock.settimeout(timeout + 0.1)
        Logger.debug(who=self.sock.getsockname(), message=f"SR Receiver init, output:{output_path}, win:{window_size}")

    def start(self):
        Logger.info("[SR-Receiver] Receiver started.")
        with open(self.output_path, 'wb') as f:
            while self.running:
                try:
                    packet, addr = self.sock.recvfrom(2048)
                    if self.packetizer.is_data(packet):
                        seq = self.packetizer.extract_seq(packet)
                        Logger.debug(who=self.sock.getsockname(), message=f"[SR-Receiver] Recv DATA seq={seq} from {addr}")

                        if self.expected_seq <= seq < self.expected_seq + self.window_size:

                            ack = self.packetizer.make_ack_packet(seq)
                            self.sock.sendto(ack, addr)
                            Logger.debug(who=self.sock.getsockname(), message=f"[SR-Receiver] Sent ACK seq={seq}")

                            if seq not in self.buffer:
                                self.buffer[seq] = self.packetizer.extract_data(packet)

                            while self.expected_seq in self.buffer:
                                f.write(self.buffer.pop(self.expected_seq))
                                Logger.debug(who=self.sock.getsockname(), message=f"[SR-Receiver] Written seq={self.expected_seq}")
                                self.expected_seq += 1
                        else:

                            last_ack = self.expected_seq - 1
                            if seq >= 0:
                                nak = self.packetizer.make_ack_packet(seq)
                                self.sock.sendto(nak, addr)
                                Logger.debug(who=self.sock.getsockname(), message=f"[SR-Receiver] Resent ACK seq={last_ack}")
                    elif self.packetizer.is_terminate(packet):
                        Logger.info("[SR-Receiver] Received terminate.")
                        self.running = False
                except socket.timeout:
                    continue
        Logger.info(f"[SR-Receiver] File saved to {self.output_path}")

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass
        Logger.debug(message=f"[SR-Receiver] Socket closed for {self.output_path}")
