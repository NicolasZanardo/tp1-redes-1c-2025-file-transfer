import unittest
import socket
from unittest.mock import MagicMock, patch, call
from utils import Logger
from test.utils_test import LossySocket, ConsistentlyLossySocket

class TestConsistentlyLossySocket(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.setup_name("test/test_consistently_lossy_socket.py")

    @classmethod
    def tearDownClass(cls):
        print("\n----------------------------------------")
        print("----------------------------------------\n")

    def setUp(self):
        self.mock_sock = MagicMock(spec=socket.socket)
        self.mock_sock.getsockname.return_value = ('127.0.0.1', 12345)
        self.lossy_sock = ConsistentlyLossySocket(self.mock_sock, loss_period=3)

    def tearDown(self):
        self.mock_sock.reset_mock()

    def test_initialization(self):
        lossy_sock = ConsistentlyLossySocket(self.mock_sock, loss_period=5)
        self.assertEqual(lossy_sock.sock, self.mock_sock)
        self.assertEqual(lossy_sock.loss_period, 5)
        self.assertEqual(lossy_sock.sent, 0)
        self.assertEqual(lossy_sock.stored, [])

    @patch.object(Logger, 'debug')
    def test_sendto_no_loss(self, mock_logger):
        self.lossy_sock.sent = 0  # sent=1, 1 % 3 != 0
        self.lossy_sock.sendto(b"test data", ('192.168.1.1', 54321))
        self.mock_sock.sendto.assert_called_once_with(b"test data", ('192.168.1.1', 54321))
        self.assertEqual(self.lossy_sock.sent, 1)
        mock_logger.assert_not_called()

    @patch.object(Logger, 'debug')
    def test_sendto_loss(self, mock_logger):
        self.lossy_sock.sent = 2  # sent=3, 3 % 3 == 0
        self.lossy_sock.sendto(b"test data", ('192.168.1.1', 54321))
        self.mock_sock.sendto.assert_not_called()
        self.assertEqual(self.lossy_sock.sent, 3)
        mock_logger.assert_called_once_with(
            who="[Lossy-Socket ('127.0.0.1', 12345)]",
            message="I didn't sent the data to ('192.168.1.1', 54321)"
        )

    def test_sendto_loss_period_one(self):
        lossy_sock = ConsistentlyLossySocket(self.mock_sock, loss_period=1)
        with patch.object(Logger, 'debug') as mock_logger:
            lossy_sock.sendto(b"test data", ('192.168.1.1', 54321))  # sent=1, 1 % 1 == 0
            self.mock_sock.sendto.assert_not_called()
            mock_logger.assert_called_once()
            self.assertEqual(lossy_sock.sent, 1)

    @patch.object(Logger, 'debug')
    def test_sendto_loss_period_two(self, mock_logger):
        lossy_sock = ConsistentlyLossySocket(self.mock_sock, loss_period=2)
        lossy_sock.sendto(b"data1", ('192.168.1.1', 54321))  # sent=1, 1 % 2 != 0
        self.mock_sock.sendto.assert_called_once_with(b"data1", ('192.168.1.1', 54321))
        mock_logger.assert_not_called()
        self.mock_sock.reset_mock()
        lossy_sock.sendto(b"data2", ('192.168.1.1', 54321))  # sent=2, 2 % 2 == 0
        self.mock_sock.sendto.assert_not_called()
        mock_logger.assert_called_once()

    def test_sendto_empty_data(self):
        self.lossy_sock.sent = 0  # sent=1, 1 % 3 != 0
        self.lossy_sock.sendto(b"", ('192.168.1.1', 54321))
        self.mock_sock.sendto.assert_called_once_with(b"", ('192.168.1.1', 54321))
        self.assertEqual(self.lossy_sock.sent, 1)

    @patch.object(Logger, 'debug')
    def test_recvfrom_no_reorder(self, mock_logger):
        self.lossy_sock.sent = 1  # sent=1, 1 % 3 != 0
        self.mock_sock.recvfrom.return_value = (b"received data", ('192.168.1.1', 54321))
        data, addr = self.lossy_sock.recvfrom(1024)
        self.assertEqual(data, b"received data")
        self.assertEqual(addr, ('192.168.1.1', 54321))
        self.assertEqual(self.lossy_sock.sent, 2)
        self.assertEqual(self.lossy_sock.stored, [])
        self.mock_sock.recvfrom.assert_called_once_with(1024)
        mock_logger.assert_not_called()

    @patch.object(Logger, 'debug')
    def test_recvfrom_reorder(self, mock_logger):
        self.lossy_sock.sent = 2  # sent=3, 3 % 3 != 0
        self.mock_sock.recvfrom.side_effect = [
            (b"first packet", ('192.168.1.1', 54321)),
            (b"second packet", ('192.168.1.1', 54321))
        ]
        data, addr = self.lossy_sock.recvfrom(1024)
        self.assertEqual(data, b"second packet")
        self.assertEqual(addr, ('192.168.1.1', 54321))
        self.assertEqual(self.lossy_sock.sent, 3)  # Incremented twice
        self.assertEqual(self.lossy_sock.stored, [(b"first packet", ('192.168.1.1', 54321))])
        self.mock_sock.recvfrom.assert_called_with(1024)
        mock_logger.assert_called_once()

    def test_recvfrom_stored_packet(self):
        self.lossy_sock.stored = [(b"stored packet", ('192.168.1.1', 54321))]
        data, addr = self.lossy_sock.recvfrom(1024)
        self.assertEqual(data, b"stored packet")
        self.assertEqual(addr, ('192.168.1.1', 54321))
        self.assertEqual(self.lossy_sock.stored, [])
        self.assertEqual(self.lossy_sock.sent, 1)  # No increment for stored
        self.mock_sock.recvfrom.assert_not_called()

    def test_recvfrom_timeout_no_stored(self):
        self.mock_sock.recvfrom.side_effect = socket.timeout("Timeout")
        with self.assertRaises(socket.timeout) as cm:
            self.lossy_sock.recvfrom(1024)
        self.assertEqual(str(cm.exception), "Simulated packet loss")
        self.assertEqual(self.lossy_sock.sent, 1)
        self.assertEqual(self.lossy_sock.stored, [])
        self.mock_sock.recvfrom.assert_called_once_with(1024)

    def test_recvfrom_timeout_with_stored(self):
        print('')
        self.mock_sock.recvfrom.side_effect = [
            (b"1", ('192.168.1.1', 54321)),
            (b"2", ('192.168.1.1', 54321)),
            (b"3", ('192.168.1.1', 54321)),
            socket.timeout("Timeout"),
            (b"4", ('192.168.1.1', 54321)),
            (b"5", ('192.168.1.1', 54321)),
            (b"6", ('192.168.1.1', 54321)),
            socket.timeout("Timeout"),
            (b"7", ('192.168.1.1', 54321)),
            (b"8", ('192.168.1.1', 54321)),
            (b"9", ('192.168.1.1', 54321)),
            socket.timeout("Timeout"),
        ]
        
        res = []
        for _ in range(0,9):
            data, addr = self.lossy_sock.recvfrom(1024)
            res.append(data)
            
        self.assertEqual(res, [b"1",b"2",b"3",b"4",b"5",b"6",b"7",b"8",b"9"])
    
    def test_recvfrom_timeout_as_last_action(self):
        print('')
        self.lossy_sock.sent = 2  # sent=3, 3 % 3 != 0
        self.mock_sock.recvfrom.side_effect = [
            (b"first", ('192.168.1.1', 54321)),
            socket.timeout("Timeout")
        ]
        data, addr = self.lossy_sock.recvfrom(1024)
        self.assertEqual(data, b"first")
        self.assertEqual(addr, ('192.168.1.1', 54321))
        self.assertEqual(self.lossy_sock.sent, 3)  # Incremented twice
        self.assertEqual(self.lossy_sock.stored, [])
        self.mock_sock.recvfrom.assert_has_calls([call(1024), call(1024)])

    @patch.object(Logger, 'debug')
    def test_recvfrom_loss_period_one(self, mock_logger):
        lossy_sock = ConsistentlyLossySocket(self.mock_sock, loss_period=1)
        self.mock_sock.recvfrom.side_effect = [
            (b"first", ('192.168.1.1', 54321)),
            (b"second", ('192.168.1.1', 54321))
        ]
        data, addr = lossy_sock.recvfrom(1024)  # sent=1, 1 % 1 == 0
        self.assertEqual(data, b"second")
        self.assertEqual(addr, ('192.168.1.1', 54321))
        self.assertEqual(lossy_sock.stored, [(b'first', ('192.168.1.1', 54321))])
        self.assertEqual(lossy_sock.sent, 1)
        mock_logger.assert_called_once()

    @patch.object(Logger, 'debug')
    def test_recvfrom_loss_period_two(self, mock_logger):
        lossy_sock = ConsistentlyLossySocket(self.mock_sock, loss_period=2)
        self.mock_sock.recvfrom.side_effect = [
            (b"first", ('192.168.1.1', 54321)),
            (b"second", ('192.168.1.1', 54321)),
            (b"third", ('192.168.1.1', 54321))
        ]
        data, addr = lossy_sock.recvfrom(1024)  # sent=1, 1 % 2 != 0
        self.assertEqual(data, b"first")
        self.assertEqual(addr, ('192.168.1.1', 54321))
        data, addr = lossy_sock.recvfrom(1024)  # sent=1, 1 % 2 != 0
        
        self.assertEqual(data, b"third")
        self.assertEqual(addr, ('192.168.1.1', 54321))
        
        self.assertEqual(lossy_sock.stored, [(b"second", ('192.168.1.1', 54321))])
        self.assertEqual(lossy_sock.sent, 2)
        
        mock_logger.assert_called_once()

    def test_recvfrom_zero_bufsize(self):
        print('')
        self.lossy_sock.sent = 2  # sent=3, 3 % 3 == 0
        self.mock_sock.recvfrom.return_value = (b"data", ('192.168.1.1', 54321))
        data, addr = self.lossy_sock.recvfrom(0)
        self.assertEqual(data, b"data")
        self.assertEqual(addr, ('192.168.1.1', 54321))
        self.assertEqual(self.lossy_sock.sent, 3)
        #self.mock_sock.recvfrom.assert_called_once_with(0)

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

    @patch.object(Logger, 'debug')
    def test_multiple_operations(self, mock_logger):
        # Test sequence: send (no loss), send (no loss), send (loss), recv (reorder), recv (no reorder)
        self.lossy_sock.sent = 0
        self.mock_sock.recvfrom.side_effect = [
            (b"first", ('192.168.1.1', 54321)),
            (b"second", ('192.168.1.1', 54321)),
            (b"third", ('192.168.1.1', 54321))
        ]

        # Send 1: sent=1, 1 % 3 != 0
        self.lossy_sock.sendto(b"data1", ('192.168.1.1', 54321))
        self.mock_sock.sendto.assert_called_with(b"data1", ('192.168.1.1', 54321))
        self.assertEqual(self.lossy_sock.sent, 1)

        # Send 2: sent=2, 2 % 3 != 0
        self.lossy_sock.sendto(b"data2", ('192.168.1.1', 54321))
        self.mock_sock.sendto.assert_called_with(b"data2", ('192.168.1.1', 54321))
        self.assertEqual(self.lossy_sock.sent, 2)

        # Send 3: sent=3, 3 % 3 == 0
        self.mock_sock.sendto.reset_mock()
        self.lossy_sock.sendto(b"data3", ('192.168.1.1', 54321))
        self.mock_sock.sendto.assert_not_called()
        self.assertEqual(self.lossy_sock.sent, 3)
        mock_logger.assert_called_once()

        # Receive 1: sent=4, 4 % 3 != 0 (keep)
        mock_logger.reset_mock()
        data, addr = self.lossy_sock.recvfrom(1024)
        self.assertEqual(data, b"first")
        self.assertEqual(addr, ('192.168.1.1', 54321))
        self.assertEqual(self.lossy_sock.stored, [])
        self.assertEqual(self.lossy_sock.sent, 4)  # Incremented twice
        mock_logger.assert_not_called()

        # Send 4: sent=5, 5 % 3 != 0
        self.mock_sock.sendto.reset_mock()
        self.lossy_sock.sendto(b"data4", ('192.168.1.1', 54321))
        self.mock_sock.sendto.assert_called_with(b"data4", ('192.168.1.1', 54321))
        self.assertEqual(self.lossy_sock.sent, 5)
        mock_logger.assert_not_called()

        # Receive 1: sent=6, 6 % 3 == 0 (STORE)
        mock_logger.reset_mock()
        data, addr = self.lossy_sock.recvfrom(1024)
        self.assertEqual(data, b"third")
        self.assertEqual(addr, ('192.168.1.1', 54321))
        self.assertEqual(self.lossy_sock.stored, [(b"second", ('192.168.1.1', 54321))])
        self.assertEqual(self.lossy_sock.sent, 6)  # Incremented twice
        mock_logger.assert_called_once()

        # Receive 2: stored packet
        data, addr = self.lossy_sock.recvfrom(1024)
        self.assertEqual(data, b"second")
        self.assertEqual(addr, ('192.168.1.1', 54321))
        
    def test_loss_period_zero(self):
        with self.assertRaises(ZeroDivisionError):
            lossy_sock = ConsistentlyLossySocket(self.mock_sock, loss_period=0)
            lossy_sock.sendto(b"data", ('192.168.1.1', 54321))  # Triggers modulo by zero
