# -*- coding: utf-8 -*-
from collections import namedtuple
from copy import deepcopy
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import sys
from time import perf_counter

from natsort import natsorted
import numpy as np
from numpy import searchsorted
from PyQt5 import QtCore, QtGui, QtWidgets, uic

from asammdf.gui import utils
from asammdf.gui.dialogs.range_editor import RangeEditor
from asammdf.gui.utils import copy_ranges, extract_mime_names, get_colors_using_ranges
from asammdf.gui.widgets.plot import PlotSignal
from asammdf.gui.widgets.tree_item import TreeItem

from ..ui import resource_rc

HERE = Path(__file__).resolve().parent


OPS = {
    "!=": "__ne__",
    "==": "__eq__",
    ">": "__gt__",
    ">=": "__ge__",
    "<": "__lt__",
    "<=": "__le__",
}


class SignalOnline:
    def __init__(
        self,
        name="",
        raw=None,
        scaled=None,
        unit="",
        entry=(),
        conversion=None,
        exists=True,
    ):
        self.name = name
        self.raw = raw
        self.scaled = scaled
        self.unit = unit
        self.entry = entry
        self.conversion = conversion
        self.exists = exists
        self.configured_from_device = True

    @property
    def mdf_uuid(self):
        return self.entry[0]

    @mdf_uuid.setter
    def mdf_uuid(self, value):
        self.entry = (value, self.name)

    def reset(self):
        self.raw = None
        self.scaled = None
        self.exists = True

    def update_values(self, values):
        self.raw = values[-1]
        if self.conversion:
            self.scaled = self.conversion.convert(values[-1:])[0]
        else:
            self.scaled = self.raw

    def __lt__(self, other):
        return self.name < other.name

    def get_value(self, index):
        if index == 0:
            return self.name
        elif index == 1:
            return self.raw
        elif index == 2:
            return self.scaled
        elif index == 3:
            return self.unit


class SignalOffline:
    def __init__(
        self,
        signal=None,
        exists=True,
    ):
        self.signal = signal
        self.exists = exists
        self.raw = None
        self.scaled = None
        self.last_timestamp = None
        self.entry = signal.entry
        self.name = signal.name
        self.unit = signal.unit

    def reset(self):
        self.signal = None
        self.exists = True
        self.raw = None
        self.scaled = None
        self.last_timestamp = None

    def __lt__(self, other):
        return self.name < other.name

    def set_timestamp(self, timestamp):
        if timestamp is not None and (
            self.last_timestamp is None or self.last_timestamp != timestamp
        ):
            self.last_timestamp = timestamp

            sig = self.signal
            if sig.size:
                idx = searchsorted(sig.timestamps, timestamp, side="right")
                idx -= 1
                if idx < 0:
                    idx = 0

                self.raw = sig.raw_samples[idx]
                self.scaled = sig.phys_samples[idx]

    def get_value(self, index, timestamp=None):
        self.set_timestamp(timestamp)
        if self.signal is not None:
            if index == 0:
                return self.signal.name
            elif index == 1:
                return self.raw
            elif index == 2:
                return self.scaled
            elif index == 3:
                return self.unit


