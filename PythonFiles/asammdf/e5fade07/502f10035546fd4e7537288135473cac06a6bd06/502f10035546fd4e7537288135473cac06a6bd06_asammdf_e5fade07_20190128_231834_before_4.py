# -*- coding: utf-8 -*-

import pyqtgraph as pg
import numpy as np


class FormatedAxis(pg.AxisItem):
    def __init__(self, *args, **kwargs):

        super(FormatedAxis, self).__init__(*args, **kwargs)

        self.format = "phys"
        self.text_conversion = None

    def tickStrings(self, values, scale, spacing):
        strns = []

        if self.format == "phys":
            strns = super(FormatedAxis, self).tickStrings(values, scale, spacing)
            if self.text_conversion:
                strns = []
                for val in values:
                    nv = self.text_conversion.convert(np.array([val]))[0]
                    if isinstance(nv, bytes):
                        try:
                            strns.append(nv.decode("utf-8"))
                        except:
                            strns.append(nv.decode("latin-1"))
                    else:
                        strns.append(f"{val:.6f}")

        elif self.format == "hex":
            for val in values:
                val = float(val)
                if val.is_integer():
                    val = hex(int(val))
                else:
                    val = ""
                strns.append(val)

        elif self.format == "bin":
            for val in values:
                val = float(val)
                if val.is_integer():
                    val = bin(int(val))
                else:
                    val = ""
                strns.append(val)

        return strns

    def setLabel(self, text=None, units=None, unitPrefix=None, **args):
        """Set the text displayed adjacent to the axis.

        ==============  =============================================================
        **Arguments:**
        text            The text (excluding units) to display on the label for this
                        axis.
        units           The units for this axis. Units should generally be given
                        without any scaling prefix (eg, 'V' instead of 'mV'). The
                        scaling prefix will be automatically prepended based on the
                        range of data displayed.
        **args          All extra keyword arguments become CSS style options for
                        the <span> tag which will surround the axis label and units.
        ==============  =============================================================

        The final text generated for the label will look like::

            <span style="...options...">{text} (prefix{units})</span>

        Each extra keyword argument will become a CSS option in the above template.
        For example, you can set the font size and color of the label::

            labelStyle = {'color': '#FFF', 'font-size': '14pt'}
            axis.setLabel('label text', units='V', **labelStyle)

        """
        show_label = False
        if text is not None:
            self.labelText = text
            show_label = True
        if units is not None:
            self.labelUnits = units
            show_label = True
        if show_label:
            self.showLabel()
        if unitPrefix is not None:
            self.labelUnitPrefix = unitPrefix
        if len(args) > 0:
            self.labelStyle = args
        self.label.setHtml(self.labelString())
        self._adjustSize()
        self.picture = None
        self.update()
