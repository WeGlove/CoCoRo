import numpy as np

# data matrix containing the eeg signals of all eigth electrodes
# The data is arranged as colomn vectors, each colomn represents
# one measure, every row containing one electrode.
eeg_matrix = np.zeros((8, 1250))  # we have to fill it with some values
                                  # before we can safely start the gui.

eeg_events = []

# The confidence of our prediction.
confidence = 0.42