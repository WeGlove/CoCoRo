import time

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

import random
import colorsys
import threading


def generate_color():
    """ Generates bright colors and avoids black.
        Used to color the different EEG signal plots.
    """
    h, s, l = random.random(), 0.5 + random.random() / 2.0, 0.4 + random.random() / 5.0
    return [int(256 * i) for i in colorsys.hls_to_rgb(h, l, s)]


class GUI:

    def __init__(self):
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

    def update(self):
        """ GUI update procedure. Currently working on the global numpy array
            containing the data. Not a clean implementation, but currently the
            best.
        """
        global data
        for index, curve in enumerate(self.curves):
            pen = pg.mkPen(self.colors[index], style=QtCore.Qt.SolidLine)
            curve.setData(data[index][-1250:], pen=pen)


def threaded(fn):
    """ Decorator for the thread run method.
        Used to get a handle of the thread for joining the thread after
        using it.
    """
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class GUI_thread:
    """ GUI thread creates the qt window and plots all 8 eeg signal graphs.
        Currently the timer is set to 4, which should be 4 milliseconds, which
        should be exactly the interval of new data arriving from the EEG headset.
    """
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

# update the global numpy array containing the simulated EEG signal data.
while True:
    new_data = np.random.rand(8, 1)
    new_data -= .5  # center it on the origin
    new_data *= 2  # scale it for better visualization
    data = np.c_[data, new_data]
    time.sleep(.004)  # one sample every 4 ms -> 250 hz

# handle.join()
