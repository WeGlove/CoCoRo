import UnicornPy
import threading
import time
import numpy as np
import struct
from EEG import SuperPrinter
import json


class EEG:

    def __init__(self, path):
        self.__path = path

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

    def get_events(self):
        return self.__events

    def toggle_recording(self):
        if not self.__recording:
            self.__record_thread = threading.Thread(target=self.__record)
            self.__record_thread.start()
        else:
            self.__record_thread.do_run = False
            self.__record_thread.join()
            while self.__record_thread.is_alive():
                pass
            # TODO: write data matrix to file.
        self.__recording = not self.__recording
        
    def set_event(self, event):
        self.__events.append([len(self.__data[0, :]), event])

    def set_data(self, data):
        self.__data = data

    def print_d(self):
        print(self.__data)

    def print_e(self):
        print(self.__events)

    def __record(self):
        t = threading.currentThread()
        # as long as `do_run` flag has not been set from main thread continue
        self.device.StartAcquisition(False)
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
        self.device.StopAcquisition()
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
        #data = np.zeros((self.__features, 0))
        #for _ in range(self.__frame_length):
        i = 0
        d = []
        while i < self.__features * 4:  # 3 being the precision
            d.append(struct.unpack('f', buffer[i:i + 4]))
            i += 4
        return np.array(d)
            #print(nd[0])
        #    data = np.c_[data, nd]
        #return data

    def clear(self):
        """
            Clears the events list and the EEG data
        """
        self.__events = []
        self.__data = np.zeros((self.__features, 0))

    def write_to_file(self, dataname="data", eventname="events"):
        np.save(self.__path + dataname, self.__data)
        with open(self.__path + eventname + ".json", "w") as f:
            json.dump(self.__events, f)



    def read_from_file(self, dataname="data", eventname="events"):
        self.__data = np.load(self.__path + dataname)
        with open(self.__path + eventname, "r") as f:
            self.__events = json.load(f)



