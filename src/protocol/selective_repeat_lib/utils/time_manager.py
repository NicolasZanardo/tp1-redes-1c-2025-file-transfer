import threading
from typing import Callable, Dict

class TimerManager:
    def __init__(self):
        self.timers: Dict[int, threading.Timer] = {}

    def start_timer(self, seq: int, timeout: float, callback: Callable[[], None]) -> None:
        timer = threading.Timer(timeout, callback)
        self.timers[seq] = timer
        timer.start()

    def cancel_timer(self, seq: int) -> None:
        if seq in self.timers:
            self.timers[seq].cancel()
            del self.timers[seq]

    def cancel_all(self) -> None:
        for timer in self.timers.values():
            timer.cancel()
        self.timers.clear()