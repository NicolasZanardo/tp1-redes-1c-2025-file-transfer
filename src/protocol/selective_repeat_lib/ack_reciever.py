import socket
import threading
from utils import Logger
from protocol.packet import Packetizer
from .utils import TimerManager
from .window import SelectiveRepeatWindow

class AckReceiver:
    def __init__(self, sock: socket.socket, packetizer: Packetizer, timer_manager: TimerManager,
                 window: SelectiveRepeatWindow, send_event: threading.Event):
        self.sock = sock
        self.packetizer = packetizer
        self.timer_manager = timer_manager
        self.window = window
        self.send_event = send_event
        self._running = True

    def start(self, send_callback: callable) -> None:
        self._thread = threading.Thread(target=self._receive_acks, args=(send_callback,), daemon=True)
        self._thread.start()

    def _receive_acks(self, send_callback: callable) -> None:
        while self._running:
            try:
                packet, _ = self.sock.recvfrom(2048)
                if not self._running:
                    break
                if self.packetizer.is_ack(packet):
                    stop_running = self._process_acks(packet, send_callback)
                    if (stop_running):
                        break
            except socket.timeout:
                continue
            except OSError:
                break

    def _process_acks(self, packet, send_callback):
        seq = self.packetizer.extract_seq(packet)
        Logger.debug(who=self.sock.getsockname(), message=f"[SR-AckReceiver] Received ACK seq={seq}")
        if self.window.is_within_window(seq):
            self.window.mark_acked(seq)
            self.timer_manager.cancel_timer(seq)
            old_base = self.window.base
            self.window.advance_window()
            if self.window.base > old_base:  # Call only on window advance
                send_callback()
            if self.window.is_complete():
                self._running = False
                self.send_event.set()
                return True
        return False

    def stop(self) -> None:
        self._running = False
        self.send_event.set()
        if hasattr(self, '_thread'):
            self._thread.join(timeout=1.0)