import unittest
import threading
import socket
import time
from unittest.mock import patch, MagicMock, mock_open
from protocol.selective_repeat import SelectiveRepeatProtocol, SelectiveRepeatReceiver
from utils import Logger

class TestSelectiveRepeatReceive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.setup_name("test/test_sr_protocol_recieve.py")

    @classmethod
    def tearDownClass(cls):
        print("\n----------------------------------------")
        print("----------------------------------------\n")

    def setUp(self):
        print('')

    @patch("protocol.selective_repeat.DefaultPacketizer")
    @patch("protocol.selective_repeat.SelectiveRepeatProtocol._file_reader", return_value=[b'x'])
    def test_ack_advances_window(self, mock_reader, mock_packetizer_cls):
        mock_packetizer = MagicMock()
        mock_packetizer.is_ack.return_value = True
        mock_packetizer.extract_seq.return_value = 0
        mock_packetizer_cls.return_value = mock_packetizer

        sock = MagicMock(spec=socket.socket)
        sock.recvfrom.side_effect = [
            (b'ack0', ("remote", 1234)), 
            socket.timeout()
        ]

        protocol = SelectiveRepeatProtocol(sock, ("remote", 1234), "f", packetizer=mock_packetizer)
        protocol.acked = {0: False}
        protocol.total = 1
        protocol.base = 0
        timer = MagicMock()
        protocol.timers = {0: timer}
        protocol.running = True  # Ensure it's running

        recv_thread = threading.Thread(target=protocol._receive_acks)
        recv_thread.start()

        # Allow time for recvfrom to be called and processed
        time.sleep(0.125)
        protocol.close()
        recv_thread.join(timeout=1)  # Wait for thread to end

        self.assertEqual(protocol.base, 1)
        self.assertTrue(protocol.send_event.is_set())
        timer.cancel.assert_called_once()


    @patch("builtins.open", new_callable=mock_open)
    @patch("protocol.selective_repeat.DefaultPacketizer")
    def test_receiver_receives_data(self, mock_packetizer_cls, mock_file):
        sock = MagicMock(spec=socket.socket)
        mock_packetizer = MagicMock()
        mock_packetizer_cls.return_value = mock_packetizer

        mock_packetizer.is_data.side_effect = [True, False]
        mock_packetizer.extract_seq.return_value = 0
        mock_packetizer.extract_data.return_value = b"hello"
        mock_packetizer.is_terminate.return_value = False
        mock_packetizer.make_ack_packet.return_value = b"ack"

        sock.recvfrom.side_effect = [(b'pkt', ("peer", 1234)), socket.timeout(), KeyboardInterrupt]

        receiver = SelectiveRepeatReceiver(sock, "file", packetizer=mock_packetizer)
        receiver.running = True
    
        try:
            receiver.start()
        except KeyboardInterrupt:
            pass

        receiver.running = False
        if hasattr(receiver, 'thread'):
            receiver.thread.join(timeout=1)


        mock_file().write.assert_called_with(b"hello")
        sock.sendto.assert_called_with(b"ack", ("peer", 1234))
