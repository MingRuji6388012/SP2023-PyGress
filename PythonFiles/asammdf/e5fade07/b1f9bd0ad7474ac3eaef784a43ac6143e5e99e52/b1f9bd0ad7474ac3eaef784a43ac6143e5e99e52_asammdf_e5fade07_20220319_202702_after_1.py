# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'numeric.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PySide6 import QtCore, QtGui, QtWidgets


class Ui_NumericDisplay(object):
    def setupUi(self, NumericDisplay):
        NumericDisplay.setObjectName("NumericDisplay")
        NumericDisplay.resize(480, 666)
        self.verticalLayout = QtWidgets.QVBoxLayout(NumericDisplay)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_4 = QtWidgets.QLabel(NumericDisplay)
        self.label_4.setObjectName("label_4")
        self.gridLayout_2.addWidget(self.label_4, 0, 0, 1, 1)
        self.mode_selection = QtWidgets.QComboBox(NumericDisplay)
        self.mode_selection.setObjectName("mode_selection")
        self.mode_selection.addItem("")
        self.mode_selection.addItem("")
        self.gridLayout_2.addWidget(self.mode_selection, 1, 0, 1, 1)
        self.label_5 = QtWidgets.QLabel(NumericDisplay)
        self.label_5.setObjectName("label_5")
        self.gridLayout_2.addWidget(self.label_5, 0, 1, 1, 1)
        self.format_selection = QtWidgets.QComboBox(NumericDisplay)
        self.format_selection.setObjectName("format_selection")
        self.format_selection.addItem("")
        self.format_selection.addItem("")
        self.format_selection.addItem("")
        self.gridLayout_2.addWidget(self.format_selection, 1, 1, 1, 1)
        self.label_6 = QtWidgets.QLabel(NumericDisplay)
        self.label_6.setObjectName("label_6")
        self.gridLayout_2.addWidget(self.label_6, 0, 2, 1, 1)
        self.float_precision = QtWidgets.QSpinBox(NumericDisplay)
        self.float_precision.setPrefix("")
        self.float_precision.setMaximum(15)
        self.float_precision.setProperty("value", 3)
        self.float_precision.setObjectName("float_precision")
        self.gridLayout_2.addWidget(self.float_precision, 1, 2, 1, 1)
        self.gridLayout_2.setColumnStretch(2, 1)
        self.verticalLayout.addLayout(self.gridLayout_2)
        self.channels = NumericTreeWidget(NumericDisplay)
        font = QtGui.QFont()
        font.setFamily("Lucida Console")
        self.channels.setFont(font)
        self.channels.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.channels.setAlternatingRowColors(True)
        self.channels.setColumnCount(3)
        self.channels.setObjectName("channels")
        self.verticalLayout.addWidget(self.channels)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.timestamp = QtWidgets.QDoubleSpinBox(NumericDisplay)
        self.timestamp.setDecimals(9)
        self.timestamp.setSingleStep(0.001)
        self.timestamp.setObjectName("timestamp")
        self.horizontalLayout.addWidget(self.timestamp)
        self.min_t = QtWidgets.QLabel(NumericDisplay)
        self.min_t.setText("")
        self.min_t.setObjectName("min_t")
        self.horizontalLayout.addWidget(self.min_t)
        self.timestamp_slider = QtWidgets.QSlider(NumericDisplay)
        self.timestamp_slider.setMaximum(99999)
        self.timestamp_slider.setOrientation(QtCore.Qt.Horizontal)
        self.timestamp_slider.setInvertedAppearance(False)
        self.timestamp_slider.setInvertedControls(False)
        self.timestamp_slider.setTickPosition(QtWidgets.QSlider.NoTicks)
        self.timestamp_slider.setTickInterval(1)
        self.timestamp_slider.setObjectName("timestamp_slider")
        self.horizontalLayout.addWidget(self.timestamp_slider)
        self.max_t = QtWidgets.QLabel(NumericDisplay)
        self.max_t.setText("")
        self.max_t.setObjectName("max_t")
        self.horizontalLayout.addWidget(self.max_t)
        self.horizontalLayout.setStretch(2, 1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.groupBox = QtWidgets.QGroupBox(NumericDisplay)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.pattern_match = QtWidgets.QLineEdit(self.groupBox)
        self.pattern_match.setObjectName("pattern_match")
        self.gridLayout.addWidget(self.pattern_match, 0, 0, 1, 1)
        self.op = QtWidgets.QComboBox(self.groupBox)
        self.op.setObjectName("op")
        self.op.addItem("")
        self.op.addItem("")
        self.op.addItem("")
        self.op.addItem("")
        self.op.addItem("")
        self.op.addItem("")
        self.gridLayout.addWidget(self.op, 0, 1, 1, 1)
        self.target = QtWidgets.QLineEdit(self.groupBox)
        self.target.setObjectName("target")
        self.gridLayout.addWidget(self.target, 0, 2, 1, 1)
        self.match = QtWidgets.QLabel(self.groupBox)
        self.match.setText("")
        self.match.setObjectName("match")
        self.gridLayout.addWidget(self.match, 1, 0, 1, 1)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.backward = QtWidgets.QPushButton(self.groupBox)
        self.backward.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/right.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.backward.setIcon(icon)
        self.backward.setObjectName("backward")
        self.horizontalLayout_3.addWidget(self.backward)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.forward = QtWidgets.QPushButton(self.groupBox)
        self.forward.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/left.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.forward.setIcon(icon1)
        self.forward.setObjectName("forward")
        self.horizontalLayout_3.addWidget(self.forward)
        self.gridLayout.addLayout(self.horizontalLayout_3, 1, 2, 1, 1)
        self.gridLayout.setColumnStretch(0, 1)
        self.verticalLayout.addWidget(self.groupBox)
        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(NumericDisplay)
        self.mode_selection.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(NumericDisplay)
        NumericDisplay.setTabOrder(self.timestamp, self.pattern_match)
        NumericDisplay.setTabOrder(self.pattern_match, self.op)
        NumericDisplay.setTabOrder(self.op, self.target)
        NumericDisplay.setTabOrder(self.target, self.backward)
        NumericDisplay.setTabOrder(self.backward, self.forward)
        NumericDisplay.setTabOrder(self.forward, self.channels)

    def retranslateUi(self, NumericDisplay):
        _translate = QtCore.QCoreApplication.translate
        NumericDisplay.setWindowTitle(_translate("NumericDisplay", "Form"))
        self.label_4.setText(_translate("NumericDisplay", "Samples mode"))
        self.mode_selection.setItemText(0, _translate("NumericDisplay", "raw values"))
        self.mode_selection.setItemText(1, _translate("NumericDisplay", "scaled values"))
        self.label_5.setText(_translate("NumericDisplay", "Integer format"))
        self.format_selection.setItemText(0, _translate("NumericDisplay", "phys"))
        self.format_selection.setItemText(1, _translate("NumericDisplay", "hex"))
        self.format_selection.setItemText(2, _translate("NumericDisplay", "bin"))
        self.label_6.setText(_translate("NumericDisplay", "Float precision"))
        self.float_precision.setSuffix(_translate("NumericDisplay", " decimals"))
        self.channels.headerItem().setText(0, _translate("NumericDisplay", "Name"))
        self.channels.headerItem().setText(1, _translate("NumericDisplay", "Value"))
        self.channels.headerItem().setText(2, _translate("NumericDisplay", "Unit"))
        self.timestamp.setSuffix(_translate("NumericDisplay", "s"))
        self.groupBox.setTitle(_translate("NumericDisplay", "Search for values"))
        self.pattern_match.setPlaceholderText(_translate("NumericDisplay", "pattern"))
        self.op.setItemText(0, _translate("NumericDisplay", "=="))
        self.op.setItemText(1, _translate("NumericDisplay", "!="))
        self.op.setItemText(2, _translate("NumericDisplay", "<"))
        self.op.setItemText(3, _translate("NumericDisplay", "<="))
        self.op.setItemText(4, _translate("NumericDisplay", ">"))
        self.op.setItemText(5, _translate("NumericDisplay", ">="))
        self.target.setPlaceholderText(_translate("NumericDisplay", "target value"))
from asammdf.gui.widgets.tree_numeric import NumericTreeWidget
from . import resource_rc
