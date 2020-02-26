import numpy as np
import threading

import data
from utils import threaded
from gui import Gui
from hal_eeg import Hal_eeg  # hardware abstraction layer for the eeg headset

# test client for debugging
# TODO: remove as soon as actual client class is ported.
class Client:
    @threaded
    def run(self):
        t = threading.currentThread()
        while getattr(t, "do_run", True):
            # no type check or similar, input has to be a float
            # otherwise the client thread will crash.
            x = input('Input:\t')
            data.confidence = float(x)

def main():
    # start all modules separately, i.e. the client, the eeg device,...
    eeg_handle = Hal_eeg().run()
    client_handle = Client().run()

    # start the Gui in the main thread and wait until we close it.
    Gui().start()
    # as soon as the gui window gets closed, we close all the remaining threads.
    eeg_handle.do_run = False
    client_handle.do_run = False
    eeg_handle.join()
    client_handle.join()

if __name__ == '__main__':
    main()
