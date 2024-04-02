# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'file_widget.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_file_widget(object):
    def setupUi(self, file_widget):
        file_widget.setObjectName("file_widget")
        file_widget.resize(1034, 865)
        self.verticalLayout = QtWidgets.QVBoxLayout(file_widget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.aspects = QtWidgets.QTabWidget(file_widget)
        self.aspects.setTabPosition(QtWidgets.QTabWidget.West)
        self.aspects.setDocumentMode(False)
        self.aspects.setObjectName("aspects")
        self.channels_tab = QtWidgets.QWidget()
        self.channels_tab.setObjectName("channels_tab")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.channels_tab)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.splitter = QtWidgets.QSplitter(self.channels_tab)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.channel_view = QtWidgets.QComboBox(self.verticalLayoutWidget)
        self.channel_view.setObjectName("channel_view")
        self.channel_view.addItem("")
        self.channel_view.addItem("")
        self.channel_view.addItem("")
        self.verticalLayout_4.addWidget(self.channel_view)
        self.channels_tree = TreeWidget(self.verticalLayoutWidget)
        self.channels_tree.setObjectName("channels_tree")
        self.verticalLayout_4.addWidget(self.channels_tree)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.load_channel_list_btn = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.load_channel_list_btn.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/open.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.load_channel_list_btn.setIcon(icon)
        self.load_channel_list_btn.setObjectName("load_channel_list_btn")
        self.horizontalLayout_2.addWidget(self.load_channel_list_btn)
        self.save_channel_list_btn = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.save_channel_list_btn.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/save.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.save_channel_list_btn.setIcon(icon1)
        self.save_channel_list_btn.setObjectName("save_channel_list_btn")
        self.horizontalLayout_2.addWidget(self.save_channel_list_btn)
        self.select_all_btn = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.select_all_btn.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/checkmark.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.select_all_btn.setIcon(icon2)
        self.select_all_btn.setObjectName("select_all_btn")
        self.horizontalLayout_2.addWidget(self.select_all_btn)
        self.clear_channels_btn = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.clear_channels_btn.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/erase.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.clear_channels_btn.setIcon(icon3)
        self.clear_channels_btn.setObjectName("clear_channels_btn")
        self.horizontalLayout_2.addWidget(self.clear_channels_btn)
        self.advanced_search_btn = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.advanced_search_btn.setText("")
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/search.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.advanced_search_btn.setIcon(icon4)
        self.advanced_search_btn.setObjectName("advanced_search_btn")
        self.horizontalLayout_2.addWidget(self.advanced_search_btn)
        self.create_window_btn = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.create_window_btn.setText("")
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/graph.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.create_window_btn.setIcon(icon5)
        self.create_window_btn.setObjectName("create_window_btn")
        self.horizontalLayout_2.addWidget(self.create_window_btn)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.verticalLayout_4.addLayout(self.horizontalLayout_2)
        self.verticalLayout_5.addWidget(self.splitter)
        self.aspects.addTab(self.channels_tab, icon5, "")
        self.modify = QtWidgets.QWidget()
        self.modify.setObjectName("modify")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.modify)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.filter_view = QtWidgets.QComboBox(self.modify)
        self.filter_view.setObjectName("filter_view")
        self.filter_view.addItem("")
        self.filter_view.addItem("")
        self.filter_view.addItem("")
        self.verticalLayout_2.addWidget(self.filter_view)
        self.filter_tree = TreeWidget(self.modify)
        self.filter_tree.setObjectName("filter_tree")
        self.verticalLayout_2.addWidget(self.filter_tree)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.load_filter_list_btn = QtWidgets.QPushButton(self.modify)
        self.load_filter_list_btn.setText("")
        self.load_filter_list_btn.setIcon(icon)
        self.load_filter_list_btn.setObjectName("load_filter_list_btn")
        self.horizontalLayout_4.addWidget(self.load_filter_list_btn)
        self.save_filter_list_btn = QtWidgets.QPushButton(self.modify)
        self.save_filter_list_btn.setText("")
        self.save_filter_list_btn.setIcon(icon1)
        self.save_filter_list_btn.setObjectName("save_filter_list_btn")
        self.horizontalLayout_4.addWidget(self.save_filter_list_btn)
        self.clear_filter_btn = QtWidgets.QPushButton(self.modify)
        self.clear_filter_btn.setText("")
        self.clear_filter_btn.setIcon(icon3)
        self.clear_filter_btn.setObjectName("clear_filter_btn")
        self.horizontalLayout_4.addWidget(self.clear_filter_btn)
        self.advanced_serch_filter_btn = QtWidgets.QPushButton(self.modify)
        self.advanced_serch_filter_btn.setText("")
        self.advanced_serch_filter_btn.setIcon(icon4)
        self.advanced_serch_filter_btn.setObjectName("advanced_serch_filter_btn")
        self.horizontalLayout_4.addWidget(self.advanced_serch_filter_btn)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem1)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_6 = QtWidgets.QVBoxLayout()
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.label = QtWidgets.QLabel(self.modify)
        self.label.setObjectName("label")
        self.verticalLayout_6.addWidget(self.label)
        self.selected_filter_channels = QtWidgets.QListWidget(self.modify)
        self.selected_filter_channels.setViewMode(QtWidgets.QListView.ListMode)
        self.selected_filter_channels.setUniformItemSizes(True)
        self.selected_filter_channels.setObjectName("selected_filter_channels")
        self.verticalLayout_6.addWidget(self.selected_filter_channels)
        self.horizontalLayout.addLayout(self.verticalLayout_6)
        spacerItem2 = QtWidgets.QSpacerItem(40, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.cut_group = QtWidgets.QGroupBox(self.modify)
        self.cut_group.setCheckable(True)
        self.cut_group.setChecked(False)
        self.cut_group.setObjectName("cut_group")
        self.gridLayout_19 = QtWidgets.QGridLayout(self.cut_group)
        self.gridLayout_19.setObjectName("gridLayout_19")
        self.label_59 = QtWidgets.QLabel(self.cut_group)
        self.label_59.setObjectName("label_59")
        self.gridLayout_19.addWidget(self.label_59, 0, 0, 1, 1)
        self.cut_stop = QtWidgets.QDoubleSpinBox(self.cut_group)
        self.cut_stop.setDecimals(6)
        self.cut_stop.setMaximum(999999.999999)
        self.cut_stop.setObjectName("cut_stop")
        self.gridLayout_19.addWidget(self.cut_stop, 1, 1, 1, 1)
        self.whence = QtWidgets.QCheckBox(self.cut_group)
        self.whence.setObjectName("whence")
        self.gridLayout_19.addWidget(self.whence, 3, 0, 1, 1)
        self.label_60 = QtWidgets.QLabel(self.cut_group)
        self.label_60.setObjectName("label_60")
        self.gridLayout_19.addWidget(self.label_60, 1, 0, 1, 1)
        self.cut_start = QtWidgets.QDoubleSpinBox(self.cut_group)
        self.cut_start.setDecimals(6)
        self.cut_start.setMaximum(999999.999999)
        self.cut_start.setObjectName("cut_start")
        self.gridLayout_19.addWidget(self.cut_start, 0, 1, 1, 1)
        self.cut_time_from_zero = QtWidgets.QCheckBox(self.cut_group)
        self.cut_time_from_zero.setObjectName("cut_time_from_zero")
        self.gridLayout_19.addWidget(self.cut_time_from_zero, 4, 0, 1, 1)
        self.verticalLayout_3.addWidget(self.cut_group)
        self.resample_group = QtWidgets.QGroupBox(self.modify)
        self.resample_group.setCheckable(True)
        self.resample_group.setChecked(False)
        self.resample_group.setObjectName("resample_group")
        self.gridLayout_21 = QtWidgets.QGridLayout(self.resample_group)
        self.gridLayout_21.setObjectName("gridLayout_21")
        self.raster_type_step = QtWidgets.QRadioButton(self.resample_group)
        self.raster_type_step.setChecked(True)
        self.raster_type_step.setObjectName("raster_type_step")
        self.gridLayout_21.addWidget(self.raster_type_step, 0, 0, 1, 1)
        self.raster = QtWidgets.QDoubleSpinBox(self.resample_group)
        self.raster.setMinimumSize(QtCore.QSize(100, 0))
        self.raster.setDecimals(6)
        self.raster.setMinimum(1e-06)
        self.raster.setObjectName("raster")
        self.gridLayout_21.addWidget(self.raster, 0, 1, 1, 1)
        self.resample_time_from_zero = QtWidgets.QCheckBox(self.resample_group)
        self.resample_time_from_zero.setObjectName("resample_time_from_zero")
        self.gridLayout_21.addWidget(self.resample_time_from_zero, 3, 0, 1, 1)
        self.raster_type_channel = QtWidgets.QRadioButton(self.resample_group)
        self.raster_type_channel.setObjectName("raster_type_channel")
        self.gridLayout_21.addWidget(self.raster_type_channel, 2, 0, 1, 1)
        self.raster_channel = QtWidgets.QComboBox(self.resample_group)
        self.raster_channel.setEnabled(False)
        self.raster_channel.setInsertPolicy(QtWidgets.QComboBox.InsertAtBottom)
        self.raster_channel.setObjectName("raster_channel")
        self.gridLayout_21.addWidget(self.raster_channel, 2, 1, 1, 1)
        self.raster_search_btn = QtWidgets.QPushButton(self.resample_group)
        self.raster_search_btn.setText("")
        self.raster_search_btn.setIcon(icon4)
        self.raster_search_btn.setObjectName("raster_search_btn")
        self.gridLayout_21.addWidget(self.raster_search_btn, 2, 2, 1, 1)
        self.gridLayout_21.setColumnStretch(1, 1)
        self.verticalLayout_3.addWidget(self.resample_group)
        self.groupBox_10 = QtWidgets.QGroupBox(self.modify)
        self.groupBox_10.setObjectName("groupBox_10")
        self.verticalLayout_20 = QtWidgets.QVBoxLayout(self.groupBox_10)
        self.verticalLayout_20.setObjectName("verticalLayout_20")
        self.output_format = QtWidgets.QComboBox(self.groupBox_10)
        self.output_format.setObjectName("output_format")
        self.output_format.addItem("")
        self.output_format.addItem("")
        self.output_format.addItem("")
        self.output_format.addItem("")
        self.output_format.addItem("")
        self.verticalLayout_20.addWidget(self.output_format)
        self.output_options = QtWidgets.QStackedWidget(self.groupBox_10)
        self.output_options.setObjectName("output_options")
        self.MDF = QtWidgets.QWidget()
        self.MDF.setObjectName("MDF")
        self.gridLayout_22 = QtWidgets.QGridLayout(self.MDF)
        self.gridLayout_22.setObjectName("gridLayout_22")
        self.line_14 = QtWidgets.QFrame(self.MDF)
        self.line_14.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_14.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_14.setObjectName("line_14")
        self.gridLayout_22.addWidget(self.line_14, 1, 0, 1, 2)
        self.label_28 = QtWidgets.QLabel(self.MDF)
        self.label_28.setObjectName("label_28")
        self.gridLayout_22.addWidget(self.label_28, 4, 0, 1, 1)
        self.mdf_compression = QtWidgets.QComboBox(self.MDF)
        self.mdf_compression.setObjectName("mdf_compression")
        self.gridLayout_22.addWidget(self.mdf_compression, 2, 1, 1, 1)
        self.mdf_split = QtWidgets.QCheckBox(self.MDF)
        self.mdf_split.setChecked(True)
        self.mdf_split.setObjectName("mdf_split")
        self.gridLayout_22.addWidget(self.mdf_split, 3, 0, 1, 1)
        self.label_29 = QtWidgets.QLabel(self.MDF)
        self.label_29.setObjectName("label_29")
        self.gridLayout_22.addWidget(self.label_29, 2, 0, 1, 1)
        self.mdf_version = QtWidgets.QComboBox(self.MDF)
        self.mdf_version.setMinimumSize(QtCore.QSize(200, 0))
        self.mdf_version.setObjectName("mdf_version")
        self.gridLayout_22.addWidget(self.mdf_version, 0, 1, 1, 1)
        self.mdf_split_size = QtWidgets.QDoubleSpinBox(self.MDF)
        self.mdf_split_size.setMaximum(4.0)
        self.mdf_split_size.setObjectName("mdf_split_size")
        self.gridLayout_22.addWidget(self.mdf_split_size, 4, 1, 1, 1)
        self.label_27 = QtWidgets.QLabel(self.MDF)
        self.label_27.setObjectName("label_27")
        self.gridLayout_22.addWidget(self.label_27, 0, 0, 1, 1)
        self.groupBox_9 = QtWidgets.QGroupBox(self.MDF)
        self.groupBox_9.setObjectName("groupBox_9")
        self.gridLayout_20 = QtWidgets.QGridLayout(self.groupBox_9)
        self.gridLayout_20.setObjectName("gridLayout_20")
        self.scramble_btn = QtWidgets.QPushButton(self.groupBox_9)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(":/scramble.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.scramble_btn.setIcon(icon6)
        self.scramble_btn.setObjectName("scramble_btn")
        self.gridLayout_20.addWidget(self.scramble_btn, 1, 0, 1, 1)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_20.addItem(spacerItem3, 1, 1, 1, 1)
        self.label_61 = QtWidgets.QLabel(self.groupBox_9)
        self.label_61.setWordWrap(True)
        self.label_61.setObjectName("label_61")
        self.gridLayout_20.addWidget(self.label_61, 0, 0, 1, 2)
        self.gridLayout_22.addWidget(self.groupBox_9, 6, 0, 1, 2)
        spacerItem4 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_22.addItem(spacerItem4, 5, 1, 1, 1)
        self.output_options.addWidget(self.MDF)
        self.HDF5 = QtWidgets.QWidget()
        self.HDF5.setObjectName("HDF5")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.HDF5)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.time_as_date = QtWidgets.QCheckBox(self.HDF5)
        self.time_as_date.setObjectName("time_as_date")
        self.gridLayout_2.addWidget(self.time_as_date, 2, 0, 1, 1)
        self.line_30 = QtWidgets.QFrame(self.HDF5)
        self.line_30.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_30.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_30.setObjectName("line_30")
        self.gridLayout_2.addWidget(self.line_30, 3, 0, 1, 2)
        self.empty_channels = QtWidgets.QComboBox(self.HDF5)
        self.empty_channels.setObjectName("empty_channels")
        self.gridLayout_2.addWidget(self.empty_channels, 7, 1, 1, 1)
        self.use_display_names = QtWidgets.QCheckBox(self.HDF5)
        self.use_display_names.setObjectName("use_display_names")
        self.gridLayout_2.addWidget(self.use_display_names, 4, 0, 1, 1)
        self.label_67 = QtWidgets.QLabel(self.HDF5)
        self.label_67.setObjectName("label_67")
        self.gridLayout_2.addWidget(self.label_67, 6, 0, 1, 1)
        self.single_time_base = QtWidgets.QCheckBox(self.HDF5)
        self.single_time_base.setObjectName("single_time_base")
        self.gridLayout_2.addWidget(self.single_time_base, 0, 0, 1, 1)
        self.time_from_zero = QtWidgets.QCheckBox(self.HDF5)
        self.time_from_zero.setObjectName("time_from_zero")
        self.gridLayout_2.addWidget(self.time_from_zero, 1, 0, 1, 1)
        self.label_65 = QtWidgets.QLabel(self.HDF5)
        self.label_65.setObjectName("label_65")
        self.gridLayout_2.addWidget(self.label_65, 7, 0, 1, 1)
        self.reduce_memory_usage = QtWidgets.QCheckBox(self.HDF5)
        self.reduce_memory_usage.setObjectName("reduce_memory_usage")
        self.gridLayout_2.addWidget(self.reduce_memory_usage, 5, 0, 1, 1)
        self.export_compression = QtWidgets.QComboBox(self.HDF5)
        self.export_compression.setObjectName("export_compression")
        self.gridLayout_2.addWidget(self.export_compression, 6, 1, 1, 1)
        spacerItem5 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem5, 8, 0, 1, 1)
        self.output_options.addWidget(self.HDF5)
        self.MAT = QtWidgets.QWidget()
        self.MAT.setObjectName("MAT")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.MAT)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.empty_channels_mat = QtWidgets.QComboBox(self.MAT)
        self.empty_channels_mat.setObjectName("empty_channels_mat")
        self.gridLayout_3.addWidget(self.empty_channels_mat, 7, 1, 1, 1)
        self.label_69 = QtWidgets.QLabel(self.MAT)
        self.label_69.setObjectName("label_69")
        self.gridLayout_3.addWidget(self.label_69, 8, 0, 1, 1)
        self.oned_as = QtWidgets.QComboBox(self.MAT)
        self.oned_as.setObjectName("oned_as")
        self.gridLayout_3.addWidget(self.oned_as, 9, 1, 1, 1)
        self.use_display_names_mat = QtWidgets.QCheckBox(self.MAT)
        self.use_display_names_mat.setObjectName("use_display_names_mat")
        self.gridLayout_3.addWidget(self.use_display_names_mat, 4, 0, 1, 1)
        self.reduce_memory_usage_mat = QtWidgets.QCheckBox(self.MAT)
        self.reduce_memory_usage_mat.setObjectName("reduce_memory_usage_mat")
        self.gridLayout_3.addWidget(self.reduce_memory_usage_mat, 5, 0, 1, 1)
        self.label_19 = QtWidgets.QLabel(self.MAT)
        self.label_19.setObjectName("label_19")
        self.gridLayout_3.addWidget(self.label_19, 9, 0, 1, 1)
        self.time_as_date_mat = QtWidgets.QCheckBox(self.MAT)
        self.time_as_date_mat.setObjectName("time_as_date_mat")
        self.gridLayout_3.addWidget(self.time_as_date_mat, 2, 0, 1, 1)
        self.time_from_zero_mat = QtWidgets.QCheckBox(self.MAT)
        self.time_from_zero_mat.setObjectName("time_from_zero_mat")
        self.gridLayout_3.addWidget(self.time_from_zero_mat, 1, 0, 1, 1)
        self.label_68 = QtWidgets.QLabel(self.MAT)
        self.label_68.setObjectName("label_68")
        self.gridLayout_3.addWidget(self.label_68, 7, 0, 1, 1)
        spacerItem6 = QtWidgets.QSpacerItem(20, 2, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_3.addItem(spacerItem6, 10, 0, 1, 1)
        self.line_31 = QtWidgets.QFrame(self.MAT)
        self.line_31.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_31.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_31.setObjectName("line_31")
        self.gridLayout_3.addWidget(self.line_31, 3, 0, 1, 2)
        self.mat_format = QtWidgets.QComboBox(self.MAT)
        self.mat_format.setObjectName("mat_format")
        self.gridLayout_3.addWidget(self.mat_format, 8, 1, 1, 1)
        self.single_time_base_mat = QtWidgets.QCheckBox(self.MAT)
        self.single_time_base_mat.setObjectName("single_time_base_mat")
        self.gridLayout_3.addWidget(self.single_time_base_mat, 0, 0, 1, 1)
        self.export_compression_mat = QtWidgets.QComboBox(self.MAT)
        self.export_compression_mat.setObjectName("export_compression_mat")
        self.gridLayout_3.addWidget(self.export_compression_mat, 6, 1, 1, 1)
        self.label_70 = QtWidgets.QLabel(self.MAT)
        self.label_70.setObjectName("label_70")
        self.gridLayout_3.addWidget(self.label_70, 6, 0, 1, 1)
        self.output_options.addWidget(self.MAT)
        self.verticalLayout_20.addWidget(self.output_options)
        self.verticalLayout_3.addWidget(self.groupBox_10)
        spacerItem7 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem7)
        self.apply_btn = QtWidgets.QPushButton(self.modify)
        self.apply_btn.setIcon(icon2)
        self.apply_btn.setObjectName("apply_btn")
        self.verticalLayout_3.addWidget(self.apply_btn)
        self.verticalLayout_3.setStretch(3, 1)
        self.horizontalLayout.addLayout(self.verticalLayout_3)
        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 1)
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(":/convert.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.aspects.addTab(self.modify, icon7, "")
        self.extract_can_tab = QtWidgets.QWidget()
        self.extract_can_tab.setObjectName("extract_can_tab")
        self.gridLayout_8 = QtWidgets.QGridLayout(self.extract_can_tab)
        self.gridLayout_8.setObjectName("gridLayout_8")
        self.groupBox_3 = QtWidgets.QGroupBox(self.extract_can_tab)
        self.groupBox_3.setObjectName("groupBox_3")
        self.gridLayout_7 = QtWidgets.QGridLayout(self.groupBox_3)
        self.gridLayout_7.setObjectName("gridLayout_7")
        self.line_13 = QtWidgets.QFrame(self.groupBox_3)
        self.line_13.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_13.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_13.setObjectName("line_13")
        self.gridLayout_7.addWidget(self.line_13, 7, 1, 1, 3)
        self.extract_can_csv_btn = QtWidgets.QPushButton(self.groupBox_3)
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap(":/csv.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.extract_can_csv_btn.setIcon(icon8)
        self.extract_can_csv_btn.setObjectName("extract_can_csv_btn")
        self.gridLayout_7.addWidget(self.extract_can_csv_btn, 8, 1, 1, 1)
        self.label_25 = QtWidgets.QLabel(self.groupBox_3)
        self.label_25.setObjectName("label_25")
        self.gridLayout_7.addWidget(self.label_25, 5, 1, 1, 1)
        self.single_time_base_can = QtWidgets.QCheckBox(self.groupBox_3)
        self.single_time_base_can.setObjectName("single_time_base_can")
        self.gridLayout_7.addWidget(self.single_time_base_can, 0, 1, 1, 1)
        self.label_23 = QtWidgets.QLabel(self.groupBox_3)
        self.label_23.setObjectName("label_23")
        self.gridLayout_7.addWidget(self.label_23, 4, 1, 1, 1)
        self.export_raster_can = QtWidgets.QDoubleSpinBox(self.groupBox_3)
        self.export_raster_can.setDecimals(6)
        self.export_raster_can.setObjectName("export_raster_can")
        self.gridLayout_7.addWidget(self.export_raster_can, 4, 2, 1, 2)
        self.ignore_invalid_signals_csv = QtWidgets.QCheckBox(self.groupBox_3)
        self.ignore_invalid_signals_csv.setObjectName("ignore_invalid_signals_csv")
        self.gridLayout_7.addWidget(self.ignore_invalid_signals_csv, 3, 1, 1, 1)
        self.empty_channels_can = QtWidgets.QComboBox(self.groupBox_3)
        self.empty_channels_can.setObjectName("empty_channels_can")
        self.gridLayout_7.addWidget(self.empty_channels_can, 5, 2, 1, 2)
        self.time_from_zero_can = QtWidgets.QCheckBox(self.groupBox_3)
        self.time_from_zero_can.setObjectName("time_from_zero_can")
        self.gridLayout_7.addWidget(self.time_from_zero_can, 1, 1, 1, 1)
        self.can_time_as_date = QtWidgets.QCheckBox(self.groupBox_3)
        self.can_time_as_date.setObjectName("can_time_as_date")
        self.gridLayout_7.addWidget(self.can_time_as_date, 2, 1, 1, 1)
        self.gridLayout_8.addWidget(self.groupBox_3, 2, 1, 1, 1)
        self.load_can_database_btn = QtWidgets.QPushButton(self.extract_can_tab)
        self.load_can_database_btn.setIcon(icon)
        self.load_can_database_btn.setObjectName("load_can_database_btn")
        self.gridLayout_8.addWidget(self.load_can_database_btn, 0, 0, 1, 1)
        self.groupBox_2 = QtWidgets.QGroupBox(self.extract_can_tab)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.extract_can_btn = QtWidgets.QPushButton(self.groupBox_2)
        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap(":/down.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.extract_can_btn.setIcon(icon9)
        self.extract_can_btn.setObjectName("extract_can_btn")
        self.gridLayout_5.addWidget(self.extract_can_btn, 5, 0, 1, 2)
        self.label__1 = QtWidgets.QLabel(self.groupBox_2)
        self.label__1.setObjectName("label__1")
        self.gridLayout_5.addWidget(self.label__1, 0, 0, 1, 1)
        self.extract_can_compression = QtWidgets.QComboBox(self.groupBox_2)
        self.extract_can_compression.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.extract_can_compression.setObjectName("extract_can_compression")
        self.gridLayout_5.addWidget(self.extract_can_compression, 0, 1, 1, 1)
        self.extract_can_format = QtWidgets.QComboBox(self.groupBox_2)
        self.extract_can_format.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.extract_can_format.setObjectName("extract_can_format")
        self.gridLayout_5.addWidget(self.extract_can_format, 1, 1, 1, 1)
        self.label_24 = QtWidgets.QLabel(self.groupBox_2)
        self.label_24.setObjectName("label_24")
        self.gridLayout_5.addWidget(self.label_24, 1, 0, 1, 1)
        self.ignore_invalid_signals_mdf = QtWidgets.QCheckBox(self.groupBox_2)
        self.ignore_invalid_signals_mdf.setObjectName("ignore_invalid_signals_mdf")
        self.gridLayout_5.addWidget(self.ignore_invalid_signals_mdf, 2, 0, 1, 2)
        self.label_26 = QtWidgets.QLabel(self.groupBox_2)
        self.label_26.setText("")
        self.label_26.setObjectName("label_26")
        self.gridLayout_5.addWidget(self.label_26, 3, 0, 1, 1)
        self.line_12 = QtWidgets.QFrame(self.groupBox_2)
        self.line_12.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_12.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_12.setObjectName("line_12")
        self.gridLayout_5.addWidget(self.line_12, 4, 0, 1, 2)
        self.gridLayout_8.addWidget(self.groupBox_2, 2, 0, 1, 1)
        self.can_database_list = MinimalListWidget(self.extract_can_tab)
        self.can_database_list.setObjectName("can_database_list")
        self.gridLayout_8.addWidget(self.can_database_list, 1, 0, 1, 2)
        self.output_info_can = QtWidgets.QTextEdit(self.extract_can_tab)
        self.output_info_can.setReadOnly(True)
        self.output_info_can.setObjectName("output_info_can")
        self.gridLayout_8.addWidget(self.output_info_can, 1, 2, 2, 2)
        self.aspects.addTab(self.extract_can_tab, icon9, "")
        self.info_tab = QtWidgets.QWidget()
        self.info_tab.setObjectName("info_tab")
        self.gridLayout_9 = QtWidgets.QGridLayout(self.info_tab)
        self.gridLayout_9.setObjectName("gridLayout_9")
        self.info = QtWidgets.QTreeWidget(self.info_tab)
        self.info.setUniformRowHeights(False)
        self.info.setObjectName("info")
        self.gridLayout_9.addWidget(self.info, 0, 0, 1, 1)
        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap(":/info.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.aspects.addTab(self.info_tab, icon10, "")
        self.attachments_tab = QtWidgets.QWidget()
        self.attachments_tab.setObjectName("attachments_tab")
        self.verticalLayout_10 = QtWidgets.QVBoxLayout(self.attachments_tab)
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.attachments = QtWidgets.QListWidget(self.attachments_tab)
        self.attachments.setObjectName("attachments")
        self.verticalLayout_10.addWidget(self.attachments)
        icon11 = QtGui.QIcon()
        icon11.addPixmap(QtGui.QPixmap(":/attach.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.aspects.addTab(self.attachments_tab, icon11, "")
        self.verticalLayout.addWidget(self.aspects)

        self.retranslateUi(file_widget)
        self.aspects.setCurrentIndex(0)
        self.output_options.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(file_widget)

    def retranslateUi(self, file_widget):
        _translate = QtCore.QCoreApplication.translate
        file_widget.setWindowTitle(_translate("file_widget", "Form"))
        self.aspects.setToolTip(_translate("file_widget", "Load channel selection list"))
        self.channel_view.setItemText(0, _translate("file_widget", "Natural sort"))
        self.channel_view.setItemText(1, _translate("file_widget", "Internal file structure"))
        self.channel_view.setItemText(2, _translate("file_widget", "Selected channels only"))
        self.channels_tree.setToolTip(_translate("file_widget", "Double click channel to see extended information"))
        self.channels_tree.headerItem().setText(0, _translate("file_widget", "Channels"))
        self.load_channel_list_btn.setToolTip(_translate("file_widget", "Load channel selection list"))
        self.save_channel_list_btn.setToolTip(_translate("file_widget", "Save channel selection list"))
        self.select_all_btn.setToolTip(_translate("file_widget", "Select all the channels"))
        self.clear_channels_btn.setToolTip(_translate("file_widget", "Clear all selected channels"))
        self.advanced_search_btn.setToolTip(_translate("file_widget", "Search and select channels"))
        self.create_window_btn.setToolTip(_translate("file_widget", "Create window"))
        self.aspects.setTabText(self.aspects.indexOf(self.channels_tab), _translate("file_widget", "Channels"))
        self.filter_view.setItemText(0, _translate("file_widget", "Natural sort"))
        self.filter_view.setItemText(1, _translate("file_widget", "Internal file structure"))
        self.filter_view.setItemText(2, _translate("file_widget", "Selected channels only"))
        self.filter_tree.setToolTip(_translate("file_widget", "Double click channel to see extended information"))
        self.filter_tree.headerItem().setText(0, _translate("file_widget", "Channels"))
        self.load_filter_list_btn.setToolTip(_translate("file_widget", "Load channel selection list"))
        self.save_filter_list_btn.setToolTip(_translate("file_widget", "Save channel selection list"))
        self.clear_filter_btn.setToolTip(_translate("file_widget", "Clear selection"))
        self.advanced_serch_filter_btn.setToolTip(_translate("file_widget", "Search and select channels"))
        self.label.setText(_translate("file_widget", "All selected channels"))
        self.selected_filter_channels.setSortingEnabled(True)
        self.cut_group.setTitle(_translate("file_widget", "Cut"))
        self.label_59.setText(_translate("file_widget", "Start"))
        self.cut_stop.setSuffix(_translate("file_widget", "s"))
        self.whence.setText(_translate("file_widget", "Start relative to first time stamp"))
        self.label_60.setText(_translate("file_widget", "End"))
        self.cut_start.setSuffix(_translate("file_widget", "s"))
        self.cut_time_from_zero.setText(_translate("file_widget", "Time from 0s"))
        self.resample_group.setTitle(_translate("file_widget", "Resample"))
        self.raster_type_step.setText(_translate("file_widget", "step"))
        self.raster.setSuffix(_translate("file_widget", "s"))
        self.resample_time_from_zero.setText(_translate("file_widget", "Time from 0s"))
        self.raster_type_channel.setText(_translate("file_widget", "channel"))
        self.raster_search_btn.setToolTip(_translate("file_widget", "Search raster channel"))
        self.groupBox_10.setTitle(_translate("file_widget", "Ouput format"))
        self.output_format.setItemText(0, _translate("file_widget", "MDF"))
        self.output_format.setItemText(1, _translate("file_widget", "CSV"))
        self.output_format.setItemText(2, _translate("file_widget", "HDF5"))
        self.output_format.setItemText(3, _translate("file_widget", "MAT"))
        self.output_format.setItemText(4, _translate("file_widget", "Parquet"))
        self.label_28.setText(_translate("file_widget", "Split size "))
        self.mdf_split.setText(_translate("file_widget", "Split data blocks"))
        self.label_29.setText(_translate("file_widget", "Compression"))
        self.mdf_split_size.setSuffix(_translate("file_widget", "MB"))
        self.label_27.setText(_translate("file_widget", "Version"))
        self.groupBox_9.setTitle(_translate("file_widget", "Scramble"))
        self.scramble_btn.setText(_translate("file_widget", "Scramble texts"))
        self.label_61.setText(_translate("file_widget", "Anonymize the measurements: scramble all texts and replace them with random strings"))
        self.time_as_date.setText(_translate("file_widget", "Time as date"))
        self.use_display_names.setText(_translate("file_widget", "Use display names"))
        self.label_67.setText(_translate("file_widget", "Compression"))
        self.single_time_base.setText(_translate("file_widget", "Single time base"))
        self.time_from_zero.setText(_translate("file_widget", "Time from 0s"))
        self.label_65.setText(_translate("file_widget", "Empty channels"))
        self.reduce_memory_usage.setText(_translate("file_widget", "Reduce  memory usage"))
        self.label_69.setText(_translate("file_widget", ".mat format"))
        self.use_display_names_mat.setText(_translate("file_widget", "Use display names"))
        self.reduce_memory_usage_mat.setText(_translate("file_widget", "Reduce  memory usage"))
        self.label_19.setText(_translate("file_widget", ".mat oned_as"))
        self.time_as_date_mat.setText(_translate("file_widget", "Time as date"))
        self.time_from_zero_mat.setText(_translate("file_widget", "Time from 0s"))
        self.label_68.setText(_translate("file_widget", "Empty channels"))
        self.single_time_base_mat.setText(_translate("file_widget", "Single time base"))
        self.label_70.setText(_translate("file_widget", "Compression"))
        self.apply_btn.setText(_translate("file_widget", "Apply"))
        self.aspects.setTabText(self.aspects.indexOf(self.modify), _translate("file_widget", "Modify && Export"))
        self.groupBox_3.setTitle(_translate("file_widget", "CSV"))
        self.extract_can_csv_btn.setText(_translate("file_widget", "Export to CSV         "))
        self.label_25.setText(_translate("file_widget", "Empty channels"))
        self.single_time_base_can.setText(_translate("file_widget", "Single time base"))
        self.label_23.setText(_translate("file_widget", "Raster"))
        self.export_raster_can.setSuffix(_translate("file_widget", "s"))
        self.ignore_invalid_signals_csv.setToolTip(_translate("file_widget", "checks if all samples are eauql to the maximum teoretical signal value"))
        self.ignore_invalid_signals_csv.setText(_translate("file_widget", "Ignore invalid signals"))
        self.time_from_zero_can.setText(_translate("file_widget", "Time from 0s"))
        self.can_time_as_date.setText(_translate("file_widget", "Time as date"))
        self.load_can_database_btn.setText(_translate("file_widget", "Load CAN database"))
        self.groupBox_2.setTitle(_translate("file_widget", "MDF"))
        self.extract_can_btn.setText(_translate("file_widget", "Extract CAN signals"))
        self.label__1.setText(_translate("file_widget", "Compression"))
        self.label_24.setText(_translate("file_widget", "Version"))
        self.ignore_invalid_signals_mdf.setToolTip(_translate("file_widget", "checks if all samples are eauql to the maximum teoretical signal value"))
        self.ignore_invalid_signals_mdf.setText(_translate("file_widget", "Ignore invalid signals"))
        self.aspects.setTabText(self.aspects.indexOf(self.extract_can_tab), _translate("file_widget", "CAN Logging"))
        self.info.headerItem().setText(0, _translate("file_widget", "Cathegory"))
        self.info.headerItem().setText(1, _translate("file_widget", "Value"))
        self.aspects.setTabText(self.aspects.indexOf(self.info_tab), _translate("file_widget", "Info"))
        self.aspects.setTabText(self.aspects.indexOf(self.attachments_tab), _translate("file_widget", "Attachments"))

from asammdf.gui.widgets.list import MinimalListWidget
from asammdf.gui.widgets.tree import TreeWidget
from . import resource_rc
