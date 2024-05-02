import unittest
import sys
import os
import importlib.util

common_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
sys.path.append(common_path)

module_name = "snapshots"
spec = importlib.util.find_spec(module_name)
if spec is not None:
    snapshots = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(snapshots)
    snapshot = snapshots.Snapshots()

from PyQt6.QtWidgets import QLabel, QApplication

class TestQtLabel(unittest.TestCase):
    """Test cases for the Qt Label."""

    @classmethod
    def setUpClass(cls):
        """Set up the QApplication for the tests."""
        cls.app = QApplication([])

    @classmethod
    def tearDownClass(cls):
        """Clean up after the tests."""
        cls.app.quit()

    def test_create_label(self):
        """Test creating a QLabel."""
        label = QLabel("Hello, world!")

        self.assertIsInstance(label, QLabel)
        self.assertEqual(label.text(), "Hello, world!")

    def test_disk_space_label(self):
        """Test displaying disk space in a QLabel."""
        free_space = snapshot.statFreeSpaceLocal("/")
        label = QLabel()

        label.setText(str(free_space))

        self.assertIsInstance(label, QLabel)
        self.assertEqual(label.text(), str(free_space))
