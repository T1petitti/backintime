# TODO: add copyright text

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
    @classmethod
    def setUpClass(cls):
        cls.test_prefs_file_name = 'test_prefs.json'
        cls.test_prefs = {'key1': 'value1', 'key2': 'value2'}
        cls.default_prefs = {'show_toolbar_text': False}

    def setUp(self):
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
            qapp = qttools.createQApplication(self.cfg.APP_NAME)
            translator = qttools.initiate_translator(self.cfg.language())
            qapp.installTranslator(translator)

            self.mainWindow = app.MainWindow(self.cfg, self.appInstance, qapp)

    def tearDown(self):
        self.cfg.PLUGIN_MANAGER.appExit()
        self.appInstance.exitApplication()
        logger.closelog()

        del self.cfg
        del self.appInstance
        del self.mainWindow

    def add_default_prefs(self, list_to_append):
        for key, val in self.default_prefs.items():
            list_to_append.setdefault(key, val)

    def test_get_preferences_when_file_exists_and_no_prefs(self):
        """When file doesn't have preference"""
        self.mainWindow.main_preferences = self.test_prefs
        self.mainWindow.save_preferences(self.test_prefs_file_name)
        prefs = self.mainWindow.get_preferences(self.test_prefs_file_name)
        self.add_default_prefs(self.mainWindow.main_preferences)
        self.assertEqual(prefs, self.mainWindow.main_preferences)

    def test_get_preferences_when_file_exists_and_has_prefs(self):
        """When file has preference"""
        self.mainWindow.main_preferences = self.test_prefs
        self.add_default_prefs(self.mainWindow.main_preferences)
        self.mainWindow.save_preferences(self.test_prefs_file_name)
        prefs = self.mainWindow.get_preferences(self.test_prefs_file_name)
        self.assertEqual(prefs, self.mainWindow.main_preferences)

    def test_get_preferences_when_file_does_not_exist(self):
        prefs = self.mainWindow.get_preferences('non_existent_file.json')
        self.assertEqual(prefs, self.default_prefs)

    def test_get_preferences_when_file_is_empty(self):
        with open(self.test_prefs_file_name, 'w') as _:
            pass  # Create an empty file
        prefs = self.mainWindow.get_preferences(self.test_prefs_file_name)
        self.assertEqual(prefs, self.default_prefs)

    def test_get_preferences_with_invalid_json(self):
        with open(self.test_prefs_file_name, 'w') as file:
            file.write("Invalid JSON data")
        prefs = self.mainWindow.get_preferences(self.test_prefs_file_name)
        self.assertEqual(prefs, self.default_prefs)

    def test__verify_preferences_when_prefs_is_none(self):
        prefs = self.mainWindow._verify_preferences(None)
        self.assertEqual(prefs, self.default_prefs)

    def test__verify_preferences_when_no_prefs(self):
        verified_prefs = self.mainWindow._verify_preferences({})
        self.assertEqual(verified_prefs, self.default_prefs)

    def test__verify_preferences_when_empty_list_arg(self):
        verified_prefs = self.mainWindow._verify_preferences([])
        self.assertEqual(verified_prefs, self.default_prefs)

    def test__verify_preferences_when_list_arg(self):
        with self.assertRaises(TypeError):
            self.mainWindow._verify_preferences([True])

    def test_verify_preferences_when_has_prefs(self):
        verified_prefs = self.mainWindow.verify_preferences(self.default_prefs)
        self.assertEqual(verified_prefs, self.default_prefs)

    def test_verify_preferences_when_has_extra_prefs(self):
        prefs = self.default_prefs
        prefs['extra_key'] = 'extra_value'
        verified_prefs = self.mainWindow.verify_preferences(prefs)
        self.assertEqual(verified_prefs, prefs)

    def test_save_preferences_writes_file(self):
        self.mainWindow.save_preferences(self.test_prefs_file_name)
        self.assertTrue(os.path.exists(self.test_prefs_file_name))

    def test_save_preferences_writes_correct_data(self):
        self.mainWindow.main_preferences = self.test_prefs
        self.mainWindow.save_preferences(self.test_prefs_file_name)
        with open(self.test_prefs_file_name, 'r') as file:
            saved_prefs = json.load(file)
        self.assertEqual(saved_prefs, self.test_prefs)


if __name__ == '__main__':
    unittest.main()
