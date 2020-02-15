import time

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

import random
import colorsys
import threading


def generate_color():
    h, s, l = random.random(), 0.5 + random.random() / 2.0, 0.4 + random.random() / 5.0
    return [int(256 * i) for i in colorsys.hls_to_rgb(h, l, s)]


class GUI:

    def __init__(self):

        # self.data = data

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

        # until proper color are chosen, just using random ones.
        self.colors = [generate_color() for _ in range(8)]

    def plot(self):
        global data
        for index, curve in enumerate(self.curves):
            pen = pg.mkPen(self.colors[index], style=QtCore.Qt.SolidLine)
            # curve.setData(self.data[index][self.offset:self.offset + 1250], pen=pen)
            curve.setData(data[index][-1250:], pen=pen)

    def update(self):
        self.offset += 1
        self.plot()


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class GUI_thread:
    @threaded
    def run(self):
        _gui = GUI()
        timer = pg.QtCore.QTimer()
        timer.timeout.connect(_gui.update)
        timer.start(4)
        QtGui.QApplication.instance().exec_()


data = np.random.rand(8, 2500)
data -= .5
data *= 2

gui = GUI_thread()
handle = gui.run()

while True:
    new_data = np.random.rand(8, 1)
    new_data -= .5
    new_data *= 2
    data = np.c_[data, new_data]
    time.sleep(.004)  # 250 hz
    # print(data[0][-1:])

handle.join()
