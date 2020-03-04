import numpy as np

# data matrix containing the eeg signals of all eight electrodes
# The data is arranged as column vectors, each column represents
# one measure, every row containing one electrode.
eeg_matrix = np.zeros((8, 1250))

eeg_events = []

# The confidence of our prediction.
confidence = 0
