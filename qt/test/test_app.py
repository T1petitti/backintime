# TODO: add copyright text

import time
import unittest
import os
import sys
import json
from unittest.mock import patch

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from qt import app

from qt import qttools_path
qttools_path.registerBackintimePath('common')

# Workaround until the codebase is rectified/equalized.
from common import tools
tools.initiate_translation(None)

from common import logger
from qt import qttools
from common import backintime
from common import guiapplicationinstance


class TestMainWindow(unittest.TestCase):
    def setUp(self):
        # Variables for preferences testing
        self.test_prefs_file_name = 'test_prefs.json'
        self.test_prefs = {'key1': 'value1', 'key2': 'value2'}
        self.default_prefs = {'show_toolbar_text': False}

        # Mock exit to prevent it from actually exiting the Python interpreter
        with patch("builtins.exit") as mock_exit:
            self.cfg = backintime.startApp('backintime-qt')

            raiseCmd = ''
            if len(sys.argv) > 1:
                raiseCmd = '\n'.join(sys.argv[1:])

            self.appInstance = guiapplicationinstance.GUIApplicationInstance(self.cfg.appInstanceFile(), raiseCmd)
            self.cfg.PLUGIN_MANAGER.load(cfg=self.cfg)
            self.cfg.PLUGIN_MANAGER.appStart()

            logger.openlog()
            self.qapp = qttools.createQApplication(self.cfg.APP_NAME)
            translator = qttools.initiate_translator(self.cfg.language())
            self.qapp.installTranslator(translator)

            self.mainWindow = app.MainWindow(self.cfg, self.appInstance, self.qapp)

    def tearDown(self):
        self.cfg.PLUGIN_MANAGER.appExit()
        self.appInstance.exitApplication()
        logger.closelog()

        self.qapp.quit()

        # Allow time for the application to finish processing events
        for _ in range(100):
            self.qapp.processEvents()
            time.sleep(0.001)

    def add_default_prefs(self, list_to_append):
        """Add default preferences to list."""
        for key, val in self.default_prefs.items():
            list_to_append.setdefault(key, val)

    def test_get_preferences_when_file_exists_and_no_prefs(self):
        """When file doesn't have preferences."""
        self.mainWindow.main_preferences = self.test_prefs.copy()
        self.mainWindow.save_preferences(self.test_prefs_file_name)
        prefs = self.mainWindow.get_preferences(self.test_prefs_file_name)
        self.add_default_prefs(self.mainWindow.main_preferences)
        self.assertEqual(prefs, self.mainWindow.main_preferences)

    def test_get_preferences_when_file_exists_and_has_prefs(self):
        """When file has preferences."""
        self.mainWindow.main_preferences = self.test_prefs.copy()
        self.add_default_prefs(self.mainWindow.main_preferences)
        self.mainWindow.save_preferences(self.test_prefs_file_name)
        prefs = self.mainWindow.get_preferences(self.test_prefs_file_name)
        self.assertEqual(prefs, self.mainWindow.main_preferences)

    def test_get_preferences_when_file_does_not_exist(self):
        """Ensure file gets created if it doesn't exist."""
        prefs = self.mainWindow.get_preferences('non_existent_file.json')
        self.assertEqual(prefs, self.default_prefs)

    def test_get_preferences_when_file_is_empty(self):
        with open(self.test_prefs_file_name, 'w') as _:
            pass  # Create an empty file
        prefs = self.mainWindow.get_preferences(self.test_prefs_file_name)
        self.assertEqual(prefs, self.default_prefs)

    def test_get_preferences_with_invalid_json(self):
        """When preferences data in file is invalid."""
        with open(self.test_prefs_file_name, 'w') as file:
            file.write("Invalid JSON data")
        prefs = self.mainWindow.get_preferences(self.test_prefs_file_name)
        self.assertEqual(prefs, self.default_prefs)

    def test__verify_preferences_when_prefs_is_none(self):
        """When argument is None."""
        prefs = self.mainWindow._verify_preferences(None)
        self.assertEqual(prefs, self.default_prefs)

    def test__verify_preferences_when_no_prefs(self):
        """When argument is empty."""
        verified_prefs = self.mainWindow._verify_preferences({})
        self.assertEqual(verified_prefs, self.default_prefs)

    def test__verify_preferences_when_empty_list_arg(self):
        """When argument is an empty list."""
        verified_prefs = self.mainWindow._verify_preferences([])
        self.assertEqual(verified_prefs, self.default_prefs)

    def test__verify_preferences_when_list_arg(self):
        """When argument is a list."""
        with self.assertRaises(TypeError):
            self.mainWindow._verify_preferences([True])

    def test__verify_preferences_when_has_prefs(self):
        """Ensure correct data comes back unchanged."""
        verified_prefs = self.mainWindow._verify_preferences(self.default_prefs)
        self.assertEqual(verified_prefs, self.default_prefs)

    def test__verify_preferences_when_has_extra_prefs(self):
        """Ensure preferences remain in data."""
        prefs = self.default_prefs.copy()
        prefs['extra_key'] = 'extra_value'
        verified_prefs = self.mainWindow._verify_preferences(prefs)
        self.assertEqual(verified_prefs, prefs)

    def test_save_preferences_writes_file(self):
        """Ensure file gets created."""
        self.mainWindow.save_preferences(self.test_prefs_file_name)
        self.assertTrue(os.path.exists(self.test_prefs_file_name))

    def test_save_preferences_writes_correct_data(self):
        """Ensure preferences gets saved correctly."""
        self.mainWindow.main_preferences = self.test_prefs.copy()
        self.mainWindow.save_preferences(self.test_prefs_file_name)
        with open(self.test_prefs_file_name, 'r') as file:
            saved_prefs = json.load(file)
        self.assertEqual(saved_prefs, self.test_prefs)


if __name__ == '__main__':
    unittest.main()
