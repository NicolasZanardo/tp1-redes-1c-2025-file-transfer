import unittest
import socket
import threading
import tempfile
import os
import time
import random
from unittest.mock import MagicMock
from protocol.selective_repeat import SelectiveRepeatProtocol, SelectiveRepeatReceiver
from protocol.packet import DefaultPacketizer
from utils import Logger
from test.utils_test import LossySocket, UtilsFunction, ConsistentlyLossySocket, TestParams

utils = UtilsFunction()

class TestSelectiveRepeatIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.setup_name("test/test_sr_protocol_integration.py")

    @classmethod
    def tearDownClass(cls):
        print("\n----------------------------------------")
        print("----------------------------------------\n")

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_file = os.path.join(self.temp_dir.name, 'input.txt')
        self.output_file = os.path.join(self.temp_dir.name, 'output.txt')

        # Prepare test file
        test_data = b"Hello, this is a test file for SR protocol!\n" * 10
        with open(self.input_file, 'wb') as f:
            f.write(test_data)
        print('')

    def tearDown(self):
        self.sender_sock.close()
        self.receiver_sock.close()
        self.temp_dir.cleanup()

    def test_file_transfer_high_random_loss(self):
        print(f"Running tests with seed {TestParams.seed}")
        random.seed(TestParams.seed)

        loss = TestParams.noise * 0.1
        self.sender_sock = LossySocket(socket.socket(socket.AF_INET, socket.SOCK_DGRAM), loss_rate=loss)
        self.receiver_sock = LossySocket(socket.socket(socket.AF_INET, socket.SOCK_DGRAM), loss_rate=loss)
        self.receiver_sock.bind(('127.0.0.1', 0))  # Bind to any free port
        self.receiver_addr = self.receiver_sock.getsockname()

        utils.setup_test_threads(
            self._test_file_transfer_SERVER,
            self._test_file_transfer_CLIENT,
            3
        )

        # Verify the output file matches the input file
        with open(self.input_file, 'rb') as f_in, open(self.output_file, 'rb') as f_out:
            input_content = f_in.read()
            output_content = f_out.read()
            self.assertEqual(input_content, output_content, "Transferred file does not match original")

    def test_file_transfer_consistent_loss(self):
        loss = 1
        if TestParams.noise == 0:
            loss = 1000000
        elif 0 < TestParams.noise <= 10:
            loss = 11-TestParams.noise
        

        self.sender_sock = ConsistentlyLossySocket(socket.socket(socket.AF_INET, socket.SOCK_DGRAM), loss_period=loss)
        self.receiver_sock = ConsistentlyLossySocket(socket.socket(socket.AF_INET, socket.SOCK_DGRAM), loss_period=loss)
        self.receiver_sock.bind(('127.0.0.1', 0))  # Bind to any free port
        self.receiver_addr = self.receiver_sock.getsockname()

        utils.setup_test_threads(
            self._test_file_transfer_SERVER,
            self._test_file_transfer_CLIENT,
            3
        )

        # Verify the output file matches the input file
        with open(self.input_file, 'rb') as f_in, open(self.output_file, 'rb') as f_out:
            input_content = f_in.read()
            output_content = f_out.read()
            self.assertEqual(input_content, output_content, "Transferred file does not match original")


    def _test_file_transfer_SERVER(self):
        sender = SelectiveRepeatProtocol(
            self.sender_sock,
            self.receiver_addr,
            self.input_file,
            packetizer=DefaultPacketizer(),
            timeout=0.25,
            window_size=4
        )

        sender.start()
        sender.close()
    
    def _test_file_transfer_CLIENT(self):
        receiver = SelectiveRepeatReceiver(
            self.receiver_sock,
            self.output_file,
            packetizer=DefaultPacketizer(),
            timeout=0.25,
            window_size=4
        )

        receiver.start()
        receiver.close()