import socket
import threading
import time
from protocol.packet import Packetizer, DefaultPacketizer
from utils.logger import Logger

class GoBackNProtocol:
    def __init__(self, sock: socket.socket, dest: tuple, file_path: str,
                 packetizer: Packetizer = None, timeout: float = 1.0, window_size: int = 4):
        self.sock = sock
        self.dest = dest
        self.file_path = file_path
        self.timeout = timeout
        self.window_size = window_size
        self.base = 0
        self.next_seq = 0
        self.lock = threading.Lock()
        self.timers = {}
        self.packetizer = packetizer or DefaultPacketizer()
        self.reader = list(self._file_reader())
        self.total_packets = len(self.reader)
        self.ack_event = threading.Event()
        self.sock.settimeout(self.timeout + 0.1)
        Logger.debug(who=self.sock.getsockname(), message=f"GoBackNProtocol initialized for {dest}, file: {file_path}, window: {window_size}")

    def _file_reader(self, chunk_size: int = 1024):
        with open(self.file_path, 'rb') as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                yield data

    def start(self):
        Logger.info(f"[GBN] Starting transfer to {self.dest}")
        recv_thread = threading.Thread(target=self._receive_acks, daemon=True)
        recv_thread.start()
        with self.lock:
            while self.next_seq < self.base + self.window_size and self.next_seq < self.total_packets:
                self._send_packet(self.next_seq)
                self.next_seq += 1
        self.ack_event.wait()
        term = self.packetizer.make_terminate_packet()
        self.sock.sendto(term, self.dest)
        Logger.info("[GBN] Transfer completed.")

    def _send_packet(self, seq):
        data = self.reader[seq]
        packet = self.packetizer.make_data_packet(seq, data)
        self.sock.sendto(packet, self.dest)
        Logger.debug(who=self.sock.getsockname(), message=f"[GBN] Sent seq={seq}")
        timer = threading.Timer(self.timeout, self._timeout, args=(seq,))
        self.timers[seq] = timer

    def _timeout(self, seq):
        with self.lock:
            Logger.debug(who=self.sock.getsockname(), message=f"[GBN] Timeout seq={seq}, retransmitting window")
            for s in range(self.base, min(self.base + self.window_size, self.total_packets)):
                if s in self.timers:
                    self.timers[s].cancel()
                self._send_packet(s)

    def _receive_acks(self):
        while True:
            try:
                packet, _ = self.sock.recvfrom(2048)
                if self.packetizer.is_ack(packet):
                    ack_seq = self.packetizer.extract_seq(packet)
                    Logger.debug(who=self.sock.getsockname(), message=f"[GBN] Received ACK seq={ack_seq}")
                    with self.lock:
                        if ack_seq >= self.base:
                            for s in range(self.base, ack_seq + 1):
                                if s in self.timers:
                                    self.timers[s].cancel()
                                    del self.timers[s]
                            self.base = ack_seq + 1
                            while self.next_seq < self.base + self.window_size and self.next_seq < self.total_packets:
                                self._send_packet(self.next_seq)
                                self.next_seq += 1
                            if self.base == self.total_packets:
                                self.ack_event.set()
                                return
            except socket.timeout:
                continue

    def close(self):
        for t in self.timers.values():
            t.cancel()
        self.sock.close()
        Logger.debug(who=self.dest, message="Socket closed.")


class GoBackNReceiver:
    def __init__(self, sock: socket.socket, output_path: str, packetizer: Packetizer=None, timeout: float=1.0):
        self.sock = sock
        self.output_path = output_path
        self.packetizer = packetizer or DefaultPacketizer()
        self.timeout = timeout
        self.expected_seq = 0
        self.running = True
        self.sock.settimeout(timeout + 0.1)
        Logger.debug(who=self.sock.getsockname(), message=f"GBN Receiver init, output: {output_path}")

    def start(self):
        Logger.info("[GBN-Receiver] Receiver started.")
        with open(self.output_path, 'wb') as f:
            while self.running:
                try:
                    packet, addr = self.sock.recvfrom(2048)
                    if self.packetizer.is_data(packet):
                        seq = self.packetizer.extract_seq(packet)
                        Logger.debug(who=self.sock.getsockname(), message=f"[GBN-Receiver] Received DATA seq={seq} from {addr}")
                        if seq == self.expected_seq:
                            data = self.packetizer.extract_data(packet)
                            f.write(data); self.expected_seq += 1
                            Logger.debug(who=self.sock.getsockname(), message=f"[GBN-Receiver] Written DATA seq={seq}")
                        else:
                            Logger.debug(who=self.sock.getsockname(), message="[GBN-Receiver] Unexpected seq, ignored.")
                        ack = self.packetizer.make_ack_packet(seq)
                        self.sock.sendto(ack, addr)
                        Logger.debug(who=self.sock.getsockname(), message=f"[GBN-Receiver] Sent ACK seq={seq} to {addr}")
                    elif self.packetizer.is_terminate(packet):
                        Logger.info("[GBN-Receiver] Received terminate.")
                        self.running = False
                except socket.timeout:
                    continue
        Logger.info(f"[GBN-Receiver] File saved to {self.output_path}")
    
    def close(self):
        self.sock.close()
        Logger.debug(
            who=self.sock.getsockname(),
            message=f"[GBN-Receiver] Socket closed for output {self.output_path}"
        )