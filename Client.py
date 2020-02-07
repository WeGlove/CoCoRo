#import Robot
import Net
import time
import random
from yee.de.dfki.tecs.robot.baxter.ttypes import *
import math

class Client:

    BREAKTIME = 2
    URI = "tecs://localhost:9000/ps"  # URI of the TECS server
    SHAPE = (2000,6800,8000)  # (Numpy) shape for the input for the net
    PATH = "cnn_model.h5"  # Filepath and name to the keras model
    NO_IMAGES = 12
    P = 0.8  # Probaility of being right on an image in training
    EPOCHS = 42 #How long to train the net for
    def __init__(self, amt_trials):
        print(self.SHAPE)
        self.robot = Robot.Robot.eeg_side_quickstart(self.URI)
        self.net = Net.Net(self.SHAPE)
        self.labels = []
        self.amt_trials = amt_trials

        try:
            model_file = open(self.PATH)
            model_file.close()
            self.net.load(self.PATH)
        except IOError:
            self.net.createCNN()

    def train(self):
        for i in range(self.amt_trials):
            image = random.randrange(self.NO_IMAGES)

            self.robot.publish("show", show(image))
            event = self.robot.wait_for_events()
            shown_event = event.parse(shown())
            if shown_event.shown < 0:
                raise Exception("Error")
            actual_image = random.choice(self.createDistribution(image, self.P))
            self.robot.publish(moveArm(0 if actual_image < 6 else 1))
            #  TODO Record data here
            #  TODO Set event here
            event = self.robot.wait_for_events()
            moved_event = event.parse(moved())
            if not moved_event.success:
                raise Exception("Error")
            if (image < 6 and actual_image >= 6) or (image >= 6 and actual_image < 6):
                self.labels.append("ErrP")
                self.robot.publish("reset", reset())
                continue
            else:
                self.labels.append("noErrP")
            self.robot.publish(moveCategory(0 if actual_image % 6 < 3 else 1))
            #  TODO Record data here
            #  TODO Set event here
            event = self.robot.wait_for_events()
            moved_event = event.parse(moved())
            if not moved_event.success:
                raise Exception("Error")
            if (image % 6 < 3 and actual_image % 6 >= 3) or (image % 6 >= 3 and actual_image % 6 < 3):
                self.labels.append("ErrP")
                self.robot.publish("reset", reset())
                continue
            else:
                self.labels.append("noErrP")
            self.robot.publish(moveImg(actual_image % 3))
            #  TODO Record data here
            #  TODO Set event here
            event = self.robot.wait_for_events()
            moved_event = event.parse(moved())
            if image != actual_image:
                self.labels.append("ErrP")
            else:
                self.labels.append("noErrP")
            if not moved_event.success:
                raise Exception("Error")
            #  TODO if "prediction" wrong restart no, we reset anyways
            # ELSE reset to original position and restart whole trial as success
            self.robot.publish("show", show(12))
            event = self.robot.wait_for_events()
            shown_event = event.parse(shown())
            self.robot.publish("reset", 0)
            event = self.robot.wait_for_events()
            moved_event = event.parse(moved())
            time.sleep(self.BREAKTIME)

            # if image == actual_image:
            #     result = "noErrp"
            #else:
            #   result="Errp"
            # add 3 labels for the 3 datasets
            # for i in range(3):
            #    self.labels.append(result)

        dummyRecordings = []
        #TODO: Replace "dummyRecordings" with actual recordings
        self.net.fit(len(self.labels), dummyRecordings, self.labels, self.EPOCHS)
        self.net.save(self.PATH)


    def createDistribution (self, selected, targetdistr):
        amt = 1
        distr = amt/self.NO_IMAGES
        output = range(12)
        output = self.balanceOutcomes(selected, output)
        while (distr <targetdistr):
            output.append(selected)
            amt = amt+1
            distr = amt / len(output)
        return output

    def balanceOutcomes (self , selected, input):
        if selected < 3:
            sel = range(3)
            sel = sel.remove(selected)
            return input.append(random.choice(sel))
        elif selected < 6:
            sel = range(3,6)
            sel = sel.remove(selected)
            return input.append(random.choice(sel))
        elif selected < 9:
            sel = range(6, 9)
            sel = sel.remove(selected)
            return input.append(random.choice(sel))
        else:
            sel = range(9, 12)
            sel = sel.remove(selected)
            return input.append(random.choice(sel))

    def run(self):
        pass


# "tecs://172.31.1.132:9000/ps"
"""
robot = Robot.Robot.robot_side_quickstart()
while True:
    print(robot.wait_for_events())
"""

"""
robot = Robot.Robot.robot_side_quickstart()
while True:
    robot.publish("moveArm", moveArm(1))
    print("sending something")
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

#c = Client()
#c.train()