class OnlineBackEnd:
    def __init__(self, signals, numeric):
        super().__init__()

        self.signals = signals or []
        self.map = None
        self.numeric = numeric

        self.sorted_column_index = 0
        self.sort_reversed = False
        self.numeric_viewer = None

        self.update()

    def update_signal_mdf_uuid(self, signal, mdf_uuid):
        old_entry = signal.entry
        signal.mdf_uuid = mdf_uuid
        self.map[signal.entry] = signal
        del self.map[old_entry]

        self.numeric_viewer.dataView.ranges[
            signal.entry
        ] = self.numeric_viewer.dataView.ranges[old_entry]
        del self.numeric_viewer.dataView.ranges[old_entry]

    def update(self, others=()):
        self.map = {signal.entry: signal for signal in self.signals}
        for signal in others:
            if signal.entry not in self.map:
                self.map[signal.entry] = signal
                self.signals.append(signal)

        self.sort()

    def sort_column(self, ix):

        if ix != self.sorted_column_index:
            self.sorted_column_index = ix
            self.sort_reversed = False
        else:
            self.sort_reversed = not self.sort_reversed

        self.sort()

    def data_changed(self):
        self.refresh_ui()

    def refresh_ui(self):

        if self.numeric is not None and self.numeric.mode == "offline":
            numeric = self.numeric
            numeric._min = float("inf")
            numeric._max = -float("inf")

            for sig in self.signals:
                if sig.size:
                    numeric._min = min(self._min, sig.timestamps[0])
                    numeric._max = max(self._max, sig.timestamps[-1])

            if numeric._min == float("inf"):
                numeric._min = numeric._max = 0

            numeric._timestamp = numeric._min

            numeric.timestamp.setRange(numeric._min, numeric._max)
            numeric.min_t.setText(f"{numeric._min:.9f}s")
            numeric.max_t.setText(f"{numeric._max:.9f}s")
            numeric.set_timestamp(numeric._min)

        if self.numeric_viewer is not None:
            self.numeric_viewer.refresh_ui()

    def sort(self):
        sorted_column_index = self.sorted_column_index

        if sorted_column_index == 0:
            self.signals = natsorted(
                self.signals, key=lambda x: x.name, reverse=self.sort_reversed
            )

        elif sorted_column_index in (1, 2):

            numeric = []
            string = []
            nones = []

            for signal in self.signals:
                value = signal.item(sorted_column_index)
                if value is None:
                    nones.append(signal)
                elif isinstance(value, (np.flexible, bytes)):
                    string.append(signal)
                else:
                    numeric.append(signal)

            self.signals = [
                *sorted(
                    numeric,
                    key=lambda x: x.item(sorted_column_index),
                    reverse=self.sort_reversed,
                ),
                *sorted(
                    string,
                    key=lambda x: x.item(sorted_column_index),
                    reverse=self.sort_reversed,
                ),
                *natsorted(nones, key=lambda x: x.name, reverse=self.sort_reversed),
            ]

        elif sorted_column_index == 3:
            self.signals = natsorted(
                self.signals, key=lambda x: x.unit, reverse=self.sort_reversed
            )

        self.data_changed()

    def set_values(self, values=None):
        map_ = self.map
        if values:
            for entry, vals in values.items():
                sig = map_[entry]
                sig.update_values(vals)

            if self.sorted_column_index in (1, 2):
                self.sort()
            else:
                self.data_changed()

    def reset(self):
        for sig in self.signals:
            sig.reset()
        self.data_changed()

    def __len__(self):
        return len(self.signals)

    def does_not_exist(self, entry, exists):
        self.map[entry].exists = exists

    def get_signal_value(self, signal, column):
        return signal.get_value(column)


class OfflineBackEnd:
    def __init__(self, signals, numeric):
        super().__init__()

        self.timestamp = None

        self.signals = signals or []
        self.map = None
        self.numeric = numeric

        self.sorted_column_index = 0
        self.sort_reversed = False
        self.numeric_viewer = None

    def update(self, others=()):
        self.map = {signal.entry: signal for signal in self.signals}
        for signal in others:
            if signal.entry not in self.map:
                self.map[signal.entry] = signal
                self.signals.append(signal)

        self.sort()

    def sort_column(self, ix):

        if ix != self.sorted_column_index:
            self.sorted_column_index = ix
            self.sort_reversed = False
        else:
            self.sort_reversed = not self.sort_reversed

        self.sort()

    def data_changed(self):
        self.refresh_ui()

    def refresh_ui(self):

        if self.numeric_viewer is not None:
            self.numeric_viewer.refresh_ui()

    def sort(self):
        sorted_column_index = self.sorted_column_index

        if sorted_column_index == 0:
            self.signals = natsorted(
                self.signals, key=lambda x: x.name, reverse=self.sort_reversed
            )

        elif sorted_column_index in (1, 2):

            numeric = []
            string = []
            nones = []

            for signal in self.signals:
                value = signal.get_value(sorted_column_index, self.timestamp)
                if value is None:
                    nones.append(signal)
                elif isinstance(value, (np.flexible, bytes)):
                    string.append(signal)
                else:
                    numeric.append(signal)

            self.signals = [
                *sorted(
                    numeric,
                    key=lambda x: x.get_value(sorted_column_index),
                    reverse=self.sort_reversed,
                ),
                *sorted(
                    string,
                    key=lambda x: x.get_value(sorted_column_index),
                    reverse=self.sort_reversed,
                ),
                *natsorted(nones, key=lambda x: x.name, reverse=self.sort_reversed),
            ]

        elif sorted_column_index == 3:
            self.signals = natsorted(
                self.signals, key=lambda x: x.unit, reverse=self.sort_reversed
            )

        self.data_changed()

    def set_timestamp(self, stamp):
        self.timestamp = stamp
        if self.sorted_column_index in (1, 2):
            self.sort()
        else:
            self.data_changed()

    def reset(self):
        for sig in self.signals:
            sig.reset()
        self.data_changed()

    def __len__(self):
        return len(self.signals)

    def does_not_exist(self, entry, exists):
        self.map[entry].exists = exists

    def get_signal_value(self, signal, column):
        return signal.get_value(column, self.timestamp)


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent, background_color, font_color):
        super().__init__(parent)
        self.numeric_viewer = parent
        self.backend = parent.backend
        self.view = None
        self.format = "Physical"
        self.float_precision = -1
        self.background_color = background_color
        self.font_color = font_color

    def headerData(self, section, orientation, role=None):
        pass

    def columnCount(self, parent=None):
        return 4

    def rowCount(self, parent=None):
        return len(self.backend)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        row = index.row()
        col = index.column()

        signal = self.backend.signals[row]
        cell = self.backend.get_signal_value(signal, col)

        if role == QtCore.Qt.DisplayRole:

            if cell is None:
                return "●"

            if isinstance(cell, (float, np.floating)):
                if self.float_precision != -1:
                    template = f"{{:.{self.float_precision}f}}"
                    return template.format(cell)
                else:
                    return str(cell)

            elif isinstance(cell, (int, np.integer)):
                if self.format == "Hex":
                    return f"{cell:X}"
                elif self.format == "Bin":
                    return f"{cell:b}"
                else:
                    return str(cell)

            elif isinstance(cell, (bytes, np.bytes_)):
                return cell.decode("utf-8", "replace")

            return str(cell)

        elif role == QtCore.Qt.BackgroundRole:

            channel_ranges = self.view.ranges[signal.entry]

            try:
                value = float(cell)
            except:
                value = str(cell)

            new_background_color, new_font_color = get_colors_using_ranges(
                value,
                ranges=channel_ranges,
                default_background_color=self.background_color,
                default_font_color=self.font_color,
            )

            return (
                new_background_color
                if new_background_color != self.background_color
                else None
            )

        elif role == QtCore.Qt.ForegroundRole:
            channel_ranges = self.view.ranges[signal.entry]

            try:
                value = float(cell)
            except:
                value = str(cell)

            new_background_color, new_font_color = get_colors_using_ranges(
                value,
                ranges=channel_ranges,
                default_background_color=self.background_color,
                default_font_color=self.font_color,
            )

            return new_font_color if new_font_color != self.font_color else None

        elif role == QtCore.Qt.TextAlignmentRole:
            if col:
                return QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            else:
                return QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter

        elif role == QtCore.Qt.DecorationRole and col == 0:
            if not signal.exists:
                icon = utils.ERROR_ICON
                if icon is None:
                    utils.ERROR_ICON = QtGui.QIcon()
                    utils.ERROR_ICON.addPixmap(
                        QtGui.QPixmap(":/error.png"),
                        QtGui.QIcon.Normal,
                        QtGui.QIcon.Off,
                    )

                    utils.NO_ERROR_ICON = QtGui.QIcon()

                    icon = utils.ERROR_ICON
            else:
                icon = utils.NO_ERROR_ICON
                if icon is None:
                    utils.ERROR_ICON = QtGui.QIcon()
                    utils.ERROR_ICON.addPixmap(
                        QtGui.QPixmap(":/error.png"),
                        QtGui.QIcon.Normal,
                        QtGui.QIcon.Off,
                    )

                    utils.NO_ERROR_ICON = QtGui.QIcon()

                    icon = utils.NO_ERROR_ICON

            return icon

    def flags(self, index):
        return (
            QtCore.Qt.ItemIsEnabled
            | QtCore.Qt.ItemIsSelectable
            | QtCore.Qt.ItemIsDragEnabled
        )

    def setData(self, index, value, role=None):
        pass

    def supportedDropActions(self) -> bool:
        return QtCore.Qt.MoveAction | QtCore.Qt.CopyAction


