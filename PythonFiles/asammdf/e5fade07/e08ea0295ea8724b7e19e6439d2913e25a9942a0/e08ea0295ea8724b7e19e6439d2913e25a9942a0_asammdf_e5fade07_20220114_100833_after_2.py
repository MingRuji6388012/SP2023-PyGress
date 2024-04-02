# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'search_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.5
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_SearchDialog(object):
    def setupUi(self, SearchDialog):
        SearchDialog.setObjectName("SearchDialog")
        SearchDialog.resize(1134, 679)
        SearchDialog.setSizeGripEnabled(True)
        self.gridLayout_2 = QtWidgets.QGridLayout(SearchDialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.tabs = QtWidgets.QTabWidget(SearchDialog)
        self.tabs.setObjectName("tabs")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.gridLayout = QtWidgets.QGridLayout(self.tab)
        self.gridLayout.setObjectName("gridLayout")
        self.match_kind = QtWidgets.QComboBox(self.tab)
        self.match_kind.setObjectName("match_kind")
        self.match_kind.addItem("")
        self.match_kind.addItem("")
        self.gridLayout.addWidget(self.match_kind, 0, 2, 1, 1)
        self.search_box = QtWidgets.QLineEdit(self.tab)
        self.search_box.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.search_box.setInputMask("")
        self.search_box.setText("")
        self.search_box.setObjectName("search_box")
        self.gridLayout.addWidget(self.search_box, 0, 0, 1, 1)
        self.selection = QtWidgets.QTreeWidget(self.tab)
        self.selection.setObjectName("selection")
        self.selection.header().setMinimumSectionSize(25)
        self.selection.header().setSortIndicatorShown(False)
        self.gridLayout.addWidget(self.selection, 5, 0, 1, 3)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.cancel_btn = QtWidgets.QPushButton(self.tab)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/erase.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.cancel_btn.setIcon(icon)
        self.cancel_btn.setObjectName("cancel_btn")
        self.horizontalLayout.addWidget(self.cancel_btn)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.apply_btn = QtWidgets.QPushButton(self.tab)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/checkmark.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.apply_btn.setIcon(icon1)
        self.apply_btn.setObjectName("apply_btn")
        self.horizontalLayout.addWidget(self.apply_btn)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.add_window_btn = QtWidgets.QPushButton(self.tab)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/plus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.add_window_btn.setIcon(icon2)
        self.add_window_btn.setObjectName("add_window_btn")
        self.horizontalLayout.addWidget(self.add_window_btn)
        self.horizontalLayout.setStretch(1, 1)
        self.gridLayout.addLayout(self.horizontalLayout, 6, 0, 1, 3)
        self.matches = QtWidgets.QTreeWidget(self.tab)
        self.matches.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.matches.setUniformRowHeights(False)
        self.matches.setObjectName("matches")
        self.matches.header().setMinimumSectionSize(40)
        self.matches.header().setStretchLastSection(True)
        self.gridLayout.addWidget(self.matches, 2, 0, 1, 3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem2 = QtWidgets.QSpacerItem(358, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.add_btn = QtWidgets.QPushButton(self.tab)
        self.add_btn.setFocusPolicy(QtCore.Qt.TabFocus)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/shift_down.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.add_btn.setIcon(icon3)
        self.add_btn.setObjectName("add_btn")
        self.horizontalLayout_2.addWidget(self.add_btn)
        spacerItem3 = QtWidgets.QSpacerItem(358, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)
        self.gridLayout.addLayout(self.horizontalLayout_2, 3, 0, 1, 3)
        self.label = QtWidgets.QLabel(self.tab)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 4, 0, 1, 1)
        self.label_7 = QtWidgets.QLabel(self.tab)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 1, 0, 1, 1)
        self.status = QtWidgets.QLabel(self.tab)
        self.status.setMinimumSize(QtCore.QSize(100, 0))
        self.status.setObjectName("status")
        self.gridLayout.addWidget(self.status, 0, 1, 1, 1)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/search.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.tabs.addTab(self.tab, icon4, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.tab_2)
        self.gridLayout_3.setObjectName("gridLayout_3")
        spacerItem4 = QtWidgets.QSpacerItem(20, 254, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_3.addItem(spacerItem4, 7, 1, 1, 1)
        self.raw = QtWidgets.QCheckBox(self.tab_2)
        self.raw.setObjectName("raw")
        self.gridLayout_3.addWidget(self.raw, 5, 2, 1, 1)
        self.filter_value = QtWidgets.QDoubleSpinBox(self.tab_2)
        self.filter_value.setDecimals(6)
        self.filter_value.setMinimum(-1e+31)
        self.filter_value.setMaximum(1e+24)
        self.filter_value.setObjectName("filter_value")
        self.gridLayout_3.addWidget(self.filter_value, 4, 2, 1, 1)
        self.filter_type = QtWidgets.QComboBox(self.tab_2)
        self.filter_type.setObjectName("filter_type")
        self.filter_type.addItem("")
        self.filter_type.addItem("")
        self.filter_type.addItem("")
        self.filter_type.addItem("")
        self.gridLayout_3.addWidget(self.filter_type, 3, 2, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.tab_2)
        self.label_3.setObjectName("label_3")
        self.gridLayout_3.addWidget(self.label_3, 3, 1, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.tab_2)
        self.label_4.setObjectName("label_4")
        self.gridLayout_3.addWidget(self.label_4, 4, 1, 1, 1)
        spacerItem5 = QtWidgets.QSpacerItem(282, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_3.addItem(spacerItem5, 8, 3, 1, 1)
        self.define_ranges_btn = QtWidgets.QPushButton(self.tab_2)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/range.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.define_ranges_btn.setIcon(icon5)
        self.define_ranges_btn.setObjectName("define_ranges_btn")
        self.gridLayout_3.addWidget(self.define_ranges_btn, 6, 2, 1, 1)
        self.apply_pattern_btn = QtWidgets.QPushButton(self.tab_2)
        self.apply_pattern_btn.setIcon(icon1)
        self.apply_pattern_btn.setObjectName("apply_pattern_btn")
        self.gridLayout_3.addWidget(self.apply_pattern_btn, 8, 4, 1, 1)
        self.cancel_pattern_btn = QtWidgets.QPushButton(self.tab_2)
        self.cancel_pattern_btn.setIcon(icon)
        self.cancel_pattern_btn.setObjectName("cancel_pattern_btn")
        self.gridLayout_3.addWidget(self.cancel_pattern_btn, 8, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.tab_2)
        self.label_2.setObjectName("label_2")
        self.gridLayout_3.addWidget(self.label_2, 1, 1, 1, 1)
        self.pattern = QtWidgets.QLineEdit(self.tab_2)
        self.pattern.setMinimumSize(QtCore.QSize(300, 0))
        self.pattern.setObjectName("pattern")
        self.gridLayout_3.addWidget(self.pattern, 1, 2, 1, 1)
        self.pattern_match_type = QtWidgets.QComboBox(self.tab_2)
        self.pattern_match_type.setObjectName("pattern_match_type")
        self.pattern_match_type.addItem("")
        self.pattern_match_type.addItem("")
        self.gridLayout_3.addWidget(self.pattern_match_type, 2, 2, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.tab_2)
        self.label_5.setObjectName("label_5")
        self.gridLayout_3.addWidget(self.label_5, 2, 1, 1, 1)
        self.label_6 = QtWidgets.QLabel(self.tab_2)
        self.label_6.setObjectName("label_6")
        self.gridLayout_3.addWidget(self.label_6, 0, 1, 1, 1)
        self.name = QtWidgets.QLineEdit(self.tab_2)
        self.name.setObjectName("name")
        self.gridLayout_3.addWidget(self.name, 0, 2, 1, 1)
        self.gridLayout_3.setColumnStretch(3, 1)
        self.gridLayout_3.setRowStretch(4, 1)
        self.tabs.addTab(self.tab_2, "")
        self.gridLayout_2.addWidget(self.tabs, 0, 0, 1, 1)

        self.retranslateUi(SearchDialog)
        self.tabs.setCurrentIndex(0)
        self.match_kind.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(SearchDialog)
        SearchDialog.setTabOrder(self.search_box, self.matches)
        SearchDialog.setTabOrder(self.matches, self.add_btn)
        SearchDialog.setTabOrder(self.add_btn, self.selection)
        SearchDialog.setTabOrder(self.selection, self.cancel_btn)
        SearchDialog.setTabOrder(self.cancel_btn, self.apply_btn)
        SearchDialog.setTabOrder(self.apply_btn, self.add_window_btn)
        SearchDialog.setTabOrder(self.add_window_btn, self.match_kind)
        SearchDialog.setTabOrder(self.match_kind, self.tabs)
        SearchDialog.setTabOrder(self.tabs, self.raw)
        SearchDialog.setTabOrder(self.raw, self.filter_value)
        SearchDialog.setTabOrder(self.filter_value, self.filter_type)
        SearchDialog.setTabOrder(self.filter_type, self.define_ranges_btn)
        SearchDialog.setTabOrder(self.define_ranges_btn, self.apply_pattern_btn)
        SearchDialog.setTabOrder(self.apply_pattern_btn, self.cancel_pattern_btn)
        SearchDialog.setTabOrder(self.cancel_pattern_btn, self.pattern)
        SearchDialog.setTabOrder(self.pattern, self.pattern_match_type)
        SearchDialog.setTabOrder(self.pattern_match_type, self.name)

    def retranslateUi(self, SearchDialog):
        _translate = QtCore.QCoreApplication.translate
        SearchDialog.setWindowTitle(_translate("SearchDialog", "Dialog"))
        self.match_kind.setItemText(0, _translate("SearchDialog", "Wildcard"))
        self.match_kind.setItemText(1, _translate("SearchDialog", "Regex"))
        self.search_box.setPlaceholderText(_translate("SearchDialog", "channel name pattern"))
        self.selection.setSortingEnabled(False)
        self.selection.headerItem().setText(0, _translate("SearchDialog", "Name"))
        self.selection.headerItem().setText(1, _translate("SearchDialog", "Group"))
        self.selection.headerItem().setText(2, _translate("SearchDialog", "Index"))
        self.selection.headerItem().setText(3, _translate("SearchDialog", "Source name"))
        self.selection.headerItem().setText(4, _translate("SearchDialog", "Source path"))
        self.selection.headerItem().setText(5, _translate("SearchDialog", "Comment"))
        self.cancel_btn.setText(_translate("SearchDialog", "Cancel"))
        self.apply_btn.setText(_translate("SearchDialog", "Apply"))
        self.add_window_btn.setText(_translate("SearchDialog", "Add window"))
        self.matches.setSortingEnabled(False)
        self.matches.headerItem().setText(0, _translate("SearchDialog", "Name"))
        self.matches.headerItem().setText(1, _translate("SearchDialog", "Group"))
        self.matches.headerItem().setText(2, _translate("SearchDialog", "Index"))
        self.matches.headerItem().setText(3, _translate("SearchDialog", "Source name"))
        self.matches.headerItem().setText(4, _translate("SearchDialog", "Source path"))
        self.matches.headerItem().setText(5, _translate("SearchDialog", "Comment"))
        self.add_btn.setText(_translate("SearchDialog", "Add to selection"))
        self.label.setText(_translate("SearchDialog", "Final selection"))
        self.label_7.setText(_translate("SearchDialog", "Search results"))
        self.status.setText(_translate("SearchDialog", "No results"))
        self.tabs.setTabText(self.tabs.indexOf(self.tab), _translate("SearchDialog", "Search"))
        self.raw.setText(_translate("SearchDialog", "Asses the raw channel values"))
        self.filter_type.setItemText(0, _translate("SearchDialog", "Unspecified"))
        self.filter_type.setItemText(1, _translate("SearchDialog", "Contains"))
        self.filter_type.setItemText(2, _translate("SearchDialog", "Do not contain"))
        self.filter_type.setItemText(3, _translate("SearchDialog", "Constant"))
        self.label_3.setText(_translate("SearchDialog", "Filter type"))
        self.label_4.setText(_translate("SearchDialog", "Filter value"))
        self.define_ranges_btn.setText(_translate("SearchDialog", "Define ranges"))
        self.apply_pattern_btn.setText(_translate("SearchDialog", "Apply"))
        self.cancel_pattern_btn.setText(_translate("SearchDialog", "Cancel"))
        self.label_2.setText(_translate("SearchDialog", "Pattern"))
        self.pattern.setPlaceholderText(_translate("SearchDialog", "channel name pattern"))
        self.pattern_match_type.setItemText(0, _translate("SearchDialog", "Wildcard"))
        self.pattern_match_type.setItemText(1, _translate("SearchDialog", "Regex"))
        self.label_5.setText(_translate("SearchDialog", "Match type"))
        self.label_6.setText(_translate("SearchDialog", "Name"))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_2), _translate("SearchDialog", "Pattern definition"))
from . import resource_rc
