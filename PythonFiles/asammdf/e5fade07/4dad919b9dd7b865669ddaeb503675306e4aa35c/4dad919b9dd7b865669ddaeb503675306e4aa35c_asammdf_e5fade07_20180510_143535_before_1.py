# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'channel_display_widget.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ChannelDiplay(object):
    def setupUi(self, ChannelDiplay):
        ChannelDiplay.setObjectName("ChannelDiplay")
        ChannelDiplay.resize(260, 30)
        ChannelDiplay.setMinimumSize(QtCore.QSize(40, 30))
        self.horizontalLayout = QtWidgets.QHBoxLayout(ChannelDiplay)
        self.horizontalLayout.setContentsMargins(5, 2, 5, 2)
        self.horizontalLayout.setSpacing(5)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.display = QtWidgets.QCheckBox(ChannelDiplay)
        self.display.setMinimumSize(QtCore.QSize(13, 13))
        self.display.setText("")
        self.display.setChecked(True)
        self.display.setObjectName("display")
        self.horizontalLayout.addWidget(self.display)
        self.color_btn = QtWidgets.QPushButton(ChannelDiplay)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.color_btn.sizePolicy().hasHeightForWidth())
        self.color_btn.setSizePolicy(sizePolicy)
        self.color_btn.setMinimumSize(QtCore.QSize(13, 13))
        self.color_btn.setMaximumSize(QtCore.QSize(13, 13))
        self.color_btn.setAutoFillBackground(False)
        self.color_btn.setStyleSheet("background-color: rgb(255, 0, 0);")
        self.color_btn.setText("")
        self.color_btn.setFlat(False)
        self.color_btn.setObjectName("color_btn")
        self.horizontalLayout.addWidget(self.color_btn)
        self.name = QtWidgets.QLabel(ChannelDiplay)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.name.sizePolicy().hasHeightForWidth())
        self.name.setSizePolicy(sizePolicy)
        self.name.setMinimumSize(QtCore.QSize(0, 26))
        self.name.setTextFormat(QtCore.Qt.RichText)
        self.name.setObjectName("name")
        self.horizontalLayout.addWidget(self.name)
        self.value = QtWidgets.QLabel(ChannelDiplay)
        self.value.setMinimumSize(QtCore.QSize(75, 0))
        self.value.setTextFormat(QtCore.Qt.RichText)
        self.value.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.value.setObjectName("value")
        self.horizontalLayout.addWidget(self.value)
        self.horizontalLayout.setStretch(2, 1)

        self.retranslateUi(ChannelDiplay)
        QtCore.QMetaObject.connectSlotsByName(ChannelDiplay)

    def retranslateUi(self, ChannelDiplay):
        _translate = QtCore.QCoreApplication.translate
        ChannelDiplay.setWindowTitle(_translate("ChannelDiplay", "Form"))
        self.name.setText(_translate("ChannelDiplay", "<html><head/><body><p><span style=\" color:#ff0000;\">Channeqgl name</span></p></body></html>"))
        self.value.setText(_translate("ChannelDiplay", "<html><head/><body><p><span style=\" color:#ff0000;\">value</span></p></body></html>"))

