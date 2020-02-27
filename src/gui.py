import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

import data
from utils import generate_color


class Gui:
    """ Main GUI window class. Defines the window and initializes the graphs
        for the data from each electrode coming from the EEG headset.
    """
    def __init__(self):
        self.win = pg.GraphicsWindow(size=(1500, 1000))
        self.win.setWindowTitle('EEG signals')

        # create 8 subplots, one for each eeg electrode.
        self.plots = [self.win.addPlot(col=1, row=r, xRange=[0, 1250], yRange=[-1, 1]) for r in range(8)]
        for index, plot in enumerate(self.plots):
            plot.setLabel(axis='left', text=f"electrode {index + 1}")
        # add one curve to each subplot
        self.curves = [plot.plot() for plot in self.plots]

        # until proper color are chosen, using random ones.
        self.colors = [generate_color() for _ in range(8)]

        self.confidence_label = self.win.addLabel(f'< span style = " font-size:20pt; font-weight:600;" >Prediction confidence: {0.00}< / span >', col=1, row=9)

    def start(self):
        timer = pg.QtCore.QTimer()
        timer.timeout.connect(self.update)
        # Since our EEG headset only has a frequency of 250 hz, it should
        # suffice to use a timer of 4 ms to keep track of the incoming data.
        timer.start(4)  # strangely everything below 100 ms is the same.
        QtGui.QApplication.instance().exec_()  # may store the app handle?

    def update(self):
        """ GUI update procedure. Currently working on the global numpy array
            containing the data. Not a clean implementation, but currently the
            best.
        """
        self.confidence_label.setText(f'< span style = " font-size:20pt; font-weight:600;" >Prediction confidence: {data.confidence:.2f}< / span >')

        # schedule a repaint for each subplot.
        for index, curve in enumerate(self.curves):
            pen = pg.mkPen(self.colors[index], style=QtCore.Qt.SolidLine)
            curve.setData(data.eeg_matrix[index][-1250:], pen=pen)  # get the last 1250 elements
        # apply the render events.
        pg.QtGui.QApplication.processEvents()  # not sure if necessary or useful?!
