import unittest
import sys
import os
import importlib.util

# Add the directory to sys.path
common_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
sys.path.append(common_path)

# Now you can import the module using its name
module_name = "snapshots"
spec = importlib.util.find_spec(module_name)
if spec is not None:
    snapshots = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(snapshots)
    # Now you can access the Snapshots class
    snapshot = snapshots.Snapshots()



from PyQt6.QtGui import (QAction,
                         QShortcut,
                         QDesktopServices,
                         QPalette,
                         QColor,
                         QIcon,
                         QFileSystemModel)
from PyQt6.QtWidgets import (QWidget,
                             QFrame,
                             QMainWindow,
                             QToolButton,
                             QLabel,
                             QLineEdit,
                             QCheckBox,
                             QListWidget,
                             QTreeView,
                             QTreeWidget,
                             QTreeWidgetItem,
                             QAbstractItemView,
                             QStyledItemDelegate,
                             QVBoxLayout,
                             QHBoxLayout,
                             QStackedLayout,
                             QSplitter,
                             QGroupBox,
                             QMenu,
                             QToolBar,
                             QProgressBar,
                             QMessageBox,
                             QInputDialog,
                             QDialog,
                             QDialogButtonBox,
                             QApplication,
                             )
from PyQt6.QtCore import (Qt,
                          QObject,
                          QPoint,
                          pyqtSlot,
                          pyqtSignal,
                          QTimer,
                          QThread,
                          QEvent,
                          QSortFilterProxyModel,
                          QDir,
                          QSize,
                          QUrl,
                          pyqtRemoveInputHook,
                          )

class TestQtLabel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create a QApplication instance before any QWidget
        cls.app = QApplication([])

    @classmethod
    def tearDownClass(cls):
        # Clean up the QApplication instance
        cls.app.quit()

    def test_create_label(self):
        # Create a QLabel instance
        label = QLabel("Hello, world!")

        # Check that the label was created successfully
        self.assertIsInstance(label, QLabel)
        self.assertEqual(label.text(), "Hello, world!")

    def test_disk_space_label(self):
        # Create a QLabel instance
        free_space = snapshot.statFreeSpaceLocal("/")
        label = QLabel()

        label.setText(str(free_space))

        # Check that the label was created successfully
        self.assertIsInstance(label, QLabel)
        self.assertEqual(label.text(), str(free_space))
