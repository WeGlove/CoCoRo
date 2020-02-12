import Robot
import Net
import time
import random
from yee.de.dfki.tecs.robot.baxter.ttypes import *
#from EEG import EEG
from enum import Enum
import os
import json


class Events(Enum):
    DEFAULT =           0b0000000

    MOVED =             0b0001000

    MOVEARMLEFT =       0b0000010
    MOVEARMRIGHT =      0b0000011

    MOVECATEGROYLEFT =  0b0000100
    MOVECATEGROYRIGHT = 0b0000101

    MOVEIMAGEONE =      0b1010000
    MOVEIMAGETWO =      0b1100000
    MOVEIMAGETHREE =    0b1110000




class Client:

    BREAKTIME = 2
    URI = "tecs://localhost:9000/ps"  # URI of the TECS server
    SHAPE = (2000,6800,8000)  # (Numpy) shape for the input for the net
    PATH = ""  # Filepath and name to the keras model
    PATH_CNN = PATH + "cnn_model.h5" # PATH to the CNN
    NO_IMAGES = 12  # Number of images in the trials
    P = 0.8  # Probability of being right on an image in training
    EPOCHS = 42  # How long to train the net for

    def __init__(self, amt_trials):
        print(self.SHAPE)
        self.robot = Robot.Robot.eeg_side_quickstart(self.URI)
        self.eeg = EEG.EEG("recording.bin")
        self.net = Net.Net(self.SHAPE)
        self.labels = []
        self.amt_trials = amt_trials  # Amount of trials

        try:
            model_file = open(self.PATH_CNN)
            model_file.close()
            self.net.load(self.PATH_CNN)
        except IOError:
            self.net.createCNN()

    def train(self):
        for i in range(self.amt_trials):
            self.robot.publish("show", show(12))
            event = self.robot.wait_for_events()
            shown_event = event.parse(shown())
            time.sleep(self.BREAKTIME)

            image = random.randrange(self.NO_IMAGES)  # Get display image
            self.robot.publish("show", show(image))
            event = self.robot.wait_for_events()
            shown_event = event.parse(shown())
            if shown_event.shown < 0:
                raise Exception("Error")

            actual_image = random.choice(self.createDistribution(image, self.P))  # Get actually shown image
            self.robot.publish(moveArm(0 if actual_image < 6 else 1))
            self.eeg.toggle_recording()
            self.eeg.set_event(Events.MOVEARMLEFT if actual_image < 6 else Events.MOVEARMRIGHT, len(self.eeg.get_data()))#TODO index?
            event = self.robot.wait_for_events()
            moved_event = event.parse(moved())
            time.sleep(1)
            self.eeg.toggle_recording()
            if not moved_event.success:
                raise Exception("Error")
            if (image < 6 and actual_image >= 6) or (image >= 6 and actual_image < 6):
                self.labels.append("ErrP")
                self.eeg.__write_to_file()  # TODO Files and stuff
                self.robot.publish("reset", reset())
                event = self.robot.wait_for_events()
                moved_event = event.parse(moved())
                continue
            else:
                self.labels.append("noErrP")

            self.robot.publish(moveCategory(0 if actual_image < 3 else
                                            (1 if actual_image < 6 else
                                             (2 if actual_image < 9 else 3))))
            self.eeg.toggle_recording()
            self.eeg.set_event(Events.MOVECATEGROYLEFT if actual_image < 6 else Events.MOVECATEGROYRIGHT, len(self.eeg.get_data()))#TODO index?
            event = self.robot.wait_for_events()
            moved_event = event.parse(moved())
            time.sleep(1)
            self.eeg.toggle_recording()
            if not moved_event.success:
                raise Exception("Error")
            if (image % 6 < 3 and actual_image % 6 >= 3) or (image % 6 >= 3 and actual_image % 6 < 3):
                self.labels.append("ErrP")
                self.eeg.__write_to_file()  # TODO Files and stuff
                self.robot.publish("reset", reset())
                event = self.robot.wait_for_events()
                moved_event = event.parse(moved())
                continue
            else:
                self.labels.append("noErrP")

            self.robot.publish(moveImg(actual_image % 3))
            self.eeg.toggle_recording()
            self.eeg.set_event(
                Events.MOVEIMAGEONE if actual_image % 3 == 0 else
                (Events.MOVEIMAGETWO if actual_image % 3 == 1 else Events.MOVEIMAGETHREE),
                len(self.eeg.get_data()))
            event = self.robot.wait_for_events()
            moved_event = event.parse(moved())
            time.sleep(1)
            self.eeg.toggle_recording()
            if image != actual_image:
                self.labels.append("ErrP")
            else:
                self.labels.append("noErrP")
            if not moved_event.success:
                raise Exception("Error")
            # ELSE reset to original position and restart whole trial as success
            self.eeg.__write_to_file()  # TODO Files and stuff
            self.robot.publish("reset", 0)
            event = self.robot.wait_for_events()
            moved_event = event.parse(moved())

        with open(self.PATH + "LABELS_{}.json".format(time.time()), "w+") as f:
            json.dump(f, self.labels)

    def train_net(self, directory):
        files = os.listdir(directory)
        recordings = self.__load_recordings(directory)
        labels = json.load(directory + some_name)
        self.net.fit(len(self.labels), recordings, labels, self.EPOCHS)
        self.net.save(self.PATH_CNN)

    def __load_recordings(self, files):
        return [self.eeg.__load_recoding(file) for file in files]

    def createDistribution(self, selected, targetdistr):
        amt = 1
        distr = amt/self.NO_IMAGES
        output = range(12)
        output = self.balanceOutcomes(selected, output)
        while (distr <targetdistr):
            output.append(selected)
            amt = amt+1
            distr = amt / len(output)
        return output

    def balanceOutcomes(self, selected, input):
        if selected < 3:
            sel = list(range(3))
            sel.remove(selected)
            return input.append(random.choice(sel))
        elif selected < 6:
            sel = list(range(3,6))
            sel.remove(selected)
            return input.append(random.choice(sel))
        elif selected < 9:
            sel = list(range(6, 9))
            sel.remove(selected)
            return input.append(random.choice(sel))
        else:
            sel = list(range(9, 12))
            sel.remove(selected)
            return input.append(random.choice(sel))

    def run(self):
        pass


# "tecs://172.31.1.132:9000/ps"

"""
robot = Robot.Robot.robot_side_quickstart()
while True:
    print(robot.wait_for_events())
"""
robot = Robot.Robot.eeg_side_quickstart()
while True:
    input()
    robot.wait_for_events()


"""
from EEG import EEG
from EEG import SuperPrinter
from EEG import Filtering
import time
import numpy
eeg = EEG.EEG('test.bin')
eeg.toggle_recording()
eeg.set_event(2, 2)
time.sleep(10)
eeg.set_event(4, 1)
eeg.toggle_recording()
eeg.print_e()
data = eeg.get_data()
#data = numpy.random.rand(8,250)
print(Filtering.Filtering.check_quality(data, 250))

SuperPrinter.SuperPrinter.plot(data)
"""
#c = Client()
#c.train()
