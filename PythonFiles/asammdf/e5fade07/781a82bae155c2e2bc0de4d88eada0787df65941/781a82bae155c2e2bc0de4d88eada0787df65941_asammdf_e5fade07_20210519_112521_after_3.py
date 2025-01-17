# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gps.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_GPSDisplay(object):
    def setupUi(self, GPSDisplay):
        GPSDisplay.setObjectName("GPSDisplay")
        GPSDisplay.resize(674, 154)
        self.gridLayout = QtWidgets.QGridLayout(GPSDisplay)
        self.gridLayout.setObjectName("gridLayout")
        self.load = QtWidgets.QPushButton(GPSDisplay)
        self.load.setObjectName("load")
        self.gridLayout.addWidget(self.load, 1, 0, 1, 1)
        self.longitude_channel = QtWidgets.QLineEdit(GPSDisplay)
        self.longitude_channel.setObjectName("longitude_channel")
        self.gridLayout.addWidget(self.longitude_channel, 2, 1, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.min_t = QtWidgets.QLabel(GPSDisplay)
        self.min_t.setText("")
        self.min_t.setObjectName("min_t")
        self.horizontalLayout_2.addWidget(self.min_t)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.max_t = QtWidgets.QLabel(GPSDisplay)
        self.max_t.setText("")
        self.max_t.setObjectName("max_t")
        self.horizontalLayout_2.addWidget(self.max_t)
        self.gridLayout.addLayout(self.horizontalLayout_2, 4, 0, 1, 2)
        self.latitude_channel = QtWidgets.QLineEdit(GPSDisplay)
        self.latitude_channel.setObjectName("latitude_channel")
        self.gridLayout.addWidget(self.latitude_channel, 1, 1, 1, 1)
        self.pushButton = QtWidgets.QPushButton(GPSDisplay)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout.addWidget(self.pushButton, 2, 0, 1, 1)
        self.timestamp_slider = QtWidgets.QSlider(GPSDisplay)
        self.timestamp_slider.setMaximum(9999)
        self.timestamp_slider.setOrientation(QtCore.Qt.Horizontal)
        self.timestamp_slider.setInvertedAppearance(False)
        self.timestamp_slider.setInvertedControls(False)
        self.timestamp_slider.setTickPosition(QtWidgets.QSlider.NoTicks)
        self.timestamp_slider.setTickInterval(1)
        self.timestamp_slider.setObjectName("timestamp_slider")
        self.gridLayout.addWidget(self.timestamp_slider, 5, 0, 1, 2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(GPSDisplay)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.timestamp = QtWidgets.QDoubleSpinBox(GPSDisplay)
        self.timestamp.setDecimals(9)
        self.timestamp.setSingleStep(0.001)
        self.timestamp.setObjectName("timestamp")
        self.horizontalLayout.addWidget(self.timestamp)
        self.gridLayout.addLayout(self.horizontalLayout, 3, 0, 1, 2)
        self.map_layout = QtWidgets.QVBoxLayout()
        self.map_layout.setObjectName("map_layout")
        self.gridLayout.addLayout(self.map_layout, 0, 0, 1, 2)
        self.gridLayout.setRowStretch(0, 1)

        self.retranslateUi(GPSDisplay)
        QtCore.QMetaObject.connectSlotsByName(GPSDisplay)
        GPSDisplay.setTabOrder(self.timestamp, self.timestamp_slider)

    def retranslateUi(self, GPSDisplay):
        _translate = QtCore.QCoreApplication.translate
        GPSDisplay.setWindowTitle(_translate("GPSDisplay", "Form"))
        self.load.setText(_translate("GPSDisplay", "Latitude"))
        self.pushButton.setText(_translate("GPSDisplay", "Longitude"))
        self.label.setText(_translate("GPSDisplay", "Time"))
        self.timestamp.setSuffix(_translate("GPSDisplay", "s"))
from . import resource_rc
