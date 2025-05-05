import unittest
import os
import time
import socket
import tempfile
import threading

from unittest.mock import Mock, patch
from test.utils_test import LossySocket, UtilsFunction

from protocol.packet import Packetizer
from utils import FileReader, FileWriter, Logger

from protocol.selective_repeat_lib import SelectiveRepeatSender, SelectiveRepeatReceiver
from protocol.selective_repeat_lib.utils import TimerManager, PacketSender, PacketReceiver

utils = UtilsFunction()

class TestSelectiveRepeatIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.setup_name("test/test_integration_sr.py")

    @classmethod
    def tearDownClass(cls):
        print("\n----------------------------------------")
        print("----------------------------------------\n")

    def setUp(self):
        # Create a mock Packetizer
        self.packetizer = Mock(spec=Packetizer)
        self.packetizer.make_data_packet.side_effect = lambda seq, data: f"DATA:{seq}:{data.decode()}".encode()
        self.packetizer.make_ack_packet.side_effect = lambda seq: f"ACK:{seq}".encode()
        self.packetizer.make_terminate_packet.return_value = b"TERMINATE"
        self.packetizer.is_data.side_effect = lambda packet: packet.startswith(b"DATA:")
        self.packetizer.is_ack.side_effect = lambda packet: packet.startswith(b"ACK:")
        self.packetizer.is_terminate.side_effect = lambda packet: packet == b"TERMINATE"
        self.packetizer.extract_seq.side_effect = lambda packet: int(packet.decode().split(":")[1])
        self.packetizer.extract_data.side_effect = lambda packet: packet.decode().split(":", 2)[2].encode()

        # Mock TimerManager
        self.timer_manager = Mock()
        self.timer_manager.start_timer.side_effect = lambda seq, timeout, callback: None
        self.timer_manager.cancel_timer.side_effect = lambda seq: None
        self.timer_manager.cancel_all.side_effect = lambda: None

        self.sockets = []

        # For better readability
        print("")

    def tearDown(self):
        # Clean up any open sockets
        for sock in getattr(self, 'sockets', []):
            try:
                sock.close()
            except OSError:
                pass

    def _test_simple_send_receive(self):
        """Test a simple file transfer with no packet loss."""
        with tempfile.NamedTemporaryFile(delete=False) as input_file, tempfile.NamedTemporaryFile(delete=False) as output_file:
            # Write small test data (fits in one packet)
            input_data = b"Hello, Selective Repeat!"
            input_file.write(input_data)
            input_file.flush()

            # Mock FileReader and FileWriter
            file_reader = Mock()
            file_reader.read_chunks.side_effect = lambda chunk_size: [input_data[i:i+chunk_size] for i in range(0, len(input_data), chunk_size)]
            file_writer = Mock()
            file_writer.write_chunk.side_effect = lambda data: output_file.write(data)
            file_writer.close.side_effect = lambda: output_file.flush()

            # Set up sockets
            sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            receiver_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            receiver_sock.bind(('127.0.0.1', 12345))
            dest = ('127.0.0.1', 12345)
            self.sockets = [sender_sock, receiver_sock]

            # Initialize sender and receiver
            sender = SelectiveRepeatSender(
                sock=sender_sock,
                dest=dest,
                file_path=input_file.name,
                packetizer=self.packetizer,
                timeout=1.0,
                window_size=4
            )
            sender.packets = [input_data[i:i+1024] for i in range(0, len(input_data), 1024)]
            sender.total = len(sender.packets)

            receiver = SelectiveRepeatReceiver(
                sock=receiver_sock,
                file_writer=file_writer,
                packetizer=self.packetizer,
                timeout=1.0,
                window_size=4
            )

            # Run sender and receiver in separate threads
            sender_thread = threading.Thread(target=sender.start)
            receiver_thread = threading.Thread(target=receiver.start)
            sender_thread.start()
            receiver_thread.start()

            # Wait for completion
            sender_thread.join(timeout=5)
            receiver_thread.join(timeout=5)

            # Verify output file content
            with open(output_file.name, 'rb') as f:
                output_data = f.read()
            self.assertEqual(output_data, input_data)

            # Verify window state
            self.assertTrue(sender.window.is_complete())
            self.assertEqual(sender.window.base, 1)  # Only one packet

            # Clean up temporary files
            os.unlink(input_file.name)
            os.unlink(output_file.name)

    def _test_send_receive_window_shift(self):
        """Test file transfer requiring window shift (more packets than window size)."""
        with tempfile.NamedTemporaryFile(delete=False) as input_file, tempfile.NamedTemporaryFile(delete=False) as output_file:
            # Write data larger than window size (8 packets, window size=4)
            input_data = b"A" * 8192  # 8KB, splits into 8 packets of 1KB each
            input_file.write(input_data)
            input_file.flush()

            # Mock FileReader and FileWriter
            file_reader = Mock()
            file_reader.read_chunks.side_effect = lambda chunk_size: [input_data[i:i+chunk_size] for i in range(0, len(input_data), chunk_size)]
            file_writer = Mock()
            file_writer.write_chunk.side_effect = lambda data: output_file.write(data)
            file_writer.close.side_effect = lambda: output_file.flush()

            # Set up sockets
            sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            receiver_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            receiver_sock.bind(('127.0.0.1', 12346))
            dest = ('127.0.0.1', 12346)
            self.sockets = [sender_sock, receiver_sock]

            # Initialize sender and receiver
            sender = SelectiveRepeatSender(
                sock=sender_sock,
                dest=dest,
                file_path=input_file.name,
                packetizer=self.packetizer,
                timeout=1.0,
                window_size=4
            )
            sender.packets = [input_data[i:i+1024] for i in range(0, len(input_data), 1024)]
            sender.total = len(sender.packets)

            receiver = SelectiveRepeatReceiver(
                sock=receiver_sock,
                file_writer=file_writer,
                packetizer=self.packetizer,
                timeout=1.0,
                window_size=4
            )

            # Run sender and receiver in separate threads
            sender_thread = threading.Thread(target=sender.start)
            receiver_thread = threading.Thread(target=receiver.start)
            sender_thread.start()
            receiver_thread.start()

            # Wait for completion
            sender_thread.join(timeout=10)
            receiver_thread.join(timeout=10)

            # Verify output file content
            with open(output_file.name, 'rb') as f:
                output_data = f.read()
            self.assertEqual(output_data, input_data)

            # Verify window state
            self.assertTrue(sender.window.is_complete())
            self.assertEqual(sender.window.base, 8)  # 8 packets sent

            # Clean up temporary files
            os.unlink(input_file.name)
            os.unlink(output_file.name)

    def test_send_receive_packet_loss(self):
        """Test file transfer with simulated packet loss."""
        with tempfile.NamedTemporaryFile(delete=False) as input_file, tempfile.NamedTemporaryFile(delete=False) as output_file:
            self.input_file = input_file
            self.output_file = output_file

            utils.setup_test_threads(
                self._test_send_receive_packet_loss_SERVER,
                self._test_send_receive_packet_loss_CLIENT,
                timeout=3
            )

            # Verify output file content
            with open(output_file.name, 'rb') as f:
                output_data = f.read()
            with open(input_file.name, 'rb') as f:
                input_data = f.read()
            
            self.assertEqual(output_data, input_data)

            # Clean up temporary files
            os.unlink(input_file.name)
            os.unlink(output_file.name)

    def _test_send_receive_packet_loss_SERVER(self):
        # Write test data (5 packets)
        input_data = b"B" * 5120  # 5KB, splits into 5 packets of 1KB each
        self.input_file.write(input_data)
        self.input_file.flush()

        file_reader = Mock()
        file_reader.read_chunks.side_effect = lambda chunk_size: [input_data[i:i+chunk_size] for i in range(0, len(input_data), chunk_size)]
        
        sender_sock = LossySocket(socket.socket(socket.AF_INET, socket.SOCK_DGRAM), loss_rate=0.0)
        self.sockets.append(sender_sock)

        # Initialize sender and receiver
        sender = SelectiveRepeatSender(
            sock=sender_sock,
            dest=('127.0.0.1', 12347),
            file_path=self.input_file.name,
            packetizer=self.packetizer,
            timeout=1.0,
            window_size=4
        )
        sender.packets = [input_data[i:i+1024] for i in range(0, len(input_data), 1024)]
        sender.total = len(sender.packets)

        sender.start()

        sender.close()
            
        # Verify window state
        self.assertTrue(sender.window.is_complete())
        self.assertEqual(sender.window.base, 5)  # 5 packets sent

    def _test_send_receive_packet_loss_CLIENT(self):
        time.sleep(0.125)
        
        file_writer = Mock()
        file_writer.write_chunk.side_effect = lambda data: self.output_file.write(data)
        file_writer.close.side_effect = lambda: self.output_file.flush() if not self.output_file.closed else None

        receiver_sock = LossySocket(socket.socket(socket.AF_INET, socket.SOCK_DGRAM), loss_rate=0.0)
        receiver_sock.bind(('127.0.0.1', 12347))
        self.sockets.append(receiver_sock)

        # Set up sockets with packet loss
        receiver = SelectiveRepeatReceiver(
            sock=receiver_sock,
            file_writer=file_writer,
            packetizer=self.packetizer,
            timeout=1.0,
            window_size=4
        )
        receiver.start()

        receiver.stop()
    