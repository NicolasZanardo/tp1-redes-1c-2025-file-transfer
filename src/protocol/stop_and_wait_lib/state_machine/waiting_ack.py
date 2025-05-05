import threading
import socket
from utils.logger import Logger
from .base import SWState

class WaitingAckState(SWState):
    def on_enter(self):
        timer = threading.Timer(self.ctx.timeout, self._on_timeout)
        timer.start()
        try:
            packet, _ = self.ctx.sock.recvfrom(2048)
            timer.cancel()
            if self.ctx.packetizer.is_ack(packet):
                ack_seq = self.ctx.packetizer.extract_seq(packet)
                Logger.debug(who=self.ctx.sock.getsockname(), message=f"[SW] received ACK seq={ack_seq}")
                if ack_seq == self.ctx.seq:
                    self.ctx.seq ^= 1
                    self.ctx.transition('sending')
                else:
                    Logger.debug(who=self.ctx.sock.getsockname(), message="[SW] unexpected ACK, resending")
                    self.ctx.transition('sending')
            else:
                Logger.debug(who=self.ctx.sock.getsockname(), message="[SW] non-ACK packet received, ignored")
                self.ctx.transition('waiting_ack')
        except socket.timeout:
            pass

    def _on_timeout(self):
        Logger.debug(who=self.ctx.sock.getsockname(), message=f"[SW] Timeout seq={self.ctx.seq}, resending")
        self.ctx.transition('sending')
