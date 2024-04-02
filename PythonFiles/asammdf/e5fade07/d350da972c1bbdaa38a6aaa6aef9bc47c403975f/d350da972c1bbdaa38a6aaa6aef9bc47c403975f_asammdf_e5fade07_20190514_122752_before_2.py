# -*- coding: utf-8 -*-
import logging
from traceback import format_exc

from PyQt5 import QtWidgets
from PyQt5 import QtCore
import pandas as pd

from ..ui import resource_rc as resource_rc
from ..ui.tabular import Ui_TabularDisplay
from .tabular_filter import TabularFilter
from ...blocks.utils import csv_bytearray2hex, csv_int2hex, pandas_query_compatible


logger = logging.getLogger("asammdf.gui")


class TreeItem(QtWidgets.QTreeWidgetItem):

    def __lt__(self, otherItem):
        column = self.treeWidget().sortColumn()

        val1 = self.text(column)
        try:
            val1 = float(val1)
        except:
            pass

        val2 = otherItem.text(column)
        try:
            val2 = float(val2)
        except:
            pass

        try:
            return val1 < val2
        except:
            if isinstance(val1, float):
                return True
            else:
                return False


class Tabular(Ui_TabularDisplay, QtWidgets.QWidget):
    add_channels_request = QtCore.pyqtSignal(list)

    def __init__(self, signals=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        if signals is None:
            self.signals = pd.DataFrame()
        else:
            dropped = {}

            for name_ in signals.columns:
                col = signals[name_]
                if col.dtype.kind == 'O':
                    dropped[name_] = pd.Series(csv_bytearray2hex(col), index=signals.index)

            signals = signals.drop(columns=list(dropped))
            for name, s in dropped.items():
                signals[name] = s

            self.signals = signals

        self.build(self.signals)

        self.add_filter_btn.clicked.connect(self.add_filter)
        self.apply_filters_btn.clicked.connect(self.apply_filters)
        self.sort.stateChanged.connect(self.sorting_changed)

    def add_filter(self, event):
        filter_widget = TabularFilter(
            [(self.signals.index.name, self.signals.index.values.dtype.kind)] +
            [
                (name, self.signals[name].values.dtype.kind)
                for name in self.signals.columns
            ]
        )

        item = QtWidgets.QListWidgetItem(self.filters)
        item.setSizeHint(filter_widget.sizeHint())
        self.filters.addItem(item)
        self.filters.setItemWidget(item, filter_widget)

    def apply_filters(self, event):
        df = self.signals

        friendly_names = {
            name: pandas_query_compatible(name)
            for name in df.columns
        }

        original_names = {
            val: key
            for key, val in friendly_names.items()
        }

        df.rename(columns=friendly_names, inplace=True)

        filters = []
        count = self.filters.count()

        for i in range(count):
            filter = self.filters.itemWidget(self.filters.item(i))
            if filter.enabled.checkState() == QtCore.Qt.Unchecked:
                continue

            target = filter._target
            if not target:
                continue

            if filters:
                filters.append(filter.relation.currentText().lower())
            filters.append(pandas_query_compatible(filter.column.currentText()))
            filters.append(filter.op.currentText())
            filters.append(str(target))

        if filters:
            try:
                new_df = df.query(' '.join(filters))
            except:
                logger.exception(f'Failed to apply filter for tabular window: {" ".join(filters)}')
                self.query.setText(format_exc())
            else:
                self.query.setText(' '.join(filters))
                new_df.rename(columns=original_names, inplace=True)
                self.build(new_df)
        else:
            self.query.setText('')
            df.rename(columns=original_names, inplace=True)
            self.build(df)

        self.signals.rename(columns=original_names, inplace=True)

    def items_deleted(self, names):
        for name in names:
            self.signals.pop(name)
        self.build()

    def build(self, df):
        self.tree.setSortingEnabled(False)
        self.tree.clear()

        dropped = {}

        for name_ in df.columns:
            if name_.endswith('CAN_DataFrame.ID'):
                dropped[name_] = pd.Series(csv_int2hex(df[name_].astype('<u4')), index=df.index)

        df = df.drop(columns=list(dropped))
        for name, s in dropped.items():
            df[name] = s

        names = [
            df.index.name,
            *df.columns
        ]

        self.tree.setColumnCount(len(names))
        self.tree.setHeaderLabels(names)

        items = [df.index.astype(str), *(df[name].astype(str) for name in df)]

        items = [
            TreeItem(row)
            for row in zip(*items)
        ]

        self.tree.addTopLevelItems(items)

    def add_new_channels(self, channels):
        for sig in channels:
            if sig:
                self.signals[sig.name] = sig
        self.build()

    def to_config(self):

        count = self.filters.count()

        config = {
            'sorted': self.sort.checkState() == QtCore.Qt.Checked,
            'channels': list(self.signals.columns),
            'filtered': bool(self.query.toPlainText()),
            'filters': [
                self.filters.itemWidget(self.filters.item(i)).to_config()
                for i in range(count)
            ]
        }

        return config

    def sorting_changed(self, state):
        if state == QtCore.Qt.Checked:
            self.tree.setSortingEnabled(True)
        else:
            self.tree.header().setSortIndicator(0, QtCore.Qt.AscendingOrder)
            self.tree.setSortingEnabled(False)
