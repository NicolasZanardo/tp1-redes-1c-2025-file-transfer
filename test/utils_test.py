import unittest
import threading
import time


class UtilsFunction(unittest.TestCase):
    def setup_test_threads(self, server_function, client_function, timeout=3):
        server_thread = threading.Thread(target=server_function)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.25)  # Give it a moment to start properly

        client_thread = threading.Thread(target=client_function)
        client_thread.daemon = True
        client_thread.start()

        client_thread.join(timeout = timeout)
        server_thread.join(timeout = timeout)

        if client_thread.is_alive() and server_thread.is_alive():
            self.fail("Client and server threads did not finish in time")

        if client_thread.is_alive():
            self.fail("Client thread did not finish in time")
        if server_thread.is_alive():
            self.fail("Server thread did not finish in time")

