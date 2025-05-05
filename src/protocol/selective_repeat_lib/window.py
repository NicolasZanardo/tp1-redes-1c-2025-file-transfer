from threading import Lock
from typing import Dict

class SelectiveRepeatWindow:
    def __init__(self, window_size: int, total_packets: int = None):
        self.window_size = window_size
        self.total = total_packets
        self.base = 0
        self.next_seq = 0
        self.acked: Dict[int, bool] = {}
        self.lock = Lock()

    def can_send(self) -> bool:
        with self.lock:
            return (self.total is None or self.next_seq < self.total) and self.next_seq < self.base + self.window_size

    def is_complete(self) -> bool:
        with self.lock:
            return self.total is not None and self.base >= self.total

    def get_next_seq(self) -> int:
        with self.lock:
            return self.next_seq

    def increment_next_seq(self) -> None:
        with self.lock:
            if self.next_seq < self.total:
                self.next_seq += 1

    def is_packet_acked(self, seq: int) -> bool:
        with self.lock:
            return seq in self.acked and self.acked[seq]

    def mark_acked(self, seq: int) -> None:
        with self.lock:
            if 0 <= seq < self.total:
                self.acked[seq] = True

    def advance_window(self) -> None:
        with self.lock:
            while self.base < self.total and self.base in self.acked and self.acked[self.base]:
                del self.acked[self.base]
                self.base += 1

    def is_within_window(self, seq: int) -> bool:
        with self.lock:
            return self.base <= seq < self.base + self.window_size