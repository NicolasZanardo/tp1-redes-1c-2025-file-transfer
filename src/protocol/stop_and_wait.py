from abc import ABC, abstractmethod
import socket
import threading
from protocol.packet import Packetizer, DefaultPacketizer

class SWState(ABC):
    def __init__(self, ctx):
        self.ctx = ctx

    @abstractmethod
    def on_enter(self):
        pass

class IdleState(SWState):
    def on_enter(self):
        print("[SW] Idle: preparing message.")
        self.ctx.transition('sending')

class SendingState(SWState):
    def on_enter(self):
        try:
            chunk = next(self.ctx.reader)
        except StopIteration:
            self.ctx.transition('finished')
            return
        packet = self.ctx.packetizer.make_data_packet(self.ctx.seq, chunk)
        self.ctx.sock.sendto(packet, self.ctx.dest)
        print(f"[SW] sent seq={self.ctx.seq}, {len(chunk)} bytes")
        self.ctx.transition('waiting_ack')

class WaitingAckState(SWState):
    def on_enter(self):
        timer = threading.Timer(self.ctx.timeout, self._on_timeout)
        timer.start()
        try:
            packet, _ = self.ctx.sock.recvfrom(2048)
            timer.cancel()
            if self.ctx.packetizer.is_ack(packet):
                ack_seq = self.ctx.packetizer.extract_seq(packet)
                print(f"[SW] recieved ACK seq={ack_seq}")
                if ack_seq == self.ctx.seq:
                    self.ctx.seq ^= 1
                    self.ctx.transition('sending')
                else:
                    print("[SW] unexpected ACK, resent")
                    self.ctx.transition('sending')
            else:
                print("[SW] non ACK packet recieved, ignored")
                self.ctx.transition('waiting_ack')
        except socket.timeout:
            # recv timeout simulado
            pass

    def _on_timeout(self):
        print(f"[SW] Timeout seq={self.ctx.seq}, re-sent")
        self.ctx.transition('sending')

class CompletedState(SWState):
    def on_enter(self):
        terminator = self.ctx.packetizer.make_terminate_packet()
        self.ctx.sock.sendto(terminator, self.ctx.dest)
        print("[SW] Transfer completed.")
        self.ctx.close()

class StopAndWaitProtocol:
    def __init__(self, sock: socket.socket, dest: tuple, file_path: str,
                 packetizer: Packetizer = None, timeout: float = 1.0):
        self.sock = sock
        self.dest = dest
        self.file_path = file_path
        self.timeout = timeout
        self.seq = 0
        self.reader = self._file_reader()
        self.packetizer = packetizer or DefaultPacketizer()
        self.states = {
            'idle': IdleState(self),
            'sending': SendingState(self),
            'waiting_ack': WaitingAckState(self),
            'completed': CompletedState(self),
        }
        self.current_state = self.states['idle']
        self.sock.settimeout(self.timeout + 0.1)

    def _file_reader(self, chunk_size: int = 1024):
        with open(self.file_path, 'rb') as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                yield data

    def start(self):
        self.current_state.on_enter()

    def transition(self, state: str):
        self.current_state = self.states[state]
        self.current_state.on_enter()

    def close(self):
        pass