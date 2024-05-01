#    Back In Time
#    Copyright (C) 2008-2022 Oprea Dan, Bart de Koning, Richard Bailey, Germar Reitze
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

import qttools
import snapshots
import encfstools
import snapshotlog
import tools
import messagebox


class LogViewDialog(QDialog):
    # Workaround because of *-imports of Qt elements.
    # Remove as soon as possible.
    def __init__(self, parent, sid = None, systray = False):
        """
        Instantiate a snapshot log file viewer

        Args:
            parent:
            sid (:py:class:`SID`): snapshot ID whose log file shall be shown
                                   (``None`` = show last log)
            systray (bool): TODO Show log from systray icon or from App (boolean)
        """
        if systray:
            super(LogViewDialog, self).__init__()
        else:
            super(LogViewDialog, self).__init__(parent)


        self.config = parent.config
        self.snapshots = parent.snapshots
        self.mainWindow = parent
        self.sid = sid
        self.enableUpdate = False
        self.decode = None

        w = self.config.intValue('qt.logview.width', 800)
        h = self.config.intValue('qt.logview.height', 500)
        self.resize(w, h)

        import icon
        self.setWindowIcon(icon.VIEW_SNAPSHOT_LOG)
        if self.sid is None:
            self.setWindowTitle(_('Last Log View'))
        else:
            self.setWindowTitle(_('Snapshot Log View'))

        self.mainLayout = QVBoxLayout(self)

        layout = QHBoxLayout()
        self.mainLayout.addLayout(layout)

        # profiles
        self.lblProfile = QLabel(_('Profile') + ':', self)
        layout.addWidget(self.lblProfile)

        self.comboProfiles = qttools.ProfileCombo(self)
        layout.addWidget(self.comboProfiles, 1)
        self.comboProfiles.currentIndexChanged.connect(self.profileChanged)

        # snapshots
        self.lblSnapshots = QLabel(_('Snapshots') + ':', self)
        layout.addWidget(self.lblSnapshots)
        self.comboSnapshots = qttools.SnapshotCombo(self)
        layout.addWidget(self.comboSnapshots, 1)
        self.comboSnapshots.currentIndexChanged.connect(self.comboSnapshotsChanged)

        if self.sid is None:
            self.lblSnapshots.hide()
            self.comboSnapshots.hide()
        if self.sid or systray:
            self.lblProfile.hide()
            self.comboProfiles.hide()

        # filter
        layout.addWidget(QLabel(_('Filter') + ':'))

        self.comboFilter = QComboBox(self)
        layout.addWidget(self.comboFilter, 1)
        self.comboFilter.currentIndexChanged.connect(self.comboFilterChanged)

        self.comboFilter.addItem(_('All'), snapshotlog.LogFilter.NO_FILTER)

        # Note about ngettext plural forms: n=102 means "Other" in Arabic and
        # "Few" in Polish.
        # Research in translation community indicate this as the best fit to
        # the meaning of "all".
        self.comboFilter.addItem(' + '.join((_('Errors'), _('Changes'))), snapshotlog.LogFilter.ERROR_AND_CHANGES)
        self.comboFilter.setCurrentIndex(self.comboFilter.count() - 1)
        self.comboFilter.addItem(_('Errors'), snapshotlog.LogFilter.ERROR)
        self.comboFilter.addItem(_('Changes'), snapshotlog.LogFilter.CHANGES)
        self.comboFilter.addItem(_('Information'), snapshotlog.LogFilter.INFORMATION)
        self.comboFilter.addItem(_('rsync transfer failures (experimental)'), snapshotlog.LogFilter.RSYNC_TRANSFER_FAILURES)
        self.comboFilter.addItem(_('Rsync Help'), snapshotlog.LogFilter.RSYNC_HELP)


        # text view
        self.txtLogView = QPlainTextEdit(self)
        self.txtLogView.setFont(QFont('Monospace'))
        self.txtLogView.setReadOnly(True)
        self.txtLogView.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.mainLayout.addWidget(self.txtLogView)

        #
        self.mainLayout.addWidget(QLabel(_('[E] Error, [I] Information, [C] Change, [R] Rsync Help')))

        #decode path
        self.cbDecode = QCheckBox(_('decode paths'), self)
        self.cbDecode.stateChanged.connect(self.cbDecodeChanged)
        self.mainLayout.addWidget(self.cbDecode)

        #buttons
        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.mainLayout.addWidget(buttonBox)
        buttonBox.rejected.connect(self.close)




        self.updateSnapshots()
        self.updateDecode()
        self.updateProfiles()



        # watch for changes in log file
        self.watcher = QFileSystemWatcher(self)
        if self.sid is None:
            # only watch if we show the last log
            log = self.config.takeSnapshotLogFile(self.comboProfiles.currentProfileID())
            self.watcher.addPath(log)
        self.watcher.fileChanged.connect(self.updateLog)  # passes the path to the changed file to updateLog()

        self.txtLogView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.txtLogView.customContextMenuRequested.connect(self.contextMenuClicked)



    def displayRsyncInfo(self):
        if self.comboFilter.currentIndex() == 6:
            self.txtLogView.setPlainText("From Rsync Man Page https://download.samba.org/pub/rsync/rsync.1#opt--itemize-changes\n"
                                         "For a more compact explanation visit https://stackoverflow.com/a/36851784")
            self.txtLogView.appendPlainText("\nThe %i escape has a cryptic output that is 11 letters long. The general format is\n"
                                            "like the string YXcstpoguax, where Y is replaced by the type of update being done,\n"
                                            "X is replaced by the file-type, and the other letters represent attributes that may\n"
                                            "be output if they are being modified.\n\n"
                                            "The update types that replace the Y are as follows:\n"
                                            "- < means that a file is being transferred to the remote host (sent).\n"
                                            "- > means that a file is being transferred to the local host (received).\n"
                                            "- c means that a local change/creation is occurring for the item (such as the\n "
                                            "creation of a directory or the changing of a symlink, etc.).\n"
                                            "- h means that the item is a hard link to another item (requires --hard-links)\n"
                                            "- . means that the item is not being updated (though it might have attributes\n"
                                            "that are being modified).\n"
                                            "- * means that the rest of the itemized-output area contains a message\n(e.g. deleting).\n\n"
                                            "The file-types that replace the X are: f for a file, a d for a directory,\n"
                                            "an L for a symlink,a D for a device, and a S for a special file \n(e.g. named sockets and fifos).\n"
                                            "The other letters in the string indicate if some attributes of the file have changed,\n as follows:\n"
                                            ". - the attribute is unchanged.\n+ - the file is newly created.\n" " - all the attributes are unchanged (all dots turn to spaces).\n"
                                            "? - the change is unknown (when the remote rsync is old).\nA letter indicates an attribute is being updated.\n\n"
                                            "The attribute that is associated with each letter is as follows:\n\n"
                                            "- A c means either that a regular file has a different checksum (requires --checksum)\n"
                                            "or that a symlink, device, or special file has a changed value. Note that if you are\n"
                                            "sending files to an rsync prior to 3.0.1, this change flag will be present only for\nchecksum-differing regular files.\n"
                                            "- A s means the size of a regular file is different and will be updated\n by the file transfer.\n"
                                            "- A t means the modification time is different and is being updated to the\n"
                                            "sender's value (requires--times). An alternate value of T means that the modification\n"
                                            "time will be set to the transfer time, which happens when a file/symlink/device is\n"
                                            "updated without --times and when a symlink is changed and the receiver can't set its\n"
                                            "time. (Note: when using an rsync 3.0.0 client, you might see the s flag combined with\n"
                                            "t instead of the proper T flag for this time-setting failure.)\n"
                                            "- A p means the permissions are different and are being updated to the\nsender's value (requires --perms).\n"
                                            "- An o means the owner is different and is being updated to the sender's value\n(requires --owner and super-user privileges).\n"
                                            "- A g means the group is different and is being updated to the sender's value\n(requires --group and the authority to set the group).\n"
                                            "- A u|n|b indicates the following information:\n\t"
                                            "- u means the access (use) time is different and is being updated to the\n\tsender's value (requires --atimes)\n\t"
                                            "- n means the create time (newness) is different and is being updated to\n\tthe sender's value (requires --crtimes)\n\t"
                                            "- b means that both the access and create times are being updated\n"
                                            "- The a means that the ACL information is being changed.\n- The x means that the extended attribute information is being changed.\n\n"
                                            "One other output is possible: when deleting files, the %i will output the\n"
                                            "string '*deleting' for each item that is being removed (assuming that you are talking\n"
                                            "to a recent enough rsync that it logs deletions instead of outputting them as a\nverbose message)."
                                            )


    def cbDecodeChanged(self):
        if self.cbDecode.isChecked():
            if not self.decode:
                self.decode = encfstools.Decode(self.config)
        else:
            if not self.decode is None:
                self.decode.close()
            self.decode = None
        self.updateLog()

    def profileChanged(self, index):
        if not self.enableUpdate:
            return
        profile_id = self.comboProfiles.currentProfileID()
        self.mainWindow.comboProfiles.setCurrentProfileID(profile_id)
        self.mainWindow.comboProfileChanged(None)

        self.updateDecode()
        self.updateLog()

    def comboSnapshotsChanged(self, index):
        if not self.enableUpdate:
            return
        self.sid = self.comboSnapshots.currentSnapshotID()
        self.updateLog()

    def comboFilterChanged(self, index):
        self.updateLog()

    def contextMenuClicked(self, point):
        menu = QMenu()
        cursor = self.txtLogView.textCursor()

        btnDecode = menu.addAction(_('Decode'))
        btnDecode.triggered.connect(self.btnDecodeClicked)
        btnDecode.setEnabled(cursor.hasSelection())
        btnDecode.setVisible(self.config.snapshotsMode() == 'ssh_encfs')

        menu.exec(self.txtLogView.mapToGlobal(point))

    def btnDecodeClicked(self):
        if not self.decode:
            self.decode = encfstools.Decode(self.config)
        cursor = self.txtLogView.textCursor()
        selection = cursor.selectedText().strip()
        plain = self.decode.path(selection)
        cursor.insertText(plain)

    def updateProfiles(self):
        current_profile_id = self.config.currentProfile()

        self.comboProfiles.clear()

        profiles = self.config.profilesSortedByName()
        for profile_id in profiles:
            self.comboProfiles.addProfileID(profile_id)
            if profile_id == current_profile_id:
                self.comboProfiles.setCurrentProfileID(profile_id)

        self.enableUpdate = True
        self.updateLog()

        if len(profiles) <= 1:
            self.lblProfile.setVisible(False)
            self.comboProfiles.setVisible(False)

    def updateSnapshots(self):
        if self.sid:
            self.comboSnapshots.clear()
            for sid in snapshots.iterSnapshots(self.config):
                self.comboSnapshots.addSnapshotID(sid)
                if sid == self.sid:
                    self.comboSnapshots.setCurrentSnapshotID(sid)

    def updateDecode(self):
        if self.config.snapshotsMode() == 'ssh_encfs':
            self.cbDecode.show()
        else:
            self.cbDecode.hide()
            if self.cbDecode.isChecked():
                self.cbDecode.setChecked(False)

    def updateLog(self, watchPath = None):
        """
        Show the log file of the current snapshot in the GUI

        Args:
            watchPath: FQN to a log file (as string) whose changes are watched
                       via ``QFileSystemWatcher``. In case of changes
                       this function is called with the log file
                       and only the new lines in the log file are appended
                       to the log file widget in the GUI
                       Use ``None`` if a complete log file shall be shown
                       at once.
        """
        if not self.enableUpdate:
            return

        mode = self.comboFilter.itemData(self.comboFilter.currentIndex())
        # self.displayRsyncInfo()


        # TODO This expressions is hard to understand (watchPath is not a boolean!)
        if watchPath and self.sid is None:
            self.displayRsyncInfo()
            # remove path from watch to prevent multiple updates at the same time
            self.watcher.removePath(watchPath)
            # append only new lines to txtLogView
            log = snapshotlog.SnapshotLog(self.config, self.comboProfiles.currentProfileID())
            for line in log.get(mode = mode,
                                decode = self.decode,
                                skipLines = self.txtLogView.document().lineCount() - 1):
                self.txtLogView.appendPlainText(line)

            # re-add path to watch after 5sec delay
            alarm = tools.Alarm(callback = lambda: self.watcher.addPath(watchPath),
                                overwrite = False)
            alarm.start(5)

        elif self.sid is None:
            log = snapshotlog.SnapshotLog(self.config, self.comboProfiles.currentProfileID())
            self.txtLogView.setPlainText('\n'.join(log.get(mode = mode, decode = self.decode)))
            self.displayRsyncInfo()
        else:
            self.txtLogView.setPlainText('\n'.join(self.sid.log(mode, decode = self.decode)))
            self.displayRsyncInfo()

    def closeEvent(self, event):
        self.config.setIntValue('qt.logview.width', self.width())
        self.config.setIntValue('qt.logview.height', self.height())
        event.accept()