class TableView(QtWidgets.QTableView):
    add_channels_request = QtCore.pyqtSignal(list)

    def __init__(self, parent):
        super().__init__(parent)
        self.numeric_viewer = parent
        self.backend = parent.backend

        self.ranges = {}

        self._backgrund_color = self.palette().color(QtGui.QPalette.Background)
        self._font_color = self.palette().color(QtGui.QPalette.WindowText)

        model = TableModel(parent, self._backgrund_color, self._font_color)
        self.setModel(model)
        model.view = self

        self.horizontalHeader().hide()
        self.verticalHeader().hide()

        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)

        self.doubleClicked.connect(self.edit_ranges)

        self.setDragDropMode(self.InternalMove)

        self.double_clicked_enabled = True

    def sizeHint(self):
        width = 2 * self.frameWidth()
        for i in range(self.model().columnCount()):
            width += self.columnWidth(i)

        height = 2 * self.frameWidth()
        height += 24 * self.model().rowCount()

        return QtCore.QSize(width, height)

    def resizeEvent(self, e: QtGui.QResizeEvent):
        super().resizeEvent(e)
        if e.oldSize().width() != e.size().width():
            self.numeric_viewer.auto_size_header()

    def keyPressEvent(self, event):

        if (
            event.key() == QtCore.Qt.Key_Delete
            and event.modifiers() == QtCore.Qt.NoModifier
        ):
            selected_items = set(
                index.row() for index in self.selectedIndexes() if index.isValid()
            )

            for row in reversed(list(selected_items)):
                signal = self.backend.signals.pop(row)
                del self.backend.map[signal.entry]

            self.backend.data_changed()

        else:
            super().keyPressEvent(event)

    def startDrag(self, supportedActions):
        selected_items = [
            index.row() for index in self.selectedIndexes() if index.isValid()
        ]

        mimeData = QtCore.QMimeData()

        data = []
        numeric_mode = self.backend.numeric.mode

        for row in sorted(set(selected_items)):

            signal = self.backend.signals[row]

            entry = signal.entry if numeric_mode == "online" else signal.signal.entry

            if entry == (-1, -1):
                info = {
                    "name": signal.name,
                    "computation": {},
                }
            else:
                info = signal.name

            ranges = copy_ranges(self.ranges[signal.entry])

            for range_info in ranges:
                range_info["font_color"] = range_info["font_color"].color().name()
                range_info["background_color"] = (
                    range_info["background_color"].color().name()
                )

            data.append(
                (
                    info,
                    *entry,
                    str(entry[0])
                    if numeric_mode == "online"
                    else signal.signal.mdf_uuid,
                    "channel",
                    ranges,
                )
            )

        data = json.dumps(data).encode("utf-8")

        mimeData.setData("application/octet-stream-asammdf", QtCore.QByteArray(data))

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.exec(QtCore.Qt.CopyAction)

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):

        if e.source() is self:
            return
        else:
            data = e.mimeData()
            if data.hasFormat("application/octet-stream-asammdf"):
                names = extract_mime_names(data)
                print(names)
                self.add_channels_request.emit(names)
            else:
                return

    def edit_ranges(self, index):
        if not self.double_clicked_enabled or not index.isValid():
            return

        row = index.row()
        signal = self.backend.signals[row]

        dlg = RangeEditor(
            signal.name, "", self.ranges[signal.entry], parent=self, brush=True
        )
        dlg.exec_()
        if dlg.pressed_button == "apply":
            ranges = dlg.result
            self.ranges[signal.entry] = ranges


