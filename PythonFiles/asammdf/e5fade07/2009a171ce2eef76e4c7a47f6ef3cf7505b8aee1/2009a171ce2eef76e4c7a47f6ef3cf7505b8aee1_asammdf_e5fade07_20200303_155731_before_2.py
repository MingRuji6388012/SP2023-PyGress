# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'error_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.13.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ErrorDialog(object):
    def setupUi(self, ErrorDialog):
        ErrorDialog.setObjectName("ErrorDialog")
        ErrorDialog.resize(622, 114)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/error.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        ErrorDialog.setWindowIcon(icon)
        ErrorDialog.setSizeGripEnabled(True)
        self.layout = QtWidgets.QVBoxLayout(ErrorDialog)
        self.layout.setObjectName("layout")
        self.error_message = QtWidgets.QLabel(ErrorDialog)
        self.error_message.setText("")
        self.error_message.setObjectName("error_message")
        self.layout.addWidget(self.error_message)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.copy_to_clipboard_btn = QtWidgets.QPushButton(ErrorDialog)
        self.copy_to_clipboard_btn.setObjectName("copy_to_clipboard_btn")
        self.horizontalLayout.addWidget(self.copy_to_clipboard_btn)
        self.layout.addLayout(self.horizontalLayout)
        self.layout.setStretch(1, 1)

        self.retranslateUi(ErrorDialog)
        QtCore.QMetaObject.connectSlotsByName(ErrorDialog)

    def retranslateUi(self, ErrorDialog):
        _translate = QtCore.QCoreApplication.translate
        ErrorDialog.setWindowTitle(_translate("ErrorDialog", "Dialog"))
        self.copy_to_clipboard_btn.setText(_translate("ErrorDialog", "Copy to clipboard"))
from . import resource_rc
