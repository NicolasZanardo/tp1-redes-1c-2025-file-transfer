from utils.logger import Logger
from .base import SWState

class SendingState(SWState):
    def on_enter(self):
        try:
            chunk = next(self.ctx.reader)
        except StopIteration:
            self.ctx.transition('completed')
            return

        packet = self.ctx.packetizer.make_data_packet(self.ctx.seq, chunk)
        self.ctx.sock.sendto(packet, self.ctx.dest)
        Logger.debug(who=self.ctx.sock.getsockname(), message=f"[SW] sent seq={self.ctx.seq}, {len(chunk)} bytes")
        self.ctx.transition('waiting_ack')
