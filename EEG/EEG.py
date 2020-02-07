import UnicornPy
import threading
import time
import numpy as np
import struct
from EEG import SuperPrinter


class EEG:

    def __init__(self, filename):
        self.__filename = filename

        self.__frame_length = 1  # for debugging purpose just one sample
        self.__bytes_per_channel = 4  # actual 3 bytes per channel but one for buffer.
        self.__features = 8  # number of channel / features / column of data matrix
        
        self.__recording = False
        self.__record_thread = threading.Thread(target=self.__record)

        # data matrix containing features as column vectors.
        self.__data = np.zeros((self.__features, 0))
        # event list containing (`index`, `event`) tuples.
        self.__events = []

        self.device = self.__get_eeg_device()

    def get_data(self):
        return self.__data

    def toggle_recording(self):
        if not self.__recording:
            self.__record_thread.start()
        else:
            self.__record_thread.do_run = False
            self.__record_thread.join()
            # TODO: write data matrix to file.
        self.__recording = not self.__recording
        
    def set_event(self, index, event):
        self.__events.append((index, event))

    def print_d(self):
        print(self.__data)

    def print_e(self):
        print(self.__events)

    def __record(self):
        t = threading.currentThread()
        # as long as `do_run` flag has not been set from main thread continue
        self.device.StartAcquisition(True)
        print(self.device.GetNumberOfAcquiredChannels())
        self.__channel_number = self.device.GetNumberOfAcquiredChannels()

        while getattr(t, "do_run", True):
            # acquire eeg data.
            # TODO: get actual eeg data and convert the 24 bit data to proper floats
            # TODO: maybe filter values online?!
            new_data = self.__get_eeg_data()
            #new_data = np.random.rand(self.__features, 1)
            # append the new data vector to the right of the data matrix.
            self.__data = np.c_[ self.__data, new_data ]
            #self.print_d()
            #time.sleep(1)
        print("stopping")

    def __get_eeg_device(self):
        devices = UnicornPy.GetAvailableDevices(True)
        print(devices)
        if len(devices) == 0:
            raise Exception("Couldn't find a device.")
        return UnicornPy.Unicorn(devices[0])  # assuming only on device is in range.

    def __get_eeg_data(self):
        buffer_length = self.__frame_length * self.__channel_number * self.__bytes_per_channel
        buffer = bytearray(buffer_length)
        self.device.GetData(self.__frame_length, buffer, buffer_length)
        data = np.zeros((self.__features, 0))
        for _ in range(self.__frame_length):
            i = 0
            d = []
            while i < self.__features * 4:  # 3 being the precision
                d.append(struct.unpack('f', buffer[i:i + 4]))
                i += 4
            nd = np.array(d)
            #print(nd[0])
            data = np.c_[data, nd]
        return data

    def __write_to_file(self, data):
        # maybe change type to appending instead of overwriting.
        with open(self.__filename, 'wb') as f:
            f.write(data)

    def __read_from_file(self):
        with open(self.__filename, 'rb') as f:
            data = f.read()
        return data



