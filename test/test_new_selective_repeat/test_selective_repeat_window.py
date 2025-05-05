import unittest
from utils import Logger
from unittest.mock import Mock, patch

from protocol.selective_repeat_lib.window import SelectiveRepeatWindow

class TestSelectiveRepeatProtocol(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.setup_name("test/test_selective_repeat_window.py")

    @classmethod
    def tearDownClass(cls):
        print("\n----------------------------------------")
        print("----------------------------------------\n")

    def test_selective_repeat_window_sender(self):
        # Test SelectiveRepeatWindow for sender
        window = SelectiveRepeatWindow(window_size=4, total_packets=10)
        
        # Test initial state
        self.assertEqual(window.base, 0)
        self.assertEqual(window.next_seq, 0)
        self.assertTrue(window.can_send())
        
        # Test sending within window
        self.assertTrue(window.can_send())
        self.assertEqual(window.get_next_seq(), 0)
        window.increment_next_seq()
        self.assertEqual(window.get_next_seq(), 1)
        
        # Test marking packets as acked
        window.mark_acked(0)
        window.mark_acked(1)
        self.assertTrue(window.is_packet_acked(0))
        self.assertTrue(window.is_packet_acked(1))
        
        # Test advancing window
        window.advance_window()
        self.assertEqual(window.base, 2)
        
        # Test completion
        for seq in range(2, 10):
            window.mark_acked(seq)
        window.advance_window()
        self.assertTrue(window.is_complete())

    def test_selective_repeat_window_receiver(self):
        # Test SelectiveRepeatWindow for receiver
        window = SelectiveRepeatWindow(window_size=4, total_packets=10)
        
        # Test buffering packets
        window.buffer_packet(0, b"data0")
        window.buffer_packet(2, b"data2")
        self.assertEqual(window.get_buffered_packet(0), b"data0")
        self.assertEqual(window.get_buffered_packet(2), b"data2")
        
        # Test advancing window
        window.advance_window()
        self.assertEqual(window.base, 1)
        window.buffer_packet(1, b"data1")
        window.advance_window()
        self.assertEqual(window.base, 3)
        
        # Test window boundaries
        self.assertTrue(window.is_within_window(3))
        self.assertFalse(window.is_within_window(7))

    def test_selective_repeat_window_receiver(self):
        window = SelectiveRepeatWindow(window_size=4, total_packets=10)
        self.assertEqual(window.base, 0)

        window.mark_acked(0)
        window.mark_acked(2)
        self.assertTrue(window.is_packet_acked(0))
        self.assertTrue(window.is_packet_acked(2))

        window.advance_window()
        self.assertEqual(window.base, 1)

        window.mark_acked(1)
        window.advance_window()
        self.assertEqual(window.base, 3)
        self.assertTrue(window.is_within_window(3))
        self.assertFalse(window.is_within_window(7))
