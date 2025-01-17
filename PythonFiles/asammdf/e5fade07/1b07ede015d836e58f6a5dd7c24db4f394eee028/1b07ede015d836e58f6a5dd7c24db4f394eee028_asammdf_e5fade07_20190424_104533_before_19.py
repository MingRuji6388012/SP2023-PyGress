# -*- coding: utf-8 -*-

from pathlib import Path

from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import uic

from ..ui import resource_qt5 as resource_rc

HERE = Path(__file__).resolve().parent


class ChannelInfoWidget(QtWidgets.QWidget):
    def __init__(self, channel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(HERE.joinpath("..", "ui", "channel_info_widget.ui"), self)

        self.channel_label.setText(channel.metadata())

        if channel.conversion:
            self.conversion_label.setText(channel.conversion.metadata())

        if channel.source:
            self.source_label.setText(channel.source.metadata())
