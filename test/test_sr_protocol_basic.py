import unittest
import socket
from unittest.mock import patch, MagicMock
from protocol.selective_repeat import SelectiveRepeatProtocol
from utils import Logger

class TestSelectiveRepeatInit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.setup_name("test/test_sr_protocol_basic.py")

    @classmethod
    def tearDownClass(cls):
        print("\n----------------------------------------")
        print("----------------------------------------\n")

    def setUp(self):
        print('')

    @patch("protocol.selective_repeat.DefaultPacketizer")
    @patch("protocol.selective_repeat.SelectiveRepeatProtocol._file_reader", return_value=[b'data1', b'data2'])
    def test_initialization(self, mock_reader, mock_packetizer):
        mock_sock = MagicMock(spec=socket.socket)
        protocol = SelectiveRepeatProtocol(mock_sock, ("127.0.0.1", 9999), "fakefile")

        self.assertEqual(protocol.base, 0)
        self.assertEqual(protocol.next_seq, 0)
        self.assertEqual(protocol.total, 2)
        self.assertIsInstance(protocol.packetizer, mock_packetizer.return_value.__class__)
        mock_sock.settimeout.assert_called_once()

    @patch("protocol.selective_repeat.DefaultPacketizer")
    @patch("protocol.selective_repeat.SelectiveRepeatProtocol._file_reader", return_value=[b'data1'])
    def test_send_starts_timer_and_sends_packet(self, mock_reader, mock_packetizer_cls):
        mock_packetizer = MagicMock()
        mock_packetizer.make_data_packet.return_value = b'pkt'
        mock_packetizer_cls.return_value = mock_packetizer

        sock = MagicMock(spec=socket.socket)
        protocol = SelectiveRepeatProtocol(sock, ("1.2.3.4", 1234), "f", timeout=1.0)
        protocol.packetizer = mock_packetizer

        protocol._send(0)
        protocol.close()

        mock_packetizer.make_data_packet.assert_called_once()
        sock.sendto.assert_called_once_with(b'pkt', ("1.2.3.4", 1234))
        self.assertIn(0, protocol.timers)