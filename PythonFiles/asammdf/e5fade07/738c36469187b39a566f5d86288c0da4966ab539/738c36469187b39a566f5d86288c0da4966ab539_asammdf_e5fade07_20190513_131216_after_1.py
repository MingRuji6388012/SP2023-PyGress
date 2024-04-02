# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tabular.ui'
#
# Created by: PyQt5 UI code generator 5.12
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_TabularDisplay(object):
    def setupUi(self, TabularDisplay):
        TabularDisplay.setObjectName("TabularDisplay")
        TabularDisplay.resize(811, 636)
        self.gridLayout_2 = QtWidgets.QGridLayout(TabularDisplay)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.tree = QtWidgets.QTreeWidget(TabularDisplay)
        font = QtGui.QFont()
        font.setFamily("Lucida Console")
        self.tree.setFont(font)
        self.tree.setUniformRowHeights(True)
        self.tree.setObjectName("tree")
        self.tree.headerItem().setText(0, "1")
        self.gridLayout_2.addWidget(self.tree, 0, 0, 1, 3)
        self.add_filter_btn = QtWidgets.QPushButton(TabularDisplay)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/plus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.add_filter_btn.setIcon(icon)
        self.add_filter_btn.setObjectName("add_filter_btn")
        self.gridLayout_2.addWidget(self.add_filter_btn, 1, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(579, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 1, 1, 1, 1)
        self.apply_filters_btn = QtWidgets.QPushButton(TabularDisplay)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/filter.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.apply_filters_btn.setIcon(icon1)
        self.apply_filters_btn.setObjectName("apply_filters_btn")
        self.gridLayout_2.addWidget(self.apply_filters_btn, 1, 2, 1, 1)
        self.filters = ListWidget(TabularDisplay)
        self.filters.setObjectName("filters")
        self.gridLayout_2.addWidget(self.filters, 2, 0, 1, 3)
        self.groupBox = QtWidgets.QGroupBox(TabularDisplay)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.query = QtWidgets.QTextEdit(self.groupBox)
        self.query.setMinimumSize(QtCore.QSize(0, 7))
        font = QtGui.QFont()
        font.setFamily("Lucida Console")
        self.query.setFont(font)
        self.query.setStyleSheet("background-color: rgb(186, 186, 186);")
        self.query.setReadOnly(True)
        self.query.setObjectName("query")
        self.gridLayout.addWidget(self.query, 0, 0, 1, 1)
        self.gridLayout_2.addWidget(self.groupBox, 3, 0, 1, 3)
        self.gridLayout_2.setRowStretch(0, 5)

        self.retranslateUi(TabularDisplay)
        QtCore.QMetaObject.connectSlotsByName(TabularDisplay)

    def retranslateUi(self, TabularDisplay):
        _translate = QtCore.QCoreApplication.translate
        TabularDisplay.setWindowTitle(_translate("TabularDisplay", "Form"))
        self.add_filter_btn.setText(_translate("TabularDisplay", "Add new filter"))
        self.apply_filters_btn.setText(_translate("TabularDisplay", "Apply filters"))
        self.groupBox.setTitle(_translate("TabularDisplay", "pandas DataFrame query"))


from asammdf.gui.widgets.list import ListWidget
from . import resource_rc
