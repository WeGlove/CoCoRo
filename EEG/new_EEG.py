# import UnicornPy
import threading
import time
import numpy as np



class EEG:

    def __init__(self, filename):
        self.__filename = filename

        self.__frame_length = 1  # for debugging purpose just one sample
        self.__bytes_per_channel = 4  # actual 3 bytes per channel but one for buffer.
        self.__features = 8  # number of channel / features / column of data matrix
        
        self.__recording = False
        self.__record_thread = threading.Thread(target = self.__record)

        self.__data = np.zeros((self.__features, 1))
        self.__events = []

        # self.device = self.__get_eeg_device()

    def print(self):
        print(self.__data)

    def toggle_recording(self):
        if self.__recording:
            self.__record_thread.do_run = False
            self.__record_thread.join()
        else:
            self.__record_thread.start()
        self.__recording = not self.__recording
        
    def set_event(self, index, event):
        self.__events.append((index, event))

    def __record(self):
        t = threading.currentThread()
        while getattr(t, "do_run", True):
            # working
            self.__data = np.c_[ self.__data, np.ones(self.__features) ]
            self.print()
            time.sleep(1)
        print("stopping")

    # def __get_eeg_device(self):
    #     devices = UnicornPy.GetAvailableDevices(True)
    #     print(devices)
    #     if len(devices) == 0:
    #         raise Exception("Couldn't find a device.")
    #     return UnicornPy.Unicorn(devices[0])  # assuming only on device is in range.

    def __write_to_file(self, data):
        # maybe change type to appending instead of overwriting.
        with open(self.__filename, 'wb') as f:
            f.write(data)

    def __read_from_file(self):
        with open(self.__filename, 'rb') as f:
            data = f.read()
        return data

eeg = EEG('test.bin')
eeg.print()
eeg.toggle_recording()
time.sleep(5)
eeg.toggle_recording()
eeg.print()

