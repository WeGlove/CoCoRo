import matplotlib
matplotlib.use("TkAgg")
from matplotlib import pyplot


class SuperPrinter:

    def __init__(self):
        self.fig, self.axe = pyplot.subplots(1,1)

    def plot(self, data):
        for i in range(8):
            filter = data[i][500:] - (sum(data[i][500:]) / len(data[i][500:]))
            self.axe.plot(filter)
        pyplot.show()
        self.axe.clear()


