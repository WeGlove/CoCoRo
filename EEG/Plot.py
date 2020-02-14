import matplotlib.pyplot as plt
import numpy as np

#TODO: put the whole plot functionality in a class and integrate with the
# actual data array
#############################################################
# generate test data. 250 = frequency, 10 = time in seconds
data = np.random.rand(8, 0)
for _ in range(250 * 10):
    new_data = np.random.rand(8, 1)
    data = np.c_[data, new_data]
#############################################################

plt.ion()
#TODO: choose and exchange some colors. For example `pink` on white background
# is not very appealing.
colors = ['red', 'blue', 'green', 'yellow', 'cyan', 'violet', 'orange', 'pink']
fig, axs = plt.subplots(8, 1, sharex=True)
line = [None] * 8
fig.suptitle("EEG signals", fontsize=20)

for i in range(8):  # for all features one plot
    # display the last 500 elements of the data matrix
    # assuming the eeg already recorded 2 seconds!!!!!!
    # for demonstration not the last 500 elements, but a sliding window of 500
    # elements to simulate realtime data flow.
    # line[i], = axs[i].plot(data[i][-500:], color=colors[i])  # returns a tuple of line objects, thus the comma
    line[i], = axs[i].plot(data[i][0:500], color=colors[i])  # returns a tuple of line objects, thus the comma
    axs[i].set_title(f"electrode {i}")
    axs[i].set_ylabel("frequency")
axs[7].set_xlabel("timestamp")

# update the plot data instead of clearing + redrawing the whole diagram.
# since we are using the last 500 elements / the last 2 seconds and the
# data matrix is updated constantly in the background, we should get a nice
# realtime data plot.
#TODO: obviously put the live plot in a separate GUI thread.
# for demonstration we just shift a sliding window of size 500 over the array
# to simulate realtime data flow.
for offset in range(2000):
    for i in range(8):
        line[i].set_ydata(data[i][offset: 500 + offset])
    fig.canvas.draw()
    fig.canvas.flush_events()

