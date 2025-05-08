import unittest
import time
from src.protocol.server_listener import ServerManager
from src.utils.logger import Logger, VerbosityLevel
from test.utils_test import UtilsFunction


# Set up the logger for the test
#Logger.setup_name("test/test_connection.py")
#Logger.setup_verbosity(VerbosityLevel.VERBOSE)

server_addr = "0.0.0.0"
server_port = 2222

utils = UtilsFunction()

class TestClientConnection(unittest.TestCase):
    def test_connection(self):
        print('')
        utils.setup_test_threads(
            self._test_connection_server, 
            self._test_connection_client, 
            timeout=3
        )

    def test_two_connection(self):
        print('')
        utils.setup_test_threads(
            self._test_connection_server_twice, 
            self._test_connection_client_twice, 
            timeout=5
        )

    def _test_connection_server(self):
        # Test if the server is running and can accept connections
        server = ServerManager.start_server(host=server_addr, port=server_port)
        cli_socket, mode, filename = server.get_client()

        self.assertIsNotNone(cli_socket, "Server is not accepting connections")
        self.assertTrue(cli_socket.get_message() == b"we are connected", "Coudnt receive message in correct format from client")

        server.stop()

    def _test_connection_client(self):
        # Test if the client can connect to the server
        socket, mode, filename = ServerManager.connect_to_server(
            ("localhost", server_port), "download", "myfile"
        )
        time.sleep(.125)

        socket.send(b"we are connected")
        time.sleep(.125)
        socket.close()
    

    def _test_connection_server_twice(self):
        # Test if the server is running and can accept connections
        server = ServerManager.start_server(host=server_addr, port=server_port)

        for _ in range(2):
            cli_socket, mode, filename = server.get_client()
            time.sleep(.125)
            self.assertIsNotNone(cli_socket, "Server is not accepting connections")
            self.assertTrue(cli_socket.get_message() == b"we are connected", "Coudnt receive message in correct format from client")
            cli_socket.close()
        
        server.stop()

    def _test_connection_client_twice(self):
        # Test if the client can connect to the server
        for i in range(2):
            Logger.debug(who="test", message=f"============ STARTING CLIENT: {i} ============")
            self._test_connection_client()
            time.sleep(.125)

    #def setUp(self):
    #    # This method will run before each test
    #    self.client = Client("localhost", 8080, "sw")

    #def tearDown(self):
    #    # This method will run after each test
    #    self.client.close()

