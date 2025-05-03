from abc import ABC, abstractmethod
import socket
import threading
from protocol.packet import Packetizer, DefaultPacketizer
from utils.logger import Logger

class SWState(ABC):
    def __init__(self, ctx):
        self.ctx = ctx

    @abstractmethod
    def on_enter(self):
        pass

class IdleState(SWState):
    def on_enter(self):
        Logger.debug(who=self.ctx.sock.getsockname(), message="[SW] Idle: preparing message.")
        self.ctx.transition('sending')

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
            # recv timeout handled by timer
            pass

    def _on_timeout(self):
        Logger.debug(who=self.ctx.sock.getsockname(), message=f"[SW] Timeout seq={self.ctx.seq}, resending")
        self.ctx.transition('sending')

class CompletedState(SWState):
    def on_enter(self):
        terminator = self.ctx.packetizer.make_terminate_packet()
        self.ctx.sock.sendto(terminator, self.ctx.dest)
        Logger.info(f"[SW] Transfer completed to {self.ctx.dest}")
        self.ctx.close()

class StopAndWaitProtocol:
    def __init__(self, sock: socket.socket, dest: tuple, file_path: str,
                 packetizer: Packetizer = None, timeout: float = 10.0):
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
        Logger.debug(who=self.sock.getsockname(), message=f"StopAndWaitProtocol initialized for {dest}, file: {file_path}")

    def _file_reader(self, chunk_size: int = 1024):
        with open(self.file_path, 'rb') as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                yield data

    def start(self):
        Logger.info(f"[SW] Starting transfer to {self.dest}")
        self.current_state.on_enter()

    def transition(self, state: str):
        Logger.debug(who=self.sock.getsockname(), message=f"[SW] Transitioning to state: {state}")
        self.current_state = self.states[state]
        self.current_state.on_enter()

    def close(self):
        self.sock.close()
        Logger.debug(who=self.dest, message="Socket closed.")

class StopAndWaitReceiver:
    def __init__(self, sock: socket.socket, output_path: str, packetizer: Packetizer = None, timeout: float = 1.0):
        self.sock = sock
        self.output_path = output_path
        self.packetizer = packetizer or DefaultPacketizer()
        self.timeout = timeout
        self.expected_seq = 0
        self.running = True
        self.sock.settimeout(timeout + 0.1)
        Logger.debug(who=self.sock.getsockname(), message=f"StopAndWaitReceiver initialized, output: {output_path}")

    def start(self):
        Logger.info("[SW-Receiver] Receiver started.")
        with open(self.output_path, 'wb') as f:
            while self.running:
                try:
                    packet, addr = self.sock.recvfrom(2048)
                    Logger.debug(
                        who=self.sock.getsockname(),
                        message=f"[SW-Receiver] Raw packet received from {addr}: {packet!r}"
)
                    if self.packetizer.is_data(packet):
                        seq = self.packetizer.extract_seq(packet)
                        Logger.debug(who=self.sock.getsockname(), message=f"[SW-Receiver] Received DATA seq={seq} from {addr}")

                        if seq == self.expected_seq:
                            data = self.packetizer.extract_data(packet)
                            f.write(data)
                            self.expected_seq ^= 1
                            Logger.debug(who=self.sock.getsockname(), message=f"[SW-Receiver] Written DATA seq={seq}")
                        else:
                            Logger.debug(who=self.sock.getsockname(), message="[SW-Receiver] Duplicate/out-of-order packet ignored.")

                        ack = self.packetizer.make_ack_packet(seq)
                        self.sock.sendto(ack, addr)
                        Logger.debug(who=self.sock.getsockname(), message=f"[SW-Receiver] Sent ACK seq={seq} to {addr}")

                    elif self.packetizer.is_terminate(packet):
                        Logger.info("[SW-Receiver] Received terminate signal.")
                        self.running = False

                except socket.timeout:
                    continue

        Logger.info(f"[SW-Receiver] File received and saved to {self.output_path}")
        
    def close(self):
        self.sock.close()
        Logger.debug(
            who=self.sock.getsockname(),
            message=f"[SW-Receiver] Socket closed for output {self.output_path}"
        )
