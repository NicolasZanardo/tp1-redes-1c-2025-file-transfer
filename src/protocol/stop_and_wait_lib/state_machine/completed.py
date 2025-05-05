from utils.logger import Logger
from .base import SWState

class CompletedState(SWState):
    def on_enter(self):
        terminator = self.ctx.packetizer.make_terminate_packet()
        self.ctx.sock.sendto(terminator, self.ctx.dest)
        Logger.info(f"[SW] Transfer completed to {self.ctx.dest}")
        self.ctx.close()
