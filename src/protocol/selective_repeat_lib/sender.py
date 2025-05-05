import time
import socket
import threading
from utils import FileReader, Logger
from protocol.packet import Packetizer
from .utils import TimerManager, PacketSender
from .window import SelectiveRepeatWindow
from .ack_reciever import AckReceiver


class SelectiveRepeatSender:
    def __init__(self, sock: socket.socket, dest: tuple, file_path: str,
                 packetizer: Packetizer = None, timeout: float = 10.0, window_size: int = 4):
        self.sock = sock
        self.dest = dest
        self.timeout = timeout
        self.sock.settimeout(timeout + 0.1)

        file_reader = FileReader(file_path)
        self.packets = list(file_reader.read_chunks(chunk_size=1024))
        self.total = len(self.packets)
        
        self.packetizer = packetizer
        self.timer_manager = TimerManager()
        self.window = SelectiveRepeatWindow(window_size, self.total)
        self.send_event = threading.Event()
        self.packet_sender = PacketSender(sock, dest, packetizer)
        self.ack_receiver = AckReceiver(sock, packetizer, self.timer_manager, self.window, self.send_event)
        self._running = True
        
        self.send_condition = threading.Condition()
        
        Logger.debug(who=self.sock.getsockname(), message=f"SR-Sender init for {dest}, win:{window_size}")

    def start(self) -> None:
        Logger.info(f"[SR-Sender] Starting transfer to {self.dest}")
        self.ack_receiver.start(self._send_next)
        while self._running and not self.window.is_complete():
            with self.send_condition:
                if self.window.can_send():
                    self._send(self.window.get_next_seq())
                    self.window.increment_next_seq()
                else:
                    self.send_condition.wait(timeout=0.01)  # Wait for ACKs
        if self.window.is_complete():
            self.packet_sender.send_terminate()
            Logger.info("[SR-Sender] Transfer completed.")
        self.close()

    def _send_next(self) -> None:
        if not self._running:
            return
        with self.window.lock:
            for seq in range(self.window.base, min(self.window.base + self.window.window_size, self.total)):
                if not self.window.is_packet_acked(seq):
                    self._send(seq)
                    with self.send_condition:
                        self.send_condition.notify()  # Notify sender to retry
                    return
            if self.window.can_send():
                self._send(self.window.get_next_seq())
                self.window.increment_next_seq()
                with self.send_condition:
                    self.send_condition.notify()

    def _send(self, seq: int) -> None:
        if self._running and seq < self.total:
            Logger.debug(who=self.sock.getsockname(), message=f"[SR-Sender] Sent seq={seq}")
            self.packet_sender.send_packet(seq, self.packets[seq])
            self.timer_manager.start_timer(seq, self.timeout, lambda: self._timeout(seq))

    def _timeout(self, seq: int) -> None:
        if self._running and not self.window.is_packet_acked(seq):
            Logger.debug(who=self.sock.getsockname(), message=f"[SR-Sender] Timeout seq={seq}, retransmitting")
            self._send(seq)

    def close(self) -> None:
        self._running = False
        self.ack_receiver.stop()
        self.timer_manager.cancel_all()
        self.send_event.set()
        try:
            self.sock.close()
        except OSError:
            pass
        Logger.debug(who=self.dest, message="[SR-Sender] Socket closed.")