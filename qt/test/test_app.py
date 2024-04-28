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


class TestSavePreferences(unittest.TestCase):
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

    def test_save_preferences_writes_file(self):
        self.mainWindow.save_preferences()
        self.assertTrue(os.path.exists('main_preferences'))

    def test_save_preferences_writes_correct_data(self):
        test_preferences = {'key1': 'value1', 'key2': 'value2'}
        self.mainWindow.main_preferences = test_preferences
        self.mainWindow.save_preferences()
        with open('main_preferences', 'r') as file:
            saved_preferences = json.load(file)
        self.assertEqual(saved_preferences, test_preferences)


if __name__ == '__main__':
    unittest.main()
