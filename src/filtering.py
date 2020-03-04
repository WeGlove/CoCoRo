import statistics
from scipy import signal, fftpack
import numpy
import mne
mne.set_log_level(False)

class Filtering:

    BAD = 0
    POOR = 1
    GOOD = 2

    BANDWITH = 2

    @staticmethod
    def check_quality(data, sfreq):
        """
        The quality check described in 18.8.2 in the manual
        :param data: the data matrix. Tobe in accordance with the manual, input exactly 2 seconds of material
        :return: The signal quality in BAD=0 POOR=1 and GOOD=2
        """
        std_checks = Filtering.check_std(data)
        bpmd_checks = Filtering.check_bpmd(data,sfreq)
        return [Filtering.GOOD if std_checks[i] and bpmd_checks[i] else
                (Filtering.POOR if std_checks[i] or bpmd_checks[i] else Filtering.BAD)
                for i in range(len(data))]


    @staticmethod
    def check_std(data):
        """
        The standard deviation check as described in 18.8.2 in the manual.
        :param data: the data matrix
        :return: a boolean array indicating good(True) and bad(False) signal quality for each channel
        """
        return [7 < statistics.stdev(row) < 50 for row in data]

    @staticmethod
    def check_bpmd(data, sfreq):
        """
        The standard bandpass median difference check as described in 18.8.2 in the manual.
        :param data: the data matrix
        :return: a boolean array indicating good(True) and bad(False) signal quality for each channel
        """

        # Apply Notch filters
        fif_num, fif_dem = signal.iirnotch(50, 50/Filtering.BANDWITH, fs=sfreq)
        six_num, six_dem = signal.iirnotch(60, 60/Filtering.BANDWITH, fs=sfreq)
        notch_data = [signal.lfilter(six_num, six_dem,signal.lfilter(fif_num, fif_dem, row)) for row in data]
        notch_freqs = [fftpack.rfft(row) for row in notch_data]
        notch_mean = [sum(row[51 - 2:51 + 2]) / len(row[51 - 2:51 + 2]) +
                      sum(row[61 - 2:61 + 2]) / len(row[61 - 2:61 + 2])
                      for row in notch_freqs]
        notch_mean = [val/2 for val in notch_mean]

        # Apply Band Pass
        band_num, band_dem = signal.butter(2,[0.1/(sfreq/2),30/(sfreq/2)], output='ba', btype="bandpass")
        band_data = [signal.lfilter(band_num, band_dem,signal.lfilter(band_num, band_dem, row)) for row in data]
        band_freqs = [fftpack.rfft(row) for row in band_data]
        band_mean = [sum(row[1:30]) / len(row[1:30])
                     for row in band_freqs]

        return [band_mean[i] - notch_mean[i] > 0.1 for i in range(len(band_mean))]

    @staticmethod
    def scale(data, factor):
        return numpy.array([(val*factor for val in row) for row in data])

    @staticmethod
    def notch(data, freq=50,sfreq=250):
        fif_num, fif_dem = signal.iirnotch(50, 50 / Filtering.BANDWITH, fs=sfreq)
        return numpy.array([signal.lfilter(fif_num, fif_dem, row) for row in data])

    @staticmethod
    def bandpass(data, sfreq=250):
        new_data = mne.filter.filter_data(data, sfreq, 5, 40)
        #print(type(new_data))
        #print(new_data.shape)

        #b,a = signal.butter(3,[5/(sfreq/2),40/(sfreq/2)], btype="band")
        #new_data = [signal.lfilter(b, a, row)for row in data]
        return new_data

    @staticmethod
    def car(data):
        acc = numpy.average(data, axis=0)
        print(f"Acc:{acc}")
        return numpy.array([row - acc for row in data])





