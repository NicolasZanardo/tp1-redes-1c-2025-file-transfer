from utils.logger import Logger
from .base import SWState

class IdleState(SWState):
    def on_enter(self):
        Logger.debug(who=self.ctx.sock.getsockname(), message="[SW] Idle: preparing message.")
        self.ctx.transition('sending')
