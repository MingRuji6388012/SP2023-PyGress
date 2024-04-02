# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets
from natsort import natsorted

from ..ui import resource_rc as resource_rc
from ..ui.tabular_filter import Ui_TabularFilter


class TabularFilter(Ui_TabularFilter, QtWidgets.QWidget):

    def __init__(self, signals, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        self._target = None

        self.names = [
            item[0]
            for item in signals
        ]

        self.dtype_kind = [
            item[1]
            for item in signals
        ]

        self.relation.addItems(['AND', 'OR'])
        self.column.addItems(self.names)
        self.op.addItems(['>', '>=', '<', '<=', '==', '!='])

        self.target.editingFinished.connect(self.validate_target)
        self.column.currentIndexChanged.connect(self.column_changed)

    def column_changed(self, index):
        self.target.setText('')
        self._target = None

    def validate_target(self):
        idx = self.column.currentIndex()
        column_name = self.column.currentText()
        kind = self.dtype_kind[idx]
        target = self.target.text().strip()

        if target:

            if kind in 'ui':
                if target.startswith('0x'):
                    try:
                        self._target = int(target, 16)
                    except:
                        QtWidgets.QMessageBox.warning(
                            None,
                            "Wrong target value",
                            f'{column_name} requires an integer target value',
                        )
                else:
                    try:
                        self._target = int(target)
                    except:
                        try:
                            self._target = int(target, 16)
                            self.target.setText(f'0x{self._target:X}')
                        except:
                            QtWidgets.QMessageBox.warning(
                                None,
                                "Wrong target value",
                                f'{column_name} requires an integer target value',
                            )
            elif kind == 'f':
                try:
                    self._target = float(target)
                except:
                    QtWidgets.QMessageBox.warning(
                        None,
                        "Wrong target value",
                        f'{column_name} requires a float target value',
                    )
