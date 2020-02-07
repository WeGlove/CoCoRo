from matplotlib import pyplot


class SuperPrinter:

    def __init__(self):
        pass

    @staticmethod
    def plot(data):
        for i in range(8):
            #print(data[i])
            pyplot.plot(data[i])
        pyplot.show()