# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'define_channel_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.3.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QDoubleSpinBox,
    QGridLayout, QGroupBox, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QRadioButton, QSizePolicy,
    QSpacerItem, QSpinBox, QTabWidget, QTextEdit,
    QWidget)
from . import resource_rc

class Ui_ComputedChannel(object):
    def setupUi(self, ComputedChannel):
        if not ComputedChannel.objectName():
            ComputedChannel.setObjectName(u"ComputedChannel")
        ComputedChannel.resize(699, 501)
        ComputedChannel.setMaximumSize(QSize(16777215, 16777215))
        icon = QIcon()
        icon.addFile(u":/plus.png", QSize(), QIcon.Normal, QIcon.Off)
        ComputedChannel.setWindowIcon(icon)
        ComputedChannel.setSizeGripEnabled(True)
        self.gridLayout = QGridLayout(ComputedChannel)
        self.gridLayout.setObjectName(u"gridLayout")
        self.tabs = QTabWidget(ComputedChannel)
        self.tabs.setObjectName(u"tabs")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.gridLayout_5 = QGridLayout(self.tab)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.groupBox = QGroupBox(self.tab)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_4 = QGridLayout(self.groupBox)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.operand1_as_signal = QRadioButton(self.groupBox)
        self.operand1_as_signal.setObjectName(u"operand1_as_signal")
        self.operand1_as_signal.setChecked(True)

        self.gridLayout_4.addWidget(self.operand1_as_signal, 0, 0, 1, 1)

        self.operand1_name = QLineEdit(self.groupBox)
        self.operand1_name.setObjectName(u"operand1_name")

        self.gridLayout_4.addWidget(self.operand1_name, 0, 1, 1, 2)

        self.operand1_search_btn = QPushButton(self.groupBox)
        self.operand1_search_btn.setObjectName(u"operand1_search_btn")
        icon1 = QIcon()
        icon1.addFile(u":/search.png", QSize(), QIcon.Normal, QIcon.Off)
        self.operand1_search_btn.setIcon(icon1)

        self.gridLayout_4.addWidget(self.operand1_search_btn, 0, 3, 1, 1)

        self.operand1_as_integer = QRadioButton(self.groupBox)
        self.operand1_as_integer.setObjectName(u"operand1_as_integer")

        self.gridLayout_4.addWidget(self.operand1_as_integer, 1, 0, 1, 1)

        self.operand1_integer = QSpinBox(self.groupBox)
        self.operand1_integer.setObjectName(u"operand1_integer")
        self.operand1_integer.setMinimumSize(QSize(200, 0))
        self.operand1_integer.setMinimum(0)
        self.operand1_integer.setMaximum(10)
        self.operand1_integer.setValue(0)

        self.gridLayout_4.addWidget(self.operand1_integer, 1, 1, 1, 1)

        self.horizontalSpacer = QSpacerItem(538, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout_4.addItem(self.horizontalSpacer, 1, 2, 2, 1)

        self.operand1_as_float = QRadioButton(self.groupBox)
        self.operand1_as_float.setObjectName(u"operand1_as_float")

        self.gridLayout_4.addWidget(self.operand1_as_float, 2, 0, 1, 1)

        self.operand1_float = QDoubleSpinBox(self.groupBox)
        self.operand1_float.setObjectName(u"operand1_float")
        self.operand1_float.setDecimals(6)

        self.gridLayout_4.addWidget(self.operand1_float, 2, 1, 1, 1)

        self.gridLayout_4.setColumnStretch(2, 1)

        self.gridLayout_5.addWidget(self.groupBox, 0, 0, 1, 2)

        self.op = QComboBox(self.tab)
        self.op.setObjectName(u"op")

        self.gridLayout_5.addWidget(self.op, 1, 0, 1, 1)

        self.horizontalSpacer_5 = QSpacerItem(794, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout_5.addItem(self.horizontalSpacer_5, 1, 1, 1, 1)

        self.groupBox_2 = QGroupBox(self.tab)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.gridLayout_3 = QGridLayout(self.groupBox_2)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.operand2_as_signal = QRadioButton(self.groupBox_2)
        self.operand2_as_signal.setObjectName(u"operand2_as_signal")
        self.operand2_as_signal.setChecked(True)

        self.gridLayout_3.addWidget(self.operand2_as_signal, 0, 0, 1, 1)

        self.operand2_name = QLineEdit(self.groupBox_2)
        self.operand2_name.setObjectName(u"operand2_name")

        self.gridLayout_3.addWidget(self.operand2_name, 0, 1, 1, 2)

        self.operand2_search_btn = QPushButton(self.groupBox_2)
        self.operand2_search_btn.setObjectName(u"operand2_search_btn")
        self.operand2_search_btn.setIcon(icon1)

        self.gridLayout_3.addWidget(self.operand2_search_btn, 0, 3, 1, 1)

        self.operand2_as_integer = QRadioButton(self.groupBox_2)
        self.operand2_as_integer.setObjectName(u"operand2_as_integer")

        self.gridLayout_3.addWidget(self.operand2_as_integer, 1, 0, 1, 1)

        self.operand2_integer = QSpinBox(self.groupBox_2)
        self.operand2_integer.setObjectName(u"operand2_integer")
        self.operand2_integer.setMinimumSize(QSize(200, 0))

        self.gridLayout_3.addWidget(self.operand2_integer, 1, 1, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(63, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer_2, 1, 2, 1, 1)

        self.operand2_as_float = QRadioButton(self.groupBox_2)
        self.operand2_as_float.setObjectName(u"operand2_as_float")

        self.gridLayout_3.addWidget(self.operand2_as_float, 2, 0, 1, 1)

        self.operand2_float = QDoubleSpinBox(self.groupBox_2)
        self.operand2_float.setObjectName(u"operand2_float")
        self.operand2_float.setDecimals(6)

        self.gridLayout_3.addWidget(self.operand2_float, 2, 1, 1, 1)

        self.gridLayout_3.setColumnStretch(2, 1)

        self.gridLayout_5.addWidget(self.groupBox_2, 2, 0, 1, 2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_5.addItem(self.verticalSpacer, 5, 0, 1, 1)

        self.gridLayout_5.setColumnStretch(1, 1)
        self.tabs.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.gridLayout_6 = QGridLayout(self.tab_2)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.label_2 = QLabel(self.tab_2)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_6.addWidget(self.label_2, 0, 0, 1, 1)

        self.label_3 = QLabel(self.tab_2)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_6.addWidget(self.label_3, 1, 0, 1, 1)

        self.first_function_argument = QDoubleSpinBox(self.tab_2)
        self.first_function_argument.setObjectName(u"first_function_argument")

        self.gridLayout_6.addWidget(self.first_function_argument, 1, 1, 1, 1)

        self.horizontalSpacer_4 = QSpacerItem(286, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout_6.addItem(self.horizontalSpacer_4, 1, 2, 1, 1)

        self.label_4 = QLabel(self.tab_2)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_6.addWidget(self.label_4, 2, 0, 1, 1)

        self.second_function_argument = QDoubleSpinBox(self.tab_2)
        self.second_function_argument.setObjectName(u"second_function_argument")

        self.gridLayout_6.addWidget(self.second_function_argument, 2, 1, 1, 1)

        self.label_5 = QLabel(self.tab_2)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout_6.addWidget(self.label_5, 3, 0, 1, 1)

        self.function_channel = QLineEdit(self.tab_2)
        self.function_channel.setObjectName(u"function_channel")

        self.gridLayout_6.addWidget(self.function_channel, 3, 1, 1, 2)

        self.function_search_btn = QPushButton(self.tab_2)
        self.function_search_btn.setObjectName(u"function_search_btn")
        self.function_search_btn.setIcon(icon1)

        self.gridLayout_6.addWidget(self.function_search_btn, 3, 3, 1, 1)

        self.function = QComboBox(self.tab_2)
        self.function.setObjectName(u"function")
        self.function.setMinimumSize(QSize(380, 20))

        self.gridLayout_6.addWidget(self.function, 0, 1, 1, 1)

        self.help = QTextEdit(self.tab_2)
        self.help.setObjectName(u"help")

        self.gridLayout_6.addWidget(self.help, 4, 0, 1, 4)

        self.gridLayout_6.setColumnStretch(2, 1)
        self.tabs.addTab(self.tab_2, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.gridLayout_2 = QGridLayout(self.tab_3)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label = QLabel(self.tab_3)
        self.label.setObjectName(u"label")
        self.label.setTextFormat(Qt.RichText)

        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 2)

        self.expression = QPlainTextEdit(self.tab_3)
        self.expression.setObjectName(u"expression")

        self.gridLayout_2.addWidget(self.expression, 2, 0, 1, 2)

        self.expression_search_btn = QPushButton(self.tab_3)
        self.expression_search_btn.setObjectName(u"expression_search_btn")
        self.expression_search_btn.setIcon(icon1)

        self.gridLayout_2.addWidget(self.expression_search_btn, 1, 0, 1, 1)

        self.gridLayout_2.setColumnStretch(1, 1)
        self.tabs.addTab(self.tab_3, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.gridLayout_7 = QGridLayout(self.tab_4)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.python_function = QPlainTextEdit(self.tab_4)
        self.python_function.setObjectName(u"python_function")

        self.gridLayout_7.addWidget(self.python_function, 1, 0, 1, 3)

        self.python_function_search_btn = QPushButton(self.tab_4)
        self.python_function_search_btn.setObjectName(u"python_function_search_btn")
        self.python_function_search_btn.setIcon(icon1)

        self.gridLayout_7.addWidget(self.python_function_search_btn, 0, 0, 1, 1)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout_7.addItem(self.horizontalSpacer_6, 0, 2, 1, 1)

        self.check_syntax_btn = QPushButton(self.tab_4)
        self.check_syntax_btn.setObjectName(u"check_syntax_btn")
        icon2 = QIcon()
        icon2.addFile(u":/checkmark.png", QSize(), QIcon.Normal, QIcon.Off)
        self.check_syntax_btn.setIcon(icon2)

        self.gridLayout_7.addWidget(self.check_syntax_btn, 0, 1, 1, 1)

        self.tabs.addTab(self.tab_4, "")

        self.gridLayout.addWidget(self.tabs, 0, 0, 1, 5)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_3, 6, 1, 1, 1)

        self.label_7 = QLabel(ComputedChannel)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout.addWidget(self.label_7, 2, 0, 1, 1)

        self.unit = QLineEdit(ComputedChannel)
        self.unit.setObjectName(u"unit")

        self.gridLayout.addWidget(self.unit, 5, 1, 1, 1)

        self.apply_btn = QPushButton(ComputedChannel)
        self.apply_btn.setObjectName(u"apply_btn")

        self.gridLayout.addWidget(self.apply_btn, 6, 3, 1, 1)

        self.comment = QPlainTextEdit(ComputedChannel)
        self.comment.setObjectName(u"comment")

        self.gridLayout.addWidget(self.comment, 4, 1, 1, 4)

        self.label_8 = QLabel(ComputedChannel)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.gridLayout.addWidget(self.label_8, 4, 0, 1, 1)

        self.cancel_btn = QPushButton(ComputedChannel)
        self.cancel_btn.setObjectName(u"cancel_btn")

        self.gridLayout.addWidget(self.cancel_btn, 6, 4, 1, 1)

        self.label_6 = QLabel(ComputedChannel)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout.addWidget(self.label_6, 5, 0, 1, 1)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_7, 6, 2, 1, 1)

        self.name = QLineEdit(ComputedChannel)
        self.name.setObjectName(u"name")

        self.gridLayout.addWidget(self.name, 2, 1, 1, 4)

        self.groupBox_3 = QGroupBox(ComputedChannel)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.gridLayout_8 = QGridLayout(self.groupBox_3)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.gridLayout_8.addItem(self.horizontalSpacer_8, 1, 2, 1, 1)

        self.trigger_interval = QDoubleSpinBox(self.groupBox_3)
        self.trigger_interval.setObjectName(u"trigger_interval")
        self.trigger_interval.setDecimals(6)
        self.trigger_interval.setMinimum(0.000001000000000)
        self.trigger_interval.setMaximum(10.000000000000000)
        self.trigger_interval.setSingleStep(0.100000000000000)
        self.trigger_interval.setValue(0.010000000000000)

        self.gridLayout_8.addWidget(self.trigger_interval, 1, 1, 1, 1)

        self.trigger_channel = QLineEdit(self.groupBox_3)
        self.trigger_channel.setObjectName(u"trigger_channel")

        self.gridLayout_8.addWidget(self.trigger_channel, 4, 1, 1, 2)

        self.triggering_on_channel = QRadioButton(self.groupBox_3)
        self.triggering_on_channel.setObjectName(u"triggering_on_channel")

        self.gridLayout_8.addWidget(self.triggering_on_channel, 4, 0, 1, 1)

        self.triggering_on_interval = QRadioButton(self.groupBox_3)
        self.triggering_on_interval.setObjectName(u"triggering_on_interval")

        self.gridLayout_8.addWidget(self.triggering_on_interval, 1, 0, 1, 1)

        self.trigger_search_btn = QPushButton(self.groupBox_3)
        self.trigger_search_btn.setObjectName(u"trigger_search_btn")
        self.trigger_search_btn.setIcon(icon1)

        self.gridLayout_8.addWidget(self.trigger_search_btn, 4, 3, 1, 1)

        self.triggering_on_all = QRadioButton(self.groupBox_3)
        self.triggering_on_all.setObjectName(u"triggering_on_all")
        self.triggering_on_all.setChecked(True)

        self.gridLayout_8.addWidget(self.triggering_on_all, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.groupBox_3, 1, 0, 1, 5)

        self.gridLayout.setColumnStretch(2, 1)

        self.retranslateUi(ComputedChannel)

        self.tabs.setCurrentIndex(3)


        QMetaObject.connectSlotsByName(ComputedChannel)
    # setupUi

    def retranslateUi(self, ComputedChannel):
        ComputedChannel.setWindowTitle(QCoreApplication.translate("ComputedChannel", u"Define new channel", None))
        self.groupBox.setTitle(QCoreApplication.translate("ComputedChannel", u"First operand", None))
        self.operand1_as_signal.setText(QCoreApplication.translate("ComputedChannel", u"Signal", None))
        self.operand1_name.setPlaceholderText(QCoreApplication.translate("ComputedChannel", u"first operand name", None))
        self.operand1_search_btn.setText("")
        self.operand1_as_integer.setText(QCoreApplication.translate("ComputedChannel", u"Integer", None))
        self.operand1_as_float.setText(QCoreApplication.translate("ComputedChannel", u"Float", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("ComputedChannel", u"Second operand", None))
        self.operand2_as_signal.setText(QCoreApplication.translate("ComputedChannel", u"Signal", None))
        self.operand2_name.setPlaceholderText(QCoreApplication.translate("ComputedChannel", u"second operand name", None))
        self.operand2_search_btn.setText("")
        self.operand2_as_integer.setText(QCoreApplication.translate("ComputedChannel", u"Integer", None))
        self.operand2_as_float.setText(QCoreApplication.translate("ComputedChannel", u"Float", None))
        self.tabs.setTabText(self.tabs.indexOf(self.tab), QCoreApplication.translate("ComputedChannel", u"Simple computation", None))
        self.label_2.setText(QCoreApplication.translate("ComputedChannel", u"Function", None))
        self.label_3.setText(QCoreApplication.translate("ComputedChannel", u"First function argument", None))
        self.label_4.setText(QCoreApplication.translate("ComputedChannel", u"Second function argument", None))
        self.label_5.setText(QCoreApplication.translate("ComputedChannel", u"Channel name", None))
        self.function_channel.setPlaceholderText(QCoreApplication.translate("ComputedChannel", u"input channel name", None))
        self.function_search_btn.setText("")
#if QT_CONFIG(tooltip)
        self.function.setToolTip(QCoreApplication.translate("ComputedChannel", u"see numpy documentation", None))
#endif // QT_CONFIG(tooltip)
        self.help.setPlaceholderText(QCoreApplication.translate("ComputedChannel", u"selected function help ", None))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_2), QCoreApplication.translate("ComputedChannel", u"Numpy function", None))
        self.label.setText(QCoreApplication.translate("ComputedChannel", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">The expression is evaluated using the <span style=\" font-style:italic;\">numexpr </span>library. Have a look at the <a href=\"https://numexpr.readthedocs.io/projects/NumExpr3/en/latest/user_guide.html\"><span style=\" text-decoration: underline; color:#0000ff;\">Numexpr documentation</span></a> for supported operators and function.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:"
                        "0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">The signal names must be enclosed by double curly braces: <span style=\" font-weight:600; color:#ff0000;\">{{</span>Signal_name<span style=\" font-weight:600; color:#ff0000;\">}}</span></p></body></html>", None))
        self.expression.setPlaceholderText(QCoreApplication.translate("ComputedChannel", u"enter your expression here. Example: ({{Sig1}} + {{Sig2}}) / ({{Sig3}} - {{Sig4}}) + 7.8", None))
        self.expression_search_btn.setText(QCoreApplication.translate("ComputedChannel", u"Available channels", None))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_3), QCoreApplication.translate("ComputedChannel", u"Expression", None))
        self.python_function.setPlaceholderText(QCoreApplication.translate("ComputedChannel", u"The virtual channel definition is written as a Python function. The device signal names must be placed inside double curly braces: {{MAIN_CLOCK}}. Use the 'return' statement to return a value, otherwise 'None' will automatically be returned by the function.  Here is a minimalistic example:   if {{MAIN_CLOCK}} > 5000:     return 0 else:     avg = ({{p_FL}} + {{p_FR}} + {{p_RL}} + {{p_RR}}) / 4          if avg > 20.5 and {{VehicleSpeed}} < 100:         return avg     else:         return avg + 9", None))
        self.python_function_search_btn.setText(QCoreApplication.translate("ComputedChannel", u"Available channels", None))
        self.check_syntax_btn.setText(QCoreApplication.translate("ComputedChannel", u"Check syntax", None))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_4), QCoreApplication.translate("ComputedChannel", u"Python function", None))
        self.label_7.setText(QCoreApplication.translate("ComputedChannel", u"Computed channel name", None))
        self.unit.setPlaceholderText("")
        self.apply_btn.setText(QCoreApplication.translate("ComputedChannel", u"Apply", None))
        self.label_8.setText(QCoreApplication.translate("ComputedChannel", u"Computed channel comment", None))
        self.cancel_btn.setText(QCoreApplication.translate("ComputedChannel", u"Cancel", None))
        self.label_6.setText(QCoreApplication.translate("ComputedChannel", u"Computed channel unit", None))
        self.name.setInputMask("")
        self.name.setText("")
        self.name.setPlaceholderText("")
        self.groupBox_3.setTitle(QCoreApplication.translate("ComputedChannel", u"Triggering", None))
        self.trigger_interval.setSuffix(QCoreApplication.translate("ComputedChannel", u"s", None))
        self.triggering_on_channel.setText(QCoreApplication.translate("ComputedChannel", u"on channel", None))
        self.triggering_on_interval.setText(QCoreApplication.translate("ComputedChannel", u"time interval", None))
        self.trigger_search_btn.setText("")
        self.triggering_on_all.setText(QCoreApplication.translate("ComputedChannel", u"all channels timestamps", None))
    # retranslateUi

