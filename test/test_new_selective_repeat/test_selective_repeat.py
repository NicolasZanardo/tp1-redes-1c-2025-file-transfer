import unittest
import socket
import threading
import time
import tempfile
import os
from unittest.mock import Mock, patch
from test.utils_test import UtilsFunction

from utils import Logger
from protocol.packet import DefaultPacketizer

from protocol.selective_repeat_lib.window import SelectiveRepeatWindow
from protocol.selective_repeat_lib.sender import SelectiveRepeatSender
from protocol.selective_repeat_lib.reciever import SelectiveRepeatReceiver
from protocol.selective_repeat_lib.ack_reciever import AckReceiver

utils = UtilsFunction()

class TestSelectiveRepeatProtocol(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.setup_name("test/test_selective_repeat.py")

    @classmethod
    def tearDownClass(cls):
        print("\n----------------------------------------")
        print("----------------------------------------\n")

    def setUp(self):
        # Create a mock Packetizer
        self.packetizer = DefaultPacketizer()

        # Mock TimerManager
        self.timer_manager = Mock()
        self.timer_manager.start_timer.side_effect = lambda seq, timeout, callback: None
        self.timer_manager.cancel_timer.side_effect = lambda seq: None
        self.timer_manager.cancel_all.side_effect = lambda: None
        
        # For better readability
        print("")

    def test_ack_receiver_packet_loss(self):
        # Test AckReceiver with simulated packet loss
        sock = Mock()
        sock.recvfrom.side_effect = [
            (self.packetizer.make_ack_packet(0), ('127.0.0.1', 12345)),  # ACK for seq 0
            (self.packetizer.make_ack_packet(2), ('127.0.0.1', 12345)),  # ACK for seq 2 (1 is lost)
            (self.packetizer.make_ack_packet(1), ('127.0.0.1', 12345)),  # ACK for seq 1
            (self.packetizer.make_ack_packet(3), ('127.0.0.1', 12345)),  # ACK for seq 3
        ]
        send_event = threading.Event()
        window = SelectiveRepeatWindow(window_size=4, total_packets=4)
        ack_receiver = AckReceiver(
            sock=sock,
            packetizer=self.packetizer,
            timer_manager=self.timer_manager,
            window=window,
            send_event=send_event
        )

        send_callback = Mock()
        ack_receiver.start(send_callback)

        # Wait for completion
        send_event.wait(timeout=2)

        # Verify window state
        self.assertEqual(window.base, 4)
        self.assertTrue(window.is_complete())
        self.assertEqual(send_callback.call_count, 3)  # Called for each advance after seq 0

    def test_ack_receiver_no_callback_after_completion(self):
        # Test that no callbacks are called after transfer completion
        sock = Mock()
        sock.recvfrom.side_effect = [
            (self.packetizer.make_ack_packet(0), ('127.0.0.1', 12345)),
            (self.packetizer.make_ack_packet(1), ('127.0.0.1', 12345)),
            (self.packetizer.make_ack_packet(2), ('127.0.0.1', 12345)),
            (self.packetizer.make_ack_packet(3), ('127.0.0.1', 12345)),
            (self.packetizer.make_ack_packet(3), ('127.0.0.1', 12345)),  # Duplicate ACK after completion
        ]
        send_event = threading.Event()
        window = SelectiveRepeatWindow(window_size=4, total_packets=4)
        ack_receiver = AckReceiver(
            sock=sock,
            packetizer=self.packetizer,
            timer_manager=self.timer_manager,
            window=window,
            send_event=send_event
        )

        send_callback = Mock()
        ack_receiver.start(send_callback)

        # Wait for completion
        send_event.wait(timeout=2)

        # Verify window state and callback count
        self.assertEqual(window.base, 4)
        self.assertTrue(window.is_complete())
        self.assertEqual(send_callback.call_count, 4)  # Only for seq 0, 1, 2
    
    def test_sender_receiver_integration(self):
        # Create temporary files for input and output
        with tempfile.NamedTemporaryFile(delete=False) as input_file, tempfile.NamedTemporaryFile(delete=False) as output_file:
            self.input_file = input_file
            self.output_file = output_file

            utils.setup_test_threads(
                self._test_sender_receiver_integration_SERVER,
                self._test_sender_receiver_integration_CLIENT,
                2
            )

            # Verify output file content
            with open(output_file.name, 'rb') as f:
                output_data = f.read()
            with open(input_file.name, 'rb') as f:
                input_data = f.read()

            self.assertNotEqual(output_data, b'')
            self.assertNotEqual(input_data, b'')
            self.assertEqual(output_data, input_data)

    def _test_sender_receiver_integration_SERVER(self):
        # Write test data to input file
        input_data = b"Hello, this is a test file for Selective Repeat!"
        self.input_file.write(input_data)
        self.input_file.flush()
        
        # Mock FileReader
        file_reader = Mock()
        file_reader.read_chunks.side_effect = lambda chunk_size: [input_data[i:i+chunk_size] for i in range(0, len(input_data), chunk_size)]
        
        sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dest = ('127.0.0.1', 12345)

        # Initialize sender
        sender = SelectiveRepeatSender(
            sock=sender_sock,
            dest=dest,
            file_path=self.input_file.name,
            packetizer=self.packetizer,
            timeout=1.0,
            window_size=4
        )
        sender.packets = [input_data[i:i+1024] for i in range(0, len(input_data), 1024)]
        sender.total = len(sender.packets)

        sender.start()

        # Clean up
        sender.close()

    
    def _test_sender_receiver_integration_CLIENT(self):
        # Mock FileWriter
        file_writer = Mock()
        file_writer.write_chunk.side_effect = lambda data: self.output_file.write(data)
        file_writer.close.side_effect = lambda: self.output_file.flush() if not self.output_file.closed else None

        receiver_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receiver_sock.bind(('127.0.0.1', 12345))
        
        # Initialize receiver
        receiver = SelectiveRepeatReceiver(
            sock=receiver_sock,
            file_writer=file_writer,
            packetizer=self.packetizer,
            timeout=1.0,
            window_size=4
        )

        receiver.start()

        # Clean up
        receiver.stop()
