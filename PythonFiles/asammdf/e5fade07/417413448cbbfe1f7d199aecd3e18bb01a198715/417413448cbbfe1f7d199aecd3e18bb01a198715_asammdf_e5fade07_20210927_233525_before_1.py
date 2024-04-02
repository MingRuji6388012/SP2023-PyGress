# -*- coding: utf-8 -*-
import json

from PyQt5 import QtCore, QtGui, QtWidgets

from ..dialogs.range_editor import RangeEditor
from ..ui import resource_rc as resource_rc
from ..ui.channel_display_widget import Ui_ChannelDiplay


class ChannelDisplay(Ui_ChannelDiplay, QtWidgets.QWidget):

    color_changed = QtCore.pyqtSignal(object, str)
    enable_changed = QtCore.pyqtSignal(object, int)
    ylink_changed = QtCore.pyqtSignal(object, int)
    individual_axis_changed = QtCore.pyqtSignal(object, int)
    unit_changed = QtCore.pyqtSignal(object, str)
    name_changed = QtCore.pyqtSignal(object, str)

    def __init__(
        self,
        uuid,
        unit="",
        kind="f",
        precision=3,
        tooltip="",
        details="",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        self.color = "#ff0000"
        self._value_prefix = ""
        self._value = ""
        self._name = ""

        self.details.setText(details or "\tSource not available")

        self.details.setVisible(False)

        self.uuid = uuid
        self.ranges = []
        self._unit = unit.strip()
        self.kind = kind
        self.precision = precision

        self._transparent = True
        self._tooltip = tooltip

        self.color_btn.clicked.connect(self.select_color)
        # self.display.stateChanged.connect(self.display_changed)
        self.ylink.stateChanged.connect(self._ylink_changed)
        self.individual_axis.stateChanged.connect(self._individual_axis)

        self.fm = QtGui.QFontMetrics(self.name.font())

        self.setToolTip(self._tooltip or self._name)

        if kind in "SUVui":
            self.fmt = "{}"
        else:
            self.fmt = f"{{:.{self.precision}f}}"
            
        self.setAutoFillBackground(True)
        self._back_ground_color = self.palette().color(QtGui.QPalette.Base)
        self._selected_color = self.palette().color(QtGui.QPalette.Highlight)
        self._selected_font_color = self.palette().color(QtGui.QPalette.HighlightedText)
        self._font_color = QtGui.QColor(self.color)

        self._current_background_color = self._back_ground_color
        self._current_font_color = self._font_color = QtGui.QColor(self.color)

    def set_unit(self, unit):
        unit = str(unit)
        if unit != self._unit:
            self._unit = unit
            self.unit_changed.emit(self.uuid, unit)

    def copy(self):
        new = ChannelDisplay(
            self.uuid,
            self._unit,
            self.kind,
            self.precision,
            self._tooltip,
            self.details.text(),
        )

        new._value_prefix = self._value_prefix
        new.fmt = self.fmt
        new.set_name(self._name)
        new.individual_axis.setCheckState(self.individual_axis.checkState())
        new.ylink.setCheckState(self.ylink.checkState())
        new.set_color(self.color)
        new.set_value(self._value)

        return new

    def set_precision(self, precision):
        if self.kind == "f":
            self.precision = precision
            self.fmt = f"{{:.{self.precision}f}}"

    # def display_changed(self, state):
    #     state = self.display.checkState()
    #     self.enable_changed.emit(self.uuid, state)

    def _individual_axis(self, state):
        state = self.individual_axis.checkState()
        self.individual_axis_changed.emit(self.uuid, state)

    def _ylink_changed(self, state):
        state = self.ylink.checkState()
        self.ylink_changed.emit(self.uuid, state)

    def mouseDoubleClickEvent(self, event):
        dlg = RangeEditor(self._name, self._unit, self.ranges, parent=self)
        dlg.exec_()
        if dlg.pressed_button == "apply":
            self.ranges = dlg.result

    def select_color(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.color))
        if color.isValid():
            self.set_color(color.name())
            self.color_changed.emit(self.uuid, color.name())

    def set_fmt(self, fmt):
        if self.kind in "SUV":
            self.fmt = "{}"
        elif self.kind == "f":
            self.fmt = f"{{:.{self.precision}f}}"
        else:
            if fmt == "hex":
                self.fmt = "0x{:X}"
            elif fmt == "bin":
                self.fmt = "0b{:b}"
            elif fmt == "phys":
                self.fmt = "{}"

    def set_color(self, color):
        self.color = color
        self.set_name(self._name)
        self.set_value(self._value)
        self.color_btn.setStyleSheet(f"background-color: {color};")

        self._font_color = QtGui.QColor(self.color)

        palette = self.palette()
        palette.setColor(QtGui.QPalette.Text, self._font_color)

        self.setPalette(palette)

    def set_selected(self, on):
        if on:
            self._current_background_color = self._selected_color
            self._current_font_color = self._selected_font_color
            self.set_value(self._value, True)
        else:
            self._current_background_color = self._back_ground_color
            self._current_font_color = self._font_color
            self.set_value(self._value, True)

    def set_name(self, text=""):
        self.setToolTip(self._tooltip or text)
        self._name = text
        self.name_changed.emit(self.uuid, text)

    def set_prefix(self, text=""):
        self._value_prefix = text

    def update_information(self):
        width = self.name.size().width()
        if self._unit:
            self.name.setText(
                self.fm.elidedText(
                    f"{self._name} ({self._unit})", QtCore.Qt.ElideMiddle, width
                )
            )
        else:
            self.name.setText(
                self.fm.elidedText(self._name, QtCore.Qt.ElideMiddle, width)
            )
        self.set_value(self._value, update=True)
            
    def set_value(self, value, update=False):
        if self._value == value and update is False:
            return

        self._value = value
        if self.ranges and value not in ("", "n.a."):
            p = self.palette()

            for range in self.ranges:
                font_color, background_color, op1, op2, value1, value2 = range.values()

                result = False
                
                if value1 is not None:
                    if op1 == '==':
                        result = value1 == value
                    elif op1 == '!=':
                        result = value1 != value
                    elif op1 == '<=':
                        result = value1 <= value
                    elif op1 == '<':
                        result = value1 < value
                    elif op1 == '>=':
                        result = value1 >= value
                    elif op1 == '>':
                        result = value1 > value

                    if not result:
                        continue
                        
                if value2 is not None:
                    if op2 == '==':
                        result = value == value2
                    elif op2 == '!=':
                        result = value != value2
                    elif op2 == '<=':
                        result = value <= value2
                    elif op2 == '<':
                        result = value < value2
                    elif op2 == '>=':
                        result = value >= value2
                    elif op2 == '>':
                        result = value > value2

                    if not result:
                        continue

                if result:
                    new_background_color = background_color
                    new_font_color = font_color
                    break
            else:
                new_background_color = self._current_background_color
                new_font_color = self._current_font_color

            p.setColor(QtGui.QPalette.Base, new_background_color)
            p.setColor(QtGui.QPalette.Text, new_font_color)
            self.setPalette(p)

        else:
            p = self.palette()
            p.setColor(QtGui.QPalette.Base, self._current_background_color)
            p.setColor(QtGui.QPalette.Text, self._current_font_color)
            self.setPalette(p)

        template = "{{}}{}"
        if value not in ("", "n.a."):
            template = template.format(self.fmt)
        else:
            template = template.format("{}")
        try:
            self.value.setText(template.format(self._value_prefix, value))
        except (ValueError, TypeError):
            template = "{}{}"
            self.value.setText(template.format(self._value_prefix, value))

    def keyPressEvent(self, event):
        key = event.key()
        modifier = event.modifiers()
        if modifier == QtCore.Qt.ControlModifier and key == QtCore.Qt.Key_C:
            QtWidgets.QApplication.instance().clipboard().setText(self._name)

        elif (
            modifier == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier)
            and key == QtCore.Qt.Key_C
        ):
            QtWidgets.QApplication.instance().clipboard().setText(
                self.get_display_properties()
            )

        elif (
            modifier == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier)
            and key == QtCore.Qt.Key_P
        ):
            info = QtWidgets.QApplication.instance().clipboard().text()
            try:
                info = json.loads(info)
                self.set_color(info["color"])
                self.color_changed.emit(self.uuid, info["color"])
                self.set_fmt(info["format"])
                self.individual_axis.setCheckState(
                    QtCore.Qt.Checked
                    if info["individual_axis"]
                    else QtCore.Qt.Unchecked
                )
                self.ylink.setCheckState(
                    QtCore.Qt.Checked if info["ylink"] else QtCore.Qt.Unchecked
                )
                self.set_precision(info["precision"])

                parent = self.parent().parent().parent().parent().parent()
                sig, index = parent.plot.signal_by_uuid(self.uuid)
                viewbox = parent.plot.view_boxes[index]
                viewbox.setYRange(info["min"], info["max"], padding=0)

                # self.display.setCheckState(
                #     QtCore.Qt.Checked if info["display"] else QtCore.Qt.Unchecked
                # )

                self.ranges = info["ranges"]

            except:
                pass

        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        width = self.name.size().width()
        if self._unit:
            self.name.setText(
                self.fm.elidedText(
                    f"{self._name} ({self._unit})", QtCore.Qt.ElideMiddle, width
                )
            )
        else:
            self.name.setText(
                self.fm.elidedText(self._name, QtCore.Qt.ElideMiddle, width)
            )

    def text(self):
        return self._name

    def get_display_properties(self):
        info = {
            "color": self.color,
            "precision": self.precision,
            "ylink": self.ylink.checkState() == QtCore.Qt.Checked,
            "individual_axis": self.individual_axis.checkState() == QtCore.Qt.Checked,
            "format": "hex"
            if self.fmt.startswith("0x")
            else "bin"
            if self.fmt.startswith("0b")
            else "phys",
            # "display": self.display.checkState() == QtCore.Qt.Checked,
            "ranges": self.ranges,
        }

        parent = self.parent().parent().parent().parent().parent()

        sig, index = parent.plot.signal_by_uuid(self.uuid)

        min_, max_ = parent.plot.view_boxes[index].viewRange()[1]

        info["min"] = float(min_)
        info["max"] = float(max_)

        return json.dumps(info)

    def does_not_exist(self, exists=False):
        if not exists:
            icon = QtGui.QIcon()
            icon.addPixmap(
                QtGui.QPixmap(":/error.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off
            )
            self.color_btn.setIcon(icon)
            self.color_btn.setFlat(True)
            try:
                self.color_btn.clicked.disconnect()
            except:
                pass
        else:
            icon = QtGui.QIcon()
            self.color_btn.setIcon(icon)
            self.color_btn.setFlat(False)
            self.color_btn.clicked.connect(self.select_color)

    def disconnect_slots(self):
        self.color_changed.disconnect()
        self.enable_changed.disconnect()
        self.ylink_changed.disconnect()
        self.individual_axis_changed.disconnect()