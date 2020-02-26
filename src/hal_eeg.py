import threading
import time
import numpy as np

from utils import threaded
import data

class Hal_eeg:
    """ Hardware abstraction layer for the EEG headset.
        Basically just simulates the incoming eeg signals for all
        eight electrodes from the eeg headset.
        The data gets stored in the global variable `data.eeg_matrix`
    """
    @threaded
    def run(self):
        t = threading.currentThread()
        i = 0
        while getattr(t, "do_run", True):
            value = np.zeros((8,1)) if (i % 500) < 250 else np.ones((8,1))
            i += 1
            data.eeg_matrix = np.c_[data.eeg_matrix, value]
            time.sleep(4 / 1000)  # simulate the 250 hz frequency
