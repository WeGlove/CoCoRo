from matplotlib import pyplot


class SuperPrinter:

    @staticmethod
    def plot(data):
        for i in range(8):
            #print(data[i])
            pyplot.plot(data[i])
        pyplot.show()
