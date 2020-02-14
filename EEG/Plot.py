import matplotlib.pyplot as plt
import numpy as np

# TODO: put the whole plot functionality in a class and integrate with the
# actual data array
# generate test data. 250 = frequency, 10 = time in seconds
data = np.random.rand(8, 2500)

plt.ion()
# TODO: choose and exchange some colors. For example `pink` on white background
# is not very appealing.
colors = ['red', 'blue', 'green', 'yellow', 'cyan', 'violet', 'orange', 'pink']
fig, axes = plt.subplots(8, 1, sharex=True)
lines = [None] * 8
fig.suptitle("EEG signals", fontsize=20)
fig.show()
fig.canvas.draw()

for i in range(8):  # for all features one plot
    # display the last 500 elements of the data matrix
    # assuming the eeg already recorded 2 seconds!!!!!!
    # for demonstration not the last 500 elements, but a sliding window of 500
    # elements to simulate realtime data flow.
    # line[i], = axs[i].plot(data[i][-500:], color=colors[i])  # returns a tuple of line objects, thus the comma
    lines[i], = axes[i].plot(data[i][0:500], color=colors[i], animated=True)
    axes[i].set_title(f"electrode {i}")
    axes[i].set_ylabel("frequency")
axes[7].set_xlabel("timestamp")

# store the background of the plots to reuse them instead of redrawing.
backgrounds = [fig.canvas.copy_from_bbox(ax.bbox) for ax in axes]

# update the plot data instead of clearing + redrawing the whole diagram.
# since we are using the last 500 elements / the last 2 seconds and the
# data matrix is updated constantly in the background, we should get a nice
# realtime data plot.
# TODO: obviously put the live plot in a separate GUI thread.
# for demonstration we just shift a sliding window of size 500 over the array
# to simulate realtime data flow.
for offset in range(2000):
    for i in range(8):
        fig.canvas.restore_region(backgrounds[i])
        lines[i].set_ydata(data[i][offset: 500 + offset])
        axes[i].draw_artist(lines[i])
        fig.canvas.blit(axes[i].bbox)
