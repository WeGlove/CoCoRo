import data

import UnicornPy

import threading
import numpy as np
import struct
import json


class Eeg:
    def __init__(self, path):
        self._path = path

        self._frame_length = 1  # for debugging purpose just one sample
        self._bytes_per_channel = 4  # actual 3 bytes per channel but one for buffer.
        self._features = 8  # number of channel / features / column of data matrix
        
        self._recording = False
        self._record_thread = threading.Thread(target=self._record)

        self.device = self._get_eeg_device()

    def toggle_recording(self):
        if not self._recording:
            self._record_thread = threading.Thread(target=self._record)
            self._record_thread.start()
        else:
            self._record_thread.do_run = False
            self._record_thread.join()
            while self._record_thread.is_alive():
                pass
        self._recording = not self._recording
        
    def _get_eeg_device(self):
       devices = UnicornPy.GetAvailableDevices(True)
       print(devices)
       if len(devices) == 0:
           raise Exception("Couldn't find a device.")
       return UnicornPy.Unicorn(devices[0])  # assuming only on device is in range.

    def _record(self):
        t = threading.currentThread()
        # as long as `do_run` flag has not been set from main thread continue
        self.device.StartAcquisition(False)
        print(self.device.GetNumberOfAcquiredChannels())
        self._channel_number = self.device.GetNumberOfAcquiredChannels()

        while getattr(t, "do_run", True):
            # acquire eeg data.
            new_data = self._get_eeg_data()
            # append the new data vector to the right of the data matrix.
            data.eeg_matrix = np.c_[ data.eeg_matrix, new_data ]
        self.device.StopAcquisition()
        print("stopping")

    def _get_eeg_data(self):
        buffer_length = self._frame_length * self._channel_number * self._bytes_per_channel
        buffer = bytearray(buffer_length)
        self.device.GetData(self._frame_length, buffer, buffer_length)
        i = 0
        d = []
        while i < self._features * 4:
            d.append(struct.unpack('f', buffer[i:i + 4]))
            i += 4
        return np.array(d)

    def write_to_file(self, dataname="data", eventname="events"):
        np.save(self._path + dataname, data.eeg_matrix)
        with open(self._path + eventname + ".json", "w") as f:
            json.dump(data.eeg_events, f)

    def read_from_file(self, dataname="data", eventname="events"):
        data.eeg_matrix = np.load(self._path + dataname)
        with open(self._path + eventname, "r") as f:
            data.eeg_events = json.load(f)

    # the following methods are redundant and obsolete, because the data no
    # longer is part of this class and is globaly reachable inside the data
    # module.
    # They are just here to guarantee that no old code breaks.
    def clear(self):
        """ Clears the events list and the EEG data. """
        data.eeg_events = []
        data.eeg_matrix = np.zeros((self._features, 0))

    def set_event(self, event):
        data.eeg_events.append([len(data.eeg_matrix[0, :]), event])

    def set_data(self, data):
        data.eeg_matrix = data

    def get_data(self):
        return data.eeg_matrix

    def get_events(self):
        return data.eeg_events
