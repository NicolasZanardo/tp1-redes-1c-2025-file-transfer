import unittest
import tempfile
from unittest.mock import Mock, patch, call, MagicMock

from src.utils import FileChunkReader, Logger
from src.protocol.packet import DefaultPacketizer
from src.protocol.stop_and_wait_lib import StopAndWaitProtocol, StopAndWaitReceiver


class TestStopAndWaitProtocol(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.setup_name("test/test_protocol.py")

    @classmethod
    def tearDownClass(cls):
        print("\n----------------------------------------")
        print("----------------------------------------\n")

    def setUp(self):
        # Setup mock socket
        self.sock = Mock()
        self.dest = ('127.0.0.1', 5001)
        self.packetizer = DefaultPacketizer()
        self.data_chunks = [b"chunk1", b"chunk2"]
        self.reader = iter(self.data_chunks)
        print('')
    
    def test_sender_transfers_all_chunks_and_terminates(self):
        
        # Patch socket sendto
        sock = Mock()
        sock.getsockname.return_value = self.dest
        sock.recvfrom.side_effect = [
            (self.packetizer.make_ack_packet(0), self.dest),
            (self.packetizer.make_ack_packet(1), self.dest)
        ]

        sender = None
        with tempfile.NamedTemporaryFile(delete=False) as input_file:
            sender = StopAndWaitProtocol(sock=sock, dest=self.dest, file_path=input_file.name, packetizer=self.packetizer)
        sender.reader = iter(self.data_chunks)  # Replace reader
        sender.start()

        # Should have sent 2 data packets and 1 terminate
        expected_calls = [
            call(self.packetizer.make_data_packet(0, b"chunk1"), self.dest),
            call(self.packetizer.make_data_packet(1, b"chunk2"), self.dest),
            call(self.packetizer.make_terminate_packet(), self.dest)
        ]
        sock.sendto.assert_has_calls(expected_calls, any_order=False)

    def test_receiver_receives_and_writes_correctly(self):
        # Prepare mock socket
        sock = Mock()
        sock.recvfrom.side_effect = [
            (self.packetizer.make_data_packet(0, b"abc"), ('client', 12345)),
            (self.packetizer.make_data_packet(1, b"def"), ('client', 12345)),
            (self.packetizer.make_terminate_packet(), ('client', 12345)),
        ]

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            receiver = StopAndWaitReceiver(sock=sock, output_path="output.txt", packetizer=self.packetizer)
            receiver.start()

            # Check file writes
            handle = mock_file()
            handle.write.assert_has_calls([call(b"abc"), call(b"def")])

            # Check ACKs sent
            ack_calls = [
                call(self.packetizer.make_ack_packet(0), ('client', 12345)),
                call(self.packetizer.make_ack_packet(1), ('client', 12345))
            ]
            sock.sendto.assert_has_calls(ack_calls, any_order=False)

    def test_receiver_ignores_duplicate_packets(self):
        sock = Mock()
        # Two packets with the same seq
        sock.recvfrom.side_effect = [
            (self.packetizer.make_data_packet(0, b"abc"), ('client', 12345)),
            (self.packetizer.make_data_packet(0, b"abc"), ('client', 12345)),
            (self.packetizer.make_terminate_packet(), ('client', 12345)),
        ]

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            receiver = StopAndWaitReceiver(sock=sock, output_path="output.txt", packetizer=self.packetizer)
            receiver.start()

            handle = mock_file()
            handle.write.assert_called_once_with(b"abc")  # Only one write

            # Should have sent ACK for same seq twice
            sock.sendto.assert_has_calls([
                call(self.packetizer.make_ack_packet(0), ('client', 12345)),
                call(self.packetizer.make_ack_packet(0), ('client', 12345))
            ])
