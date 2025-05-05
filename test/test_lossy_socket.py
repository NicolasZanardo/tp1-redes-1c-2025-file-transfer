import unittest
import socket
from unittest.mock import MagicMock, patch
from utils import Logger
from test.utils_test import LossySocket, ConsistentlyLossySocket

class TestLossySocket(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.setup_name("test/test_lossy_socket.py")

    @classmethod
    def tearDownClass(cls):
        print("\n----------------------------------------")
        print("----------------------------------------\n")

    def setUp(self):
        self.mock_sock = MagicMock(spec=socket.socket)
        self.mock_sock.getsockname.return_value = ('127.0.0.1', 12345)
        self.lossy_sock = LossySocket(self.mock_sock, loss_rate=0.2)

    def tearDown(self):
        self.mock_sock.reset_mock()

    @patch('random.random')
    def test_initialization(self, mock_random):
        lossy_sock = LossySocket(self.mock_sock, loss_rate=0.5)
        self.assertEqual(lossy_sock.sock, self.mock_sock)
        self.assertEqual(lossy_sock.loss_rate, 0.5)
        self.assertEqual(lossy_sock.stored, [])

    @patch('random.random')
    @patch.object(Logger, 'debug')
    def test_sendto_no_loss(self, mock_logger, mock_random):
        mock_random.return_value = 0.9  # Greater than loss_rate (0.2)
        self.lossy_sock.sendto(b"test data", ('192.168.1.1', 54321))
        self.mock_sock.sendto.assert_called_once_with(b"test data", ('192.168.1.1', 54321))
        mock_logger.assert_not_called()

    @patch('random.random')
    @patch.object(Logger, 'debug')
    def test_sendto_loss(self, mock_logger, mock_random):
        mock_random.return_value = 0.1  # Less than loss_rate (0.2)
        self.lossy_sock.sendto(b"test data", ('192.168.1.1', 54321))
        self.mock_sock.sendto.assert_not_called()
        mock_logger.assert_called_once_with(
            who="[Lossy-Socket ('127.0.0.1', 12345)]",
            message="I didn't sent the data to ('192.168.1.1', 54321)"
        )

    @patch('random.random')
    def test_sendto_zero_loss_rate(self, mock_random):
        lossy_sock = LossySocket(self.mock_sock, loss_rate=0.0)
        mock_random.return_value = 0.0  # Any value works since loss_rate is 0
        lossy_sock.sendto(b"test data", ('192.168.1.1', 54321))
        self.mock_sock.sendto.assert_called_once_with(b"test data", ('192.168.1.1', 54321))

    @patch('random.random')
    @patch.object(Logger, 'debug')
    def test_sendto_full_loss_rate(self, mock_logger, mock_random):
        lossy_sock = LossySocket(self.mock_sock, loss_rate=1.0)
        mock_random.return_value = 0.9  # Any value works since loss_rate is 1
        lossy_sock.sendto(b"test data", ('192.168.1.1', 54321))
        self.mock_sock.sendto.assert_not_called()
        mock_logger.assert_called_once()

    @patch('random.random')
    def test_recvfrom_no_loss_no_stored(self, mock_random):
        mock_random.return_value = 0.9  # Greater than loss_rate (0.2)
        self.mock_sock.recvfrom.return_value = (b"received data", ('192.168.1.1', 54321))
        data, addr = self.lossy_sock.recvfrom(1024)
        self.assertEqual(data, b"received data")
        self.assertEqual(addr, ('192.168.1.1', 54321))
        self.mock_sock.recvfrom.assert_called_once_with(1024)
        self.assertEqual(self.lossy_sock.stored, [])

    @patch('random.random')
    @patch.object(Logger, 'debug')
    def test_recvfrom_reorder(self, mock_logger, mock_random):
        mock_random.side_effect = [0.1]  # Less than loss_rate (0.2) to trigger reordering
        self.mock_sock.recvfrom.side_effect = [
            (b"first packet", ('192.168.1.1', 54321)),
            (b"second packet", ('192.168.1.1', 54321))
        ]
        data, addr = self.lossy_sock.recvfrom(1024)
        self.assertEqual(data, b"second packet")
        self.assertEqual(addr, ('192.168.1.1', 54321))
        self.assertEqual(self.lossy_sock.stored, [(b"first packet", ('192.168.1.1', 54321))])
        mock_logger.assert_called_once_with(
            who="[Lossy-Socket ('127.0.0.1', 12345)]",
            message="I changed the order of the packets sent to ('192.168.1.1', 54321)"
        )

    @patch('random.random')
    def test_recvfrom_stored_packet(self, mock_random):
        self.lossy_sock.stored = [(b"stored packet", ('192.168.1.1', 54321))]
        data, addr = self.lossy_sock.recvfrom(1024)
        self.assertEqual(data, b"stored packet")
        self.assertEqual(addr, ('192.168.1.1', 54321))
        self.assertEqual(self.lossy_sock.stored, [])
        self.mock_sock.recvfrom.assert_not_called()

    @patch('random.random')
    def test_recvfrom_timeout_no_stored(self, mock_random):
        self.mock_sock.recvfrom.side_effect = socket.timeout("Timeout")
        with self.assertRaises(socket.timeout) as cm:
            self.lossy_sock.recvfrom(1024)
        self.assertEqual(str(cm.exception), "Simulated packet loss")
        self.mock_sock.recvfrom.assert_called_once_with(1024)
        self.assertEqual(self.lossy_sock.stored, [])

    @patch('random.random')
    def test_recvfrom_timeout_with_stored(self, mock_random):
        self.lossy_sock.stored = [(b"stored packet", ('192.168.1.1', 54321))]
        self.mock_sock.recvfrom.side_effect = socket.timeout("Timeout")
        data, addr = self.lossy_sock.recvfrom(1024)
        self.assertEqual(data, b"stored packet")
        self.assertEqual(addr, ('192.168.1.1', 54321))
        self.assertEqual(self.lossy_sock.stored, [])
        self.mock_sock.recvfrom.assert_not_called()

    def test_bind(self):
        self.lossy_sock.bind(('127.0.0.1', 54321))
        self.mock_sock.bind.assert_called_once_with(('127.0.0.1', 54321))

    def test_settimeout(self):
        self.lossy_sock.settimeout(1.0)
        self.mock_sock.settimeout.assert_called_once_with(1.0)

    def test_getsockname(self):
        result = self.lossy_sock.getsockname()
        self.assertEqual(result, ('127.0.0.1', 12345))
        self.mock_sock.getsockname.assert_called_once()

    def test_close(self):
        self.lossy_sock.close()
        self.mock_sock.close.assert_called_once()

    @patch('random.random')
    def test_sendto_empty_data(self, mock_random):
        mock_random.return_value = 0.9  # No loss
        self.lossy_sock.sendto(b"", ('192.168.1.1', 54321))
        self.mock_sock.sendto.assert_called_once_with(b"", ('192.168.1.1', 54321))

    @patch('random.random')
    def test_recvfrom_zero_bufsize(self, mock_random):
        mock_random.return_value = 0.9  # No loss
        self.mock_sock.recvfrom.return_value = (b"data", ('192.168.1.1', 54321))
        data, addr = self.lossy_sock.recvfrom(0)
        self.assertEqual(data, b"data")
        self.assertEqual(addr, ('192.168.1.1', 54321))
        self.mock_sock.recvfrom.assert_called_once_with(0)

    @patch('random.random')
    def test_multiple_reordering(self, mock_random):
        print('')
        mock_random.side_effect = [0.1, 0.1, 0.9]  # Reorder twice, then no reordering
        self.mock_sock.recvfrom.side_effect = [
            (b"first", ('192.168.1.1', 54321)),
            (b"second", ('192.168.1.1', 54321)),
            (b"third", ('192.168.1.1', 54321))
        ]
        data, addr = self.lossy_sock.recvfrom(1024)
        self.assertEqual(data, b"second")
        self.assertEqual(addr, ('192.168.1.1', 54321))
        self.assertEqual(len(self.lossy_sock.stored), 1)
        self.assertEqual(self.lossy_sock.stored[0][0], b"first")

