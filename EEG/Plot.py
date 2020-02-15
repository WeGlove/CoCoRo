import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

import random
import colorsys

offset = 0  # just for debugging to simulate the EEG data flow.

win = pg.GraphicsWindow(size=(1500, 1000))
win.setWindowTitle('EEG signals')
win.setAntialiasing(True)

# win.setLabel(axis='left', text="asfd")

# create 8 subplots, one for each eeg electrode.
plots = [win.addPlot(col=1, row=r, xRange=[0, 1250], yRange=[-1, 1]) for r in range(8)]
for index, plot in enumerate(plots):
    plot.setLabel(axis='left', text=f"electrode {index + 1}")
# add one curve to each subplot
curves = [plot.plot() for plot in plots]

data = np.random.rand(8, 25000)
data -= .5
data *= 2


# until proper color are chosen, just using random ones.
def generate_color():
    h, s, l = random.random(), 0.5 + random.random()/2.0, 0.4 + random.random()/5.0
    return [int(256*i) for i in colorsys.hls_to_rgb(h, l, s)]


colors = [generate_color() for _ in range(8)]


def plot():
    # global offset
    for index, curve in enumerate(curves):
        pen = pg.mkPen(colors[index], style = QtCore.Qt.SolidLine)
        curve.setData(data[index][offset:offset + 1250], pen=pen)


def update():
    global offset
    offset += 1
    plot()


timer = pg.QtCore.QTimer()
timer.timeout.connect(update)
timer.start(1)
QtGui.QApplication.instance().exec_()