class HeaderModel(QtCore.QAbstractTableModel):
    def __init__(self, parent):
        super().__init__(parent)
        self.backend = parent.backend

    def columnCount(self, parent=None):
        return 4

    def rowCount(self, parent=None):
        return 1  # 1?

    def data(self, index, role=QtCore.Qt.DisplayRole):
        col = index.column()

        names = ["Name", "Raw", "Scaled", "Unit"]

        if role == QtCore.Qt.DisplayRole:

            return names[col]

        elif role == QtCore.Qt.DecorationRole:

            if col != self.backend.sorted_column_index:
                return
            else:

                if self.backend.sort_reversed:
                    icon = QtGui.QIcon(":/sort-descending.png")
                else:
                    icon = QtGui.QIcon(":/sort-ascending.png")

                return icon

        elif role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter

    def headerData(self, section, orientation, role=None):
        pass


class HeaderView(QtWidgets.QTableView):
    def __init__(self, parent):
        super().__init__(parent)
        self.numeric_viewer = parent
        self.backend = parent.backend

        self.table = parent.dataView
        self.setModel(HeaderModel(parent))
        self.padding = 10

        self.header_cell_being_resized = None
        self.header_being_resized = False

        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.viewport().installEventFilter(self)

        self.setIconSize(QtCore.QSize(16, 16))
        self.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum
            )
        )
        self.setWordWrap(False)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        font = QtGui.QFont()
        font.setBold(True)
        self.setFont(font)

        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.resize(self.sizeHint())

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        super(HeaderView, self).showEvent(a0)
        self.initial_size = self.size()

    def mouseDoubleClickEvent(self, event):
        point = event.pos()
        ix = self.indexAt(point)
        col = ix.column()
        if event.button() == QtCore.Qt.LeftButton:
            self.backend.sort_column(col)
        else:
            super().mouseDoubleClickEvent(event)

    def eventFilter(self, object: QtCore.QObject, event: QtCore.QEvent):
        if event.type() in [
            QtCore.QEvent.MouseButtonPress,
            QtCore.QEvent.MouseButtonRelease,
            QtCore.QEvent.MouseButtonDblClick,
            QtCore.QEvent.MouseMove,
        ]:
            return self.manage_resizing(object, event)

        return False

    def manage_resizing(self, object: QtCore.QObject, event: QtCore.QEvent):
        def over_header_cell_edge(mouse_position, margin=3):
            x = mouse_position
            if self.columnAt(x - margin) != self.columnAt(x + margin):
                if self.columnAt(x + margin) == 0:
                    return None
                else:
                    return self.columnAt(x - margin)
            else:
                return None

        mouse_position = event.pos().x()
        orthogonal_mouse_position = event.pos().y()

        if over_header_cell_edge(mouse_position) is not None:
            self.viewport().setCursor(QtGui.QCursor(QtCore.Qt.SplitHCursor))

        else:
            self.viewport().setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

        if event.type() == QtCore.QEvent.MouseButtonPress:
            if over_header_cell_edge(mouse_position) is not None:
                self.header_cell_being_resized = over_header_cell_edge(mouse_position)
                return True
            else:
                self.header_cell_being_resized = None

        if event.type() == QtCore.QEvent.MouseButtonRelease:
            self.header_cell_being_resized = None
            self.header_being_resized = False

        if event.type() == QtCore.QEvent.MouseButtonDblClick:
            if over_header_cell_edge(mouse_position) is not None:
                header_index = over_header_cell_edge(mouse_position)
                self.numeric_viewer.auto_size_column(header_index)
                return True

        if event.type() == QtCore.QEvent.MouseMove:
            if self.header_cell_being_resized is not None:
                size = mouse_position - self.columnViewportPosition(
                    self.header_cell_being_resized
                )
                if size > 10:
                    self.setColumnWidth(self.header_cell_being_resized, size)
                    self.numeric_viewer.dataView.setColumnWidth(
                        self.header_cell_being_resized, size
                    )

                    self.updateGeometry()
                    self.numeric_viewer.dataView.updateGeometry()
                return True

            elif self.header_being_resized:

                size = orthogonal_mouse_position - self.geometry().top()
                self.setFixedHeight(max(size, self.initial_size.height()))

                self.updateGeometry()
                self.numeric_viewer.dataView.updateGeometry()
                return True

        return False

    def sizeHint(self):

        width = self.table.sizeHint().width() + self.verticalHeader().width()
        height = 24

        return QtCore.QSize(width, height)

    def minimumSizeHint(self):
        return QtCore.QSize(50, self.sizeHint().height())


