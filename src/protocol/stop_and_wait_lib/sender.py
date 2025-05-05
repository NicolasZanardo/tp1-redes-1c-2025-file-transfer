import socket
from utils import Logger
from utils.file_handler import FileChunkReader

from protocol.packet import DefaultPacketizer
from .state_machine import *

class StopAndWaitProtocol:
    def __init__(self, sock: socket.socket, dest: tuple, file_path: str,
                 packetizer=None, timeout: float = 10.0):
        self.sock = sock
        self.dest = dest
        self.file_path = file_path
        self.reader = FileChunkReader(self.file_path)
        self.timeout = timeout
        self.seq = 0
        self.packetizer = packetizer or DefaultPacketizer()
        self.states = {
            'idle': IdleState(self),
            'sending': SendingState(self),
            'waiting_ack': WaitingAckState(self),
            'completed': CompletedState(self),
        }
        self.current_state = self.states['idle']
        self.sock.settimeout(self.timeout + 0.1)
        Logger.debug(who=self.sock.getsockname(), message=f"StopAndWaitProtocol initialized for {dest}, file: {file_path}")

    def start(self):
        Logger.info(f"[SW] Starting transfer to {self.dest}")
        self.current_state.on_enter()

    def transition(self, state: str):
        Logger.debug(who=self.sock.getsockname(), message=f"[SW] Transitioning to state: {state}")
        self.current_state = self.states[state]
        self.current_state.on_enter()

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass
        Logger.debug(who=self.dest, message="Socket closed.")
