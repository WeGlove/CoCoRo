import UnicornPy


class EEG:

    def __init__(self, filename):
        self.frame_length = 1  # for debugging purpose just one sample
        self.bytes_per_channel = 3
        self.filename = filename

        devices = UnicornPy.GetAvailableDevices(True)
        print(devices)
        if len(devices) == 0:
            raise Exception("Couldn't find a device.")
        self.device = UnicornPy.Unicorn(devices[0])  # assuming only on device is in range.

    def record(self):
        # start the acquisition of the EEG headset
        self.device.StartAcquisition(False)
        number_of_channels = self.device.GetNumberOfAcquiredChannels()
        print(number_of_channels)
        buffer_length = self.frame_length * number_of_channels * self.bytes_per_channel
        buffer = bytearray(buffer_length)

        while True:
            self.device.GetData(self.frame_length, buffer, buffer_length)
            for byte in buffer:
                print(f"{byte:03}", end=' ')
            self.__write_to_file(buffer)
            print()
            break  # for debugging

        read_buffer = bytearray(buffer_length)
        self.__read_from_file(read_buffer)
        for byte in read_buffer:
            print(f"{byte:03}", end=' ')
        print()

    def __write_to_file(self, data):
        # maybe change type to appending instead of overwriting.
        with open(self.filename, 'wb') as f:
            for byte in data:
                f.write(byte)

    def __read_from_file(self, data):
        with open(self.filename, 'rb') as f:
            byte = f.read(1)
            i = 0
            while byte:
                data[i] = byte
                i += 1
                byte = f.read(1)

eeg = EEG('test.bin')
eeg.record()
