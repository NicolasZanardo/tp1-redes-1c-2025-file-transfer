import socket
from protocol.packet import DefaultPacketizer
from utils import Logger

class StopAndWaitReceiver:
    def __init__(self, sock: socket.socket, output_path: str, packetizer=None, timeout: float = 1.0):
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
                    Logger.debug(who=self.sock.getsockname(), message=f"[SW-Receiver] Raw packet received from {addr}: {packet!r}")
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
        try:
            self.sock.close()
        except OSError:
            pass
        Logger.debug(message=f"[SW-Receiver] Socket closed for output {self.output_path}")