class NumericViewer(QtWidgets.QWidget):
    def __init__(self, backend):
        super().__init__()

        backend.numeric_viewer = self
        self.backend = backend

        self.dataView = TableView(parent=self)

        self.columnHeader = HeaderView(parent=self)

        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.setLayout(self.gridLayout)

        self.dataView.horizontalScrollBar().valueChanged.connect(
            self.columnHeader.horizontalScrollBar().setValue
        )

        self.columnHeader.horizontalScrollBar().valueChanged.connect(
            self.dataView.horizontalScrollBar().setValue
        )

        self.dataView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.dataView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.gridLayout.addWidget(self.columnHeader, 0, 0)
        self.gridLayout.addWidget(self.dataView, 1, 0)
        self.gridLayout.addWidget(self.dataView.horizontalScrollBar(), 2, 0, 1, 1)
        self.gridLayout.addWidget(self.dataView.verticalScrollBar(), 1, 1, 1, 1)

        self.dataView.verticalScrollBar().setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Ignored
            )
        )
        self.dataView.horizontalScrollBar().setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed
            )
        )

        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setRowStretch(1, 1)

        self.set_styles()

        self.columnHeader.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.MinimumExpanding
        )

        default_row_height = 24
        self.dataView.verticalHeader().setDefaultSectionSize(default_row_height)
        self.dataView.verticalHeader().setMinimumSectionSize(default_row_height)
        self.dataView.verticalHeader().setMaximumSectionSize(default_row_height)
        self.dataView.verticalHeader().sectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.columnHeader.verticalHeader().setDefaultSectionSize(default_row_height)
        self.columnHeader.verticalHeader().setMinimumSectionSize(default_row_height)
        self.columnHeader.verticalHeader().setMaximumSectionSize(default_row_height)
        self.columnHeader.verticalHeader().sectionResizeMode(
            QtWidgets.QHeaderView.Fixed
        )

        for column_index in range(self.columnHeader.model().columnCount()):
            self.auto_size_column(column_index)

        self.columnHeader.horizontalHeader().setStretchLastSection(True)

        self.columnHeader.horizontalHeader().sectionResized.connect(
            self.update_horizontal_scroll
        )

        self.columnHeader.horizontalHeader().setMinimumSectionSize(1)
        self.dataView.horizontalHeader().setMinimumSectionSize(1)

        self.show()

    def set_styles(self):
        return
        for item in [
            self.dataView,
            self.columnHeader,
        ]:
            item.setContentsMargins(0, 0, 0, 0)

    def auto_size_header(self):
        s = 0
        for i in range(self.columnHeader.model().columnCount()):
            s += self.auto_size_column(i)

        delta = int((self.dataView.viewport().size().width() - s) // 4)

        if delta > 0:
            for i in range(self.columnHeader.model().columnCount()):
                self.auto_size_column(i, extra_padding=delta)
            self.dataView.horizontalScrollBar().hide()
        else:
            self.dataView.horizontalScrollBar().show()

    def update_horizontal_scroll(self, *args):
        s = 0
        for i in range(self.columnHeader.model().columnCount()):
            s += self.dataView.columnWidth(i) + self.dataView.frameWidth()

        if self.dataView.viewport().size().width() < s:
            self.dataView.horizontalScrollBar().show()
        else:
            self.dataView.horizontalScrollBar().hide()

    def auto_size_column(self, column_index, extra_padding=0):
        width = 0

        N = 100
        for i in range(self.dataView.model().rowCount())[:N]:
            mi = self.dataView.model().index(i, column_index)
            text = self.dataView.model().data(mi)
            w = self.dataView.fontMetrics().boundingRect(text).width()
            width = max(width, w)

        for i in range(self.columnHeader.model().rowCount()):
            mi = self.columnHeader.model().index(i, column_index)
            text = self.columnHeader.model().data(mi)
            w = self.columnHeader.fontMetrics().boundingRect(text).width()
            width = max(width, w)

        padding = 20
        width += padding + extra_padding

        self.columnHeader.setColumnWidth(column_index, width)
        self.dataView.setColumnWidth(
            column_index, self.columnHeader.columnWidth(column_index)
        )

        self.dataView.updateGeometry()
        self.columnHeader.updateGeometry()

        return width

    def auto_size_row(self, row_index):
        height = 24

        self.indexHeader.setRowHeight(row_index, height)
        self.dataView.setRowHeight(row_index, height)

        self.dataView.updateGeometry()
        self.indexHeader.updateGeometry()

    def scroll_to_column(self, column=0):
        index = self.dataView.model().index(0, column)
        self.dataView.scrollTo(index)
        self.columnHeader.selectColumn(column)
        self.columnHeader.on_selectionChanged(force=True)

    def refresh_ui(self):
        self.models = []
        self.models += [
            self.dataView.model(),
            self.columnHeader.model(),
        ]

        for model in self.models:
            model.beginResetModel()
            model.endResetModel()

        for view in [self.columnHeader, self.dataView]:
            view.updateGeometry()


class Numeric(QtWidgets.QWidget):
    add_channels_request = QtCore.pyqtSignal(list)
    timestamp_changed_signal = QtCore.pyqtSignal(object, float)

    def __init__(
        self,
        channels=None,
        format=None,
        mode="offline",
        float_precision=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if mode == "offline":
            uic.loadUi(HERE.joinpath("..", "ui", "numeric_offline.ui"), self)
        else:
            uic.loadUi(HERE.joinpath("..", "ui", "numeric_online.ui"), self)

        self.mode = mode

        self._settings = QtCore.QSettings()

        if mode == "offline":
            backend = OfflineBackEnd(None, self)
        else:
            backend = OnlineBackEnd(None, self)
        self.channels = NumericViewer(backend)

        self.channels.dataView.ranges = {}

        self.verticalLayout.insertWidget(1, self.channels)
        self.verticalLayout.setStretch(1, 1)

        self.float_precision.addItems(
            ["Full float precision"] + [f"{i} float decimals" for i in range(16)]
        )
        self.float_precision.setCurrentIndex(-1)
        self.format_selection.setCurrentIndex(-1)

        self.format_selection.currentTextChanged.connect(self.set_format)
        self.float_precision.currentIndexChanged.connect(self.set_float_precision)

        format = format or self._settings.value("numeric_format", "Physical")
        if format not in ("Physical", "Hex", "Binary"):
            format = "Physical"
            self._settings.setValue("numeric_format", format)

        self.format_selection.setCurrentText(format)

        if float_precision is None:
            float_precision = self._settings.value("numeric_float_precision", -1)
        self.float_precision.setCurrentIndex(float_precision + 1)

        if channels:
            self.add_new_channels(channels)

        self.channels.dataView.add_channels_request.connect(self.add_channels_request)

        self.channels.auto_size_header()
        self.double_clicked_enabled = True

        if self.mode == "offline":
            self.pattern = {}

            self.timestamp.valueChanged.connect(self._timestamp_changed)
            self.timestamp_slider.valueChanged.connect(self._timestamp_slider_changed)

            self._inhibit = False

            self.forward.clicked.connect(self.search_forward)
            self.backward.clicked.connect(self.search_backward)
            self.op.addItems([">", ">=", "<", "<=", "==", "!="])

    def add_new_channels(self, channels, mime_data=None):

        if self.mode == "online":
            others = []
            for sig in channels:
                if sig is not None:
                    entry = (sig.mdf_uuid, sig.name)

                    others.append(
                        SignalOnline(
                            name=sig.name,
                            conversion=sig.conversion,
                            entry=entry,
                            unit=sig.unit,
                        )
                    )

                    self.channels.dataView.ranges[entry] = []

        else:
            others = []
            for sig in channels:
                if sig is not None:
                    sig.computed = False
                    sig.computation = None
                    sig = PlotSignal(sig)
                    sig.entry = sig.group_index, sig.channel_index

                    others.append(
                        SignalOffline(
                            signal=sig,
                        )
                    )

                    self.channels.dataView.ranges[sig.entry] = []

        self.channels.backend.update(others)

        if self.mode == "offline":

            numeric = self
            numeric._min = float("inf")
            numeric._max = -float("inf")

            for sig in self.channels.backend.signals:
                timestamps = sig.signal.timestamps
                if timestamps.size:
                    numeric._min = min(numeric._min, timestamps[0])
                    numeric._max = max(numeric._max, timestamps[-1])

            if numeric._min == float("inf"):
                numeric._min = numeric._max = 0

            numeric._timestamp = numeric._min

            numeric.timestamp.setRange(numeric._min, numeric._max)
            numeric.min_t.setText(f"{numeric._min:.9f}s")
            numeric.max_t.setText(f"{numeric._max:.9f}s")
            numeric.set_timestamp(numeric._min)

    def reset(self):
        self.channels.backend.reset()
        self.channels.dataView.double_clicked_enabled = True

    def set_values(self, values=None):
        self.channels.backend.set_values(values)

    def to_config(self):

        if self.mode == "online":

            channels = []
            for signal in self.channels.backend.signals:
                ranges = self.channels.dataView.ranges[signal.entry]
                ranges = copy_ranges(ranges)

                for range_info in ranges:
                    range_info["font_color"] = range_info["font_color"].color().name()
                    range_info["background_color"] = (
                        range_info["background_color"].color().name()
                    )

                channels.append(
                    {
                        "mdf_uuid": str(signal.entry[0]),
                        "name": signal.name,
                        "ranges": ranges,
                    }
                )

            config = {
                "format": self.format_selection.currentText(),
                "mode": "",
                "channels": channels,
                "float_precision": self.float_precision.currentIndex() - 1,
                "header_sections_width": [
                    self.channels.columnHeader.horizontalHeader().sectionSize(i)
                    for i in range(
                        self.channels.columnHeader.horizontalHeader().count()
                    )
                ],
            }

        else:
            channels = {}
            for signal in self.channels.backend.signals:
                ranges = self.channels.dataView.ranges[signal.entry]
                ranges = copy_ranges(ranges)

                for range_info in ranges:
                    range_info["font_color"] = range_info["font_color"].color().name()
                    range_info["background_color"] = (
                        range_info["background_color"].color().name()
                    )

                channels[signal.name] = ranges

            pattern = self.pattern
            if pattern:
                ranges = copy_ranges(pattern["ranges"])

                for range_info in ranges:
                    range_info["font_color"] = range_info["font_color"].color().name()
                    range_info["background_color"] = (
                        range_info["background_color"].color().name()
                    )

                pattern["ranges"] = ranges

            config = {
                "format": self.format_selection.currentText(),
                "mode": self.mode,
                "channels": list(channels) if not self.pattern else [],
                "ranges": list(channels.values()) if not self.pattern else [],
                "pattern": pattern,
                "float_precision": self.float_precision.currentIndex() - 1,
                "header_sections_width": [
                    self.channels.columnHeader.horizontalHeader().sectionSize(i)
                    for i in range(
                        self.channels.columnHeader.horizontalHeader().count()
                    )
                ],
            }

        return config

    def does_not_exist(self, entry, exists=False):
        self.channels.backend.does_not_exist(entry, exists)

    def set_format(self, fmt):
        if fmt not in ("Physical", "Hex", "Bin"):
            fmt = "Physical"

        self.channels.dataView.model().format = fmt
        self._settings.setValue("numeric_format", fmt)
        self.channels.backend.data_changed()

    def set_float_precision(self, index):
        self._settings.setValue("numeric_float_precision", index - 1)
        self.channels.dataView.model().float_precision = index - 1
        self.channels.backend.data_changed()

    def visible_entries(self):
        visible = set()

        if self.channels.backend.sorted_column_index in (1, 2):
            visible = set(self.channels.backend.map)

        else:
            rect = self.channels.dataView.viewport().rect()

            top = self.channels.dataView.indexAt(rect.topLeft()).row()
            bottom = self.channels.dataView.indexAt(rect.bottomLeft()).row()
            if top == -1:
                pass
            elif bottom == -1:
                visible = set(self.channels.backend.map)
            else:
                for row in range(top, bottom + 1):
                    visible.add(self.channels.backend.signals[row].entry)

        return visible

    def _timestamp_changed(self, stamp):
        if not self._inhibit:
            self.set_timestamp(stamp)

    def _timestamp_slider_changed(self, stamp):
        if not self._inhibit:
            factor = stamp / 99999
            stamp = (self._max - self._min) * factor + self._min
            self.set_timestamp(stamp)

    def set_timestamp(self, stamp=None):
        if stamp is None:
            stamp = self._timestamp

        if not (self._min <= stamp <= self._max):
            return

        self.channels.backend.set_timestamp(stamp)

        self._inhibit = True
        if self._min != self._max:
            val = int((stamp - self._min) / (self._max - self._min) * 99999)
            self.timestamp_slider.setValue(val)
        self.timestamp.setValue(stamp)
        self._inhibit = False
        self.timestamp_changed_signal.emit(self, stamp)

    def search_forward(self):
        if (
            self.op.currentIndex() < 0
            or not self.target.text().strip()
            or not self.pattern_match.text().strip()
        ):
            self.match.setText("invalid input values")
            return

        operator = self.op.currentText()

        pattern = self.pattern_match.text().strip().replace("*", "_WILDCARD_")
        pattern = re.escape(pattern)
        pattern = pattern.replace("_WILDCARD_", ".*")

        pattern = re.compile(f"(?i){pattern}")
        matches = [
            sig for sig in self.channels.backend.signals if pattern.search(sig.name)
        ]

        mode = self.match_mode.currentText()

        if not matches:
            self.match.setText("the pattern does not match any channel name")
            return

        try:
            target = float(self.target.text().strip())
        except:
            self.match.setText("the target must a numeric value")
        else:

            if target.is_integer():
                target = int(target)

            start = self.timestamp.value()

            timestamp = None
            signal_name = ""
            for sig in matches:
                sig = sig.signal.cut(start=start)
                if mode == "Raw" or sig.comversion is None:
                    samples = sig.raw_samples
                else:
                    samples = sig.phys_samples

                op = getattr(samples, OPS[operator])
                try:
                    idx = np.argwhere(op(target)).flatten()
                    if len(idx):
                        if len(idx) == 1 or sig.timestamps[idx[0]] != start:
                            timestamp_ = sig.timestamps[idx[0]]
                        else:
                            timestamp_ = sig.timestamps[idx[1]]

                        if timestamp is None or timestamp_ < timestamp:
                            timestamp = timestamp_
                            signal_name = sig.name
                except:
                    continue

            if timestamp is not None:
                self.timestamp.setValue(timestamp)
                self.match.setText(f"condition found for {signal_name}")
            else:
                self.match.setText("condition not found")

    def search_backward(self):
        if (
            self.op.currentIndex() < 0
            or not self.target.text().strip()
            or not self.pattern_match.text().strip()
        ):
            self.match.setText("invalid input values")
            return

        operator = self.op.currentText()

        pattern = self.pattern_match.text().strip().replace("*", "_WILDCARD_")
        pattern = re.escape(pattern)
        pattern = pattern.replace("_WILDCARD_", ".*")

        pattern = re.compile(f"(?i){pattern}")
        matches = [
            sig for sig in self.channels.backend.signals if pattern.search(sig.name)
        ]

        mode = self.match_mode.currentText()

        if not matches:
            self.match.setText("the pattern does not match any channel name")
            return

        try:
            target = float(self.target.text().strip())
        except:
            self.match.setText(f"the target must a numeric value")
        else:

            if target.is_integer():
                target = int(target)

            stop = self.timestamp.value()

            timestamp = None
            signal_name = ""
            for sig in matches:
                sig = sig.signal.cut(stop=stop)
                if mode == "raw values" or sig.comversion is None:
                    samples = sig.raw_samples[:-1]
                else:
                    samples = sig.phys_samples[:-1]

                op = getattr(samples, OPS[operator])
                try:
                    idx = np.argwhere(op(target)).flatten()
                    if len(idx):

                        if len(idx) == 1 or sig.timestamps[idx[-1]] != stop:
                            timestamp_ = sig.timestamps[idx[-1]]
                        else:
                            timestamp_ = sig.timestamps[idx[-2]]

                        if timestamp is None or timestamp_ > timestamp:
                            timestamp = timestamp_
                            signal_name = sig.name
                except:
                    continue

            if timestamp is not None:
                self.timestamp.setValue(timestamp)
                self.match.setText(f"condition found for {signal_name}")
            else:
                self.match.setText(f"condition not found")

    def keyPressEvent(self, event):
        key = event.key()
        modifier = event.modifiers()

        if (
            key in (QtCore.Qt.Key_H, QtCore.Qt.Key_B, QtCore.Qt.Key_P)
            and modifier == QtCore.Qt.ControlModifier
        ):
            if key == QtCore.Qt.Key_H:
                self.format_selection.setCurrentText("Hex")
            elif key == QtCore.Qt.Key_B:
                self.format_selection.setCurrentText("Binary")
            else:
                self.format_selection.setCurrentText("Physical")
            event.accept()
        elif (
            key == QtCore.Qt.Key_Right
            and modifier == QtCore.Qt.NoModifier
            and self.mode == "offline"
        ):
            self.timestamp_slider.setValue(self.timestamp_slider.value() + 1)

        elif (
            key == QtCore.Qt.Key_Left
            and modifier == QtCore.Qt.NoModifier
            and self.mode == "offline"
        ):
            self.timestamp_slider.setValue(self.timestamp_slider.value() - 1)

        elif (
            key == QtCore.Qt.Key_S
            and modifier == QtCore.Qt.ControlModifier
            and self.mode == "offline"
        ):
            file_name, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Select output measurement file",
                "",
                "MDF version 4 files (*.mf4)",
            )

            if file_name:
                signals = [signal for signal in self.signals if signal.enable]
                if signals:
                    with MDF() as mdf:
                        groups = {}
                        for sig in signals:
                            id_ = id(sig.timestamps)
                            group_ = groups.setdefault(id_, [])
                            group_.append(sig)

                        for signals in groups.values():
                            sigs = []
                            for signal in signals:
                                if ":" in signal.name:
                                    sig = signal.copy()
                                    sig.name = sig.name.split(":")[-1].strip()
                                    sigs.append(sig)
                                else:
                                    sigs.append(signal)
                            mdf.append(sigs, common_timebase=True)
                        mdf.save(file_name, overwrite=True)
        else:
            self.channels.dataView.keyPressEvent(event)
