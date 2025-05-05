import unittest
import socket
import threading
import os
import time

from src.utils import FileChunkReader, Logger
from src.protocol.packet import DefaultPacketizer
from src.protocol.stop_and_wait_lib import StopAndWaitProtocol, StopAndWaitReceiver

TEST_FILE_CONTENT = b"Hello, this is a test file.\nAnother line.\n"
TEST_INPUT_PATH = "test/temp_input.txt"
TEST_OUTPUT_PATH = "test/temp_output.txt"
DEST_ADDR = ('127.0.0.1', 9999)


class TestStopAndWaitIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.setup_name("test/test_integration_sw.py")
        # Create input file
        os.makedirs("test", exist_ok=True)
        with open(TEST_INPUT_PATH, "wb") as f:
            f.write(TEST_FILE_CONTENT)

    @classmethod
    def tearDownClass(cls):
        os.remove(TEST_INPUT_PATH)
        if os.path.exists(TEST_OUTPUT_PATH):
            os.remove(TEST_OUTPUT_PATH)
        print("\n----------------------------------------")
        print("----------------------------------------\n")

    def setUp(self):
        print('')

    def test_send_and_receive_file_over_udp(self):
        packetizer = DefaultPacketizer()

        # Set up receiver
        receiver_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receiver_sock.bind(DEST_ADDR)

        receiver = StopAndWaitReceiver(
            sock=receiver_sock,
            output_path=TEST_OUTPUT_PATH,
            packetizer=packetizer
        )

        receiver_thread = threading.Thread(target=receiver.start)
        receiver_thread.daemon = True
        receiver_thread.start()

        time.sleep(0.2)  # Ensure receiver is listening

        # Set up sender
        sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        sender = StopAndWaitProtocol(
            sock=sender_sock,
            dest=DEST_ADDR,
            file_path=TEST_INPUT_PATH,
            packetizer=packetizer
        )

        sender.start()

        receiver_thread.join(timeout=2)

        with open(TEST_OUTPUT_PATH, "rb") as f:
            received_data = f.read()

        self.assertEqual(received_data, TEST_FILE_CONTENT)

