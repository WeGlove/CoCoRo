import time
import random
import colorsys
import threading

import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui


def generate_color():
    """ Generates bright colors and avoids black.
        Used to color the different EEG signal plots.
    """
    h, s, l = random.random(), 0.5 + random.random() / 2.0, 0.4 + random.random() / 5.0
    return [int(256 * i) for i in colorsys.hls_to_rgb(h, l, s)]

class GUI:
    """ Main GUI window class. Defines the window and initializes the graphs
        for the data from each electrode coming from the EEG headset.
    """

    def __init__(self):
        self.win = pg.GraphicsWindow(size=(1500, 1000))
        self.win.setWindowTitle('EEG signals')
        self.win.setAntialiasing(True)  # not sure if it does anything
        self.win.enableMouse(False)  # sadly does nothing...
        # self.win.showMaximized()

        # create 8 subplots, one for each eeg electrode.
        self.plots = [self.win.addPlot(col=1, row=r, xRange=[0, 1250], yRange=[-1, 1]) for r in range(8)]
        for index, plot in enumerate(self.plots):
            plot.setLabel(axis='left', text=f"electrode {index + 1}")
        # add one curve to each subplot
        self.curves = [plot.plot() for plot in self.plots]

        # until proper color are chosen, using random ones.
        self.colors = [generate_color() for _ in range(8)]

        self.confidence_label = self.win.addLabel(f'< span style = " font-size:20pt; font-weight:600;" >Prediction confidence: {0.00}< / span >', col=1, row=9)
        # self.confidence_label.setAlignment(QtCore.Qt.AlignLeft)

    def update(self):
        """ GUI update procedure. Currently working on the global numpy array
            containing the data. Not a clean implementation, but currently the
            best.
        """
        global data  # currently the best option to use a global variable.
        global confidence

        # example label value
        val = data[0][-1]
        if val < 0:
            val *= -1
        self.confidence_label.setText(f'< span style = " font-size:20pt; font-weight:600;" >Prediction confidence: {confidence:.2f}< / span >')

        # schedule a repaint for each subplot.
        for index, curve in enumerate(self.curves):
            pen = pg.mkPen(self.colors[index], style=QtCore.Qt.SolidLine)
            curve.setData(data[index][-1250:], pen=pen)  # get the last 1250 elements
        # apply the render events.
        pg.QtGui.QApplication.processEvents()  # not sure if necessary or useful?!


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
        Currently the timer is set to 4, which should be exactly the interval
        of new data arriving from the EEG headset.
    """

    @threaded
    def run(self):
        gui = GUI()
        timer = pg.QtCore.QTimer()
        timer.timeout.connect(gui.update)
        # Since our EEG headset only has a frequency of 250 hz, it should
        # suffice to use a timer of 4 ms to keep track of the incoming data.
        timer.start(4)  # strangely everything below 100 ms is the same.
        QtGui.QApplication.instance().exec_()  # may store the app handle?


# we need at least 1250 elements in the data matrix before executing the gui
# thread, otherwise it will crash because we are out of bounds.
#data -= .5
#data *= 2

#handle = GUI_thread().run()

# we will simulate the data flow, coming from the EEG headset.
# As soon as the GUI window gets closed we shut down the entire program.
"""
while handle.is_alive():
    new_data = np.random.rand(8, 1)
    new_data -= .5  # center it on the origin
    new_data *= 2  # scale it for better visualization
    data = np.c_[data, new_data]
    time.sleep(4 / 1000)  # one sample every 4 ms -> 250 hz

handle.join()
"""