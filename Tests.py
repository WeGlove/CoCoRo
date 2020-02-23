import numpy as np
import unittest
from EEG.EEG import EEG
from EEG.EEG import SuperPrinter
from keras.utils import to_categorical
import Net
import Client

class Tests(unittest.TestCase):

    def test_Event_set(self):
        device = EEG("")
        device.set_event(2)
        events = device.get_events()
        assert len(events) == 1, "EventList not of length 1"
        assert events[0][0] == 0 and events[0][1] == 2, "Incorrect event saved"

    def test_Event_index(self):
        device = EEG("")
        tmp_data = np.zeros((8,0))
        for _ in range(10):
            d = np.random.rand(8, 1)
            tmp_data = np.c_[tmp_data, d]
        device.set_data(tmp_data)
        device.set_event(2)
        events = device.get_events()
        assert len(events) == 1, "EventList not of length 1"
        assert events[0][0] == 10 and events[0][1] == 2, "Incorrect event saved"

    def test_io(self):
        device = EEG("")
        tmp_data = np.zeros((8,0))
        for _ in range(10):
            d = np.random.rand(8, 1)
            tmp_data = np.c_[tmp_data, d]
        device.set_data(tmp_data)
        device.set_event(2)

        device.write_to_file()

        device.read_from_file()
        events = device.get_events()
        data = device.get_data()

        assert len(events) == 1, "EventList not of length 1"
        assert events[0][0] == 10 and events[0][1] == 2, "Incorrect event saved"

        bools = tmp_data == data
        assert bools.all(), "Loaded incorrectly"

    def test_net_train(self):
        shape = np.array([8, 250, 1])
        net = Net.Net(shape)
        net.createCNN()
        vals = np.array([np.array(np.random.rand(8, 250, 1))] * 192)
        print(vals.shape)
        print(vals[0])
        print("=============================")
        print(vals[1])

        labels = [0] * ((6 * 32)-1)
        labels.append(1)
        labels = to_categorical(labels)
        print(labels)
        net.fit(vals, labels, 6)

        predict = np.array([np.array(np.random.rand(8, 250, 1))])

    def test_dist(self):
        import random
        client = Client.Client(10)
        agg = [0]*12
        for _ in range(1_000_000):
            agg[random.choice(client.createDistribution(2, 0.66))] += 1
        agg = [val/1_000_000 for val in agg]
        print(agg)




