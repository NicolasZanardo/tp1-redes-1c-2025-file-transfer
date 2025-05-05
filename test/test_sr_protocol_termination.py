import unittest
import socket
from unittest.mock import MagicMock
from protocol.selective_repeat import SelectiveRepeatProtocol, SelectiveRepeatReceiver
from utils import Logger

class TestTermination(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.setup_name("test/test_sr_protocol_termination.py")

    @classmethod
    def tearDownClass(cls):
        print("\n----------------------------------------")
        print("----------------------------------------\n")

    def setUp(self):
        print('')

    def test_sender_sends_terminate(self):
        sock = MagicMock(spec=socket.socket)
        pktzr = MagicMock()
        pktzr.make_terminate_packet.return_value = b'term'

        sr = SelectiveRepeatProtocol(sock, ("1.1.1.1", 1234), "file", packetizer=pktzr)
        sr._send = lambda s: None
        sr.packets = [b'x']
        sr.total = 1
        sr._receive_acks = lambda: sr.send_event.set()

        sr.start()
        sock.sendto.assert_called_with(b'term', ("1.1.1.1", 1234))

    def test_receiver_handles_terminate(self):
        sock = MagicMock(spec=socket.socket)
        pktzr = MagicMock()
        pktzr.is_data.return_value = False
        pktzr.is_terminate.side_effect = [True]

        sock.recvfrom.side_effect = [(b'term', ("remote", 1234))]

        receiver = SelectiveRepeatReceiver(sock, "file", packetizer=pktzr)
        receiver.start()

        self.assertFalse(receiver.running)
