# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'channel_group_display_widget.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ChannelGroupDisplay(object):
    def setupUi(self, ChannelGroupDisplay):
        ChannelGroupDisplay.setObjectName("ChannelGroupDisplay")
        ChannelGroupDisplay.resize(643, 35)
        ChannelGroupDisplay.setMinimumSize(QtCore.QSize(40, 35))
        self.verticalLayout = QtWidgets.QVBoxLayout(ChannelGroupDisplay)
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.verticalLayout.setContentsMargins(2, 2, 2, 5)
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self._icon = QtWidgets.QLabel(ChannelGroupDisplay)
        self._icon.setMinimumSize(QtCore.QSize(16, 16))
        self._icon.setMaximumSize(QtCore.QSize(24, 24))
        self._icon.setText("")
        self._icon.setPixmap(QtGui.QPixmap(":/open.png"))
        self._icon.setScaledContents(True)
        self._icon.setObjectName("_icon")
        self.horizontalLayout.addWidget(self._icon)
        self.range_indicator = QtWidgets.QLabel(ChannelGroupDisplay)
        self.range_indicator.setMinimumSize(QtCore.QSize(16, 16))
        self.range_indicator.setMaximumSize(QtCore.QSize(16, 16))
        self.range_indicator.setText("")
        self.range_indicator.setPixmap(QtGui.QPixmap(":/paint.png"))
        self.range_indicator.setScaledContents(True)
        self.range_indicator.setObjectName("range_indicator")
        self.horizontalLayout.addWidget(self.range_indicator)
        self.name = QtWidgets.QLabel(ChannelGroupDisplay)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.name.sizePolicy().hasHeightForWidth())
        self.name.setSizePolicy(sizePolicy)
        self.name.setMinimumSize(QtCore.QSize(0, 30))
        self.name.setMouseTracking(False)
        self.name.setText("")
        self.name.setTextFormat(QtCore.Qt.PlainText)
        self.name.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse)
        self.name.setObjectName("name")
        self.horizontalLayout.addWidget(self.name)
        self.horizontalLayout.setStretch(2, 1)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(ChannelGroupDisplay)
        QtCore.QMetaObject.connectSlotsByName(ChannelGroupDisplay)

    def retranslateUi(self, ChannelGroupDisplay):
        _translate = QtCore.QCoreApplication.translate
        ChannelGroupDisplay.setWindowTitle(_translate("ChannelGroupDisplay", "Form"))
from . import resource_rc
