import matplotlib
matplotlib.use("TkAgg")
from matplotlib import pyplot


class SuperPrinter:

    CUTOFF = 0

    def __init__(self):
        self.fig, self.axe = pyplot.subplots(1,1)

    def plot(self, data):
        for i in range(8):
            filter = data[i][self.CUTOFF:] - (sum(data[i][self.CUTOFF:]) / len(data[i][self.CUTOFF:]))
            self.axe.plot(filter, markevery=250, marker="o")
        pyplot.show()
        self.axe.clear()


