import unittest
import threading
import os
import tempfile
import time
import hashlib
from argparse import Namespace
from unittest.mock import patch
from utils.logger import Logger, VerbosityLevel

import upload
import download
import importlib
start_server = importlib.import_module('start-server')
# Assume LossySocket is available and mimics socket.socket with packet loss
#from protocol.lossy_socket import LossySocket

from test.utils_test import UtilsFunction, SocketTestParams
utils = UtilsFunction()

class TestServerClientIntegration(unittest.TestCase):
    def setUp(self):
        # Setup logger
        Logger.setup_name('test_integration.py')
        print('')
        
        # Create temporary directories for server storage and client files
        self.server_storage = tempfile.mkdtemp()
        self.client_dir = tempfile.mkdtemp()
        
        # Wait briefly for server to start
        time.sleep(0.1)
        
        self.client_input_file = self._make_test_file(self.client_dir, "input.txt")
        self.client_output_file = self._make_test_file(self.client_dir, "output.txt")

        self.server_file_name = "middleman.txt"
        self._make_test_file(self.server_storage, self.server_file_name)
        
        self.test_file_content = b"Hello, this is a test file!"
        with open(self.client_input_file, 'wb') as f:
            f.write(self.test_file_content)
        
        self.host = "127.0.0.1"
        self.port = 54321

    def _make_test_file(self, dirpath, name):
        """Create a test file with some content."""
        file_path = os.path.join(dirpath, name)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return file_path


    def tearDown(self):
        # Clean up temporary directories
        for temp_dir in [self.server_storage, self.client_dir]:
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(temp_dir)
    
    def _compute_file_hash(self, file_path):
        """Compute SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def test_upload_and_download_sw(self):
        self.protocol = "sw"
        utils.setup_test_threads(
            self._test_upload_and_download_SERVER,
            self._test_upload_and_download_CLIENT,
            15
        )
        self.server_stop_event.running = False

    def test_upload_and_download_sr(self):
        self.protocol = "sr"
        utils.setup_test_threads(
            self._test_upload_and_download_SERVER,
            self._test_upload_and_download_CLIENT,
            15
        )
        self.server_stop_event.running = False
    
    def _test_upload_and_download_SERVER(self):
        # Mock server arguments
        self.server_args = Namespace(
            verbose=False,
            quiet=True,
            host=self.host,
            port=self.port,
            storage=self.server_storage,
            protocol=self.protocol
        )
        
        self.server_stop_event = Namespace(
            running = True
        )
        
        # Start server in a separate thread
        start_server.behaviour(self.server_args, self.server_stop_event)

        Logger.info("Server stoped in test.")

    def _test_upload_and_download_CLIENT(self):
        """Helper to test upload followed by download."""
        # Mock upload arguments
        upload_args = Namespace(
            verbose=False,
            quiet=True,
            host=self.host,
            port=self.port,
            src=self.client_input_file,
            name=self.server_file_name,
            protocol=self.protocol
        )
        
        # Perform upload
        upload.behaviour(upload_args)
        
        # Verify uploaded file on server
        server_file_path = os.path.join(self.server_storage, self.server_file_name)
        self.assertTrue(os.path.isfile(server_file_path), f"Uploaded file not found on server '{server_file_path}'")
        
        with open(self.client_input_file, 'rb') as f:
            original_content = f.read()
        with open(server_file_path, 'rb') as f:
            uploaded_content = f.read()
        
        Logger.debug(who="TEST", message=f"ORIGINAL: {original_content}")
        Logger.debug(who="TEST", message=f"UPLOADED: {uploaded_content}")
        
        self.assertEqual(
            original_content,
            uploaded_content,
            "Uploaded file hash mismatch"
        )
        
        self.assertEqual(
            self._compute_file_hash(self.client_input_file),
            self._compute_file_hash(server_file_path),
            "Uploaded file hash mismatch"
        )
        
        # Mock download arguments
        download_file_path = os.path.join(self.client_dir, "downloaded_" + self.server_file_name)
        download_args = Namespace(
            verbose=False,
            quiet=True,
            host=self.host,
            port=self.port,
            dst=self.client_output_file,
            name=self.server_file_name,
            protocol=self.protocol
        )
        
        # Perform download

        Logger.debug(who="TEST", message="BEGIN WITH DOWNLOAD")
        download.behaviour(download_args)
        Logger.debug(who="TEST", message="-------------END WITH DOWNLOAD----------------")


        # Verify downloaded file
        self.assertTrue(os.path.isfile(self.client_output_file), "Downloaded file not found")
        self.assertEqual(
            self._compute_file_hash(self.client_input_file),
            self._compute_file_hash(self.client_output_file),
            "Downloaded file hash mismatch"
        )

        Logger.debug(who="TEST", message="TELL SERVER TO STOP")
        self.server_stop_event.running = False
