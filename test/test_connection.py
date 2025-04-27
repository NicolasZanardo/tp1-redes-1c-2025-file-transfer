import unittest
import threading
import time
from src.protocol.server_listener import ServerManager

server_port = 2222
client_port = 3333

class TestClientConnection(unittest.TestCase):
    def _setup_test_threads(self, server_function, client_function, timeout=3):
        server_thread = threading.Thread(target=server_function)
        server_thread.start()
        time.sleep(0.25)  # Give it a moment to start properly

        client_thread = threading.Thread(target=client_function)
        client_thread.start()

        client_thread.join(timeout = timeout)
        server_thread.join(timeout = timeout)

        if client_thread.is_alive() and server_thread.is_alive():
            self.fail("Client and server threads did not finish in time")

        if client_thread.is_alive():
            self.fail("Client thread did not finish in time")
        if server_thread.is_alive():
            self.fail("Server thread did not finish in time")
        

    def test_connection(self):
        self._setup_test_threads(
            self._test_connection_server, 
            self._test_connection_client, 
            timeout=3
        )

    def _test_connection_server(self):
        # Test if the server is running and can accept connections
        server = ServerManager.start_server(host="localhost", port=server_port)
        cli_socket = server.get_client()

        self.assertIsNotNone(cli_socket, "Server is not accepting connections")
        self.assertTrue(cli_socket.get_message() == b"we are connected", "Coudnt receive message in correct format from client")


        server.stop()

    def _test_connection_client(self):
        # Test if the client can connect to the server
        socket = ServerManager.connect_to_server(
            ("localhost", client_port), 
            ("localhost", server_port)
        )

        time.sleep(.25)

        socket.send(b"we are connected")
        time.sleep(.25)
        socket.close()

        
    #def setUp(self):
    #    # This method will run before each test
    #    self.client = Client("localhost", 8080, "sw")

    #def tearDown(self):
    #    # This method will run after each test
    #    self.client.close()

