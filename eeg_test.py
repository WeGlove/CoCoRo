import UnicornPy
import matplotlib
import numpy as np
import struct
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
data = np.zeros(8)

deviceList = UnicornPy.GetAvailableDevices(True)
print(deviceList)

if (len(deviceList) == 0):
    raise("Couldn't find a device")

device = UnicornPy.Unicorn(deviceList[0])

device.StartAcquisition(False)
print(device.GetNumberOfAcquiredChannels())
channel_number = device.GetNumberOfAcquiredChannels()
receiveBufferBufferLength = 250 * channel_number * 3
receiveBuffer = bytearray(receiveBufferBufferLength)

while True:
    device.GetData(250, receiveBuffer, receiveBufferBufferLength)
    for i in range(channel_number):
        print(f"Channel {i}")
        print(receiveBuffer[i], end=' ')
        print(receiveBuffer[i+1], end=' ')
        print(receiveBuffer[i+2])
        print(struct.unpack('f', b'\x00'+receiveBuffer[i:i+3]))
    print(receiveBuffer)

device.StopAcquisition()

