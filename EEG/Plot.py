import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

import random
import colorsys


def generate_color():
    h, s, l = random.random(), 0.5 + random.random() / 2.0, 0.4 + random.random() / 5.0
    return [int(256 * i) for i in colorsys.hls_to_rgb(h, l, s)]


class GUI:

    def __init__(self):

        self.offset = 0  # just for debugging to simulate the EEG data flow.

        self.win = pg.GraphicsWindow(size=(1500, 1000))
        self.win.setWindowTitle('EEG signals')
        self.win.setAntialiasing(True)  # not sure if it does anything

        # create 8 subplots, one for each eeg electrode.
        self.plots = [self.win.addPlot(col=1, row=r, xRange=[0, 1250], yRange=[-1, 1]) for r in range(8)]
        for index, plot in enumerate(self.plots):
            plot.setLabel(axis='left', text=f"electrode {index + 1}")
        # add one curve to each subplot
        self.curves = [plot.plot() for plot in self.plots]

        self.data = np.random.rand(8, 25000)
        self.data -= .5
        self.data *= 2

        # until proper color are chosen, just using random ones.
        self.colors = [generate_color() for _ in range(8)]

    def plot(self):
        for index, curve in enumerate(self.curves):
            pen = pg.mkPen(self.colors[index], style=QtCore.Qt.SolidLine)
            curve.setData(self.data[index][self.offset:self.offset + 1250], pen=pen)

    def update(self):
        self.offset += 1
        self.plot()


gui = GUI()

timer = pg.QtCore.QTimer()
timer.timeout.connect(gui.update)
timer.start(1)
QtGui.QApplication.instance().exec_()
