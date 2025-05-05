import unittest
import time
from src.protocol.server_listener import ServerManager
from src.utils import Logger
from test.utils_test import UtilsFunction

server_addr = "0.0.0.0"
server_port = 2222

utils = UtilsFunction()

class TestClientConnection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.setup_name("test/test_connection.py")

    @classmethod
    def tearDownClass(cls):
        print("\n----------------------------------------")
        print("----------------------------------------\n")

    def test_connection(self):
        print('')
        utils.setup_test_threads(
            self._test_connection_server, 
            self._test_connection_client, 
            timeout=3
        )

    def _test_connection_server(self):
        # Test if the server is running and can accept connections
        server = ServerManager.start_server(host=server_addr, port=server_port)
        cli_socket = server.get_client()

        self.assertIsNotNone(cli_socket, "Server is not accepting connections")
        self.assertTrue(cli_socket.get_message() == b"we are connected", "Coudnt receive message in correct format from client")


        server.stop()

    def _test_connection_client(self):
        # Test if the client can connect to the server
        socket = ServerManager.connect_to_server(
            ("localhost", server_port)
        )

        time.sleep(.25)

        socket.send(b"we are connected")
        time.sleep(.25)
        socket.close()