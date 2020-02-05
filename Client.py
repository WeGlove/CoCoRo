import Robot
import Net
import random
from yee.de.dfki.tecs.robot.baxter.ttypes import *
import math

class Client:

    URI = "tecs://localhost:9000/ps"  # URI of the TECS server
    SHAPE = (2000,6800,8000)  # (Numpy) shape for the input for the net
    PATH = "cnn_model.h5"  # Filepath and name to the keras model
    NO_IMAGES = 12
    P = 0.8  # Probaility of being right on an image in training

    def __init__(self):
        print(self.SHAPE)
        self.robot = Robot.Robot.eeg_side_quickstart(self.URI)
        self.net = Net.Net(self.SHAPE)
        self.labels  = []

        try:
            model_file = open(self.PATH)
            model_file.close()
            self.net.load(self.PATH)
        except IOError:
            self.net.createCNN()

    def train(self):
        image = random.randrange(self.NO_IMAGES)

        self.robot.publish("show", show())
        event = self.robot.wait_for_events()
        shown_event = event.parse(shown())
        if shown_event.shown < 0:
            raise Exception("Error")
        correct_image = random.random() <= self.P
        actual_image = 0
        self.robot.publish(moveArm(0 if actual_image < 6 else 1))
        #  TODO Record data here
        #  TODO Set event here
        event = self.robot.wait_for_events()
        moved_event = event.parse(moved())
        if not moved_event.success:
            raise Exception("Error")
        #  TODO if "prediction" wrong restart
        self.robot.publish(moveCategory(0 if actual_image % 6 < 3 else 1))
        #  TODO Record data here
        #  TODO Set event here
        event = self.robot.wait_for_events()
        moved_event = event.parse(moved())
        if not moved_event.success:
            raise Exception("Error")
        #  TODO if "prediction" wrong restart
        self.robot.publish(moveImg(actual_image % 3))
        #  TODO Record data here
        #  TODO Set event here
        event = self.robot.wait_for_events()
        moved_event = event.parse(moved())
        if not moved_event.success:
            raise Exception("Error")
        #  TODO if "prediction" wrong restart
        # ELSE reset to original position and restart whole trial as success
        self.robot.publish("reset", 0)
        if image == actual_image:
            result = "noErrp"
        else:
            result="Errp"
        # add 3 labels for the 3 datasets
        for i in range(3):
            self.labels.append(result)


    def run(self):
        pass


# "tecs://172.31.1.132:9000/ps"
"""
robot = Robot.Robot.robot_side_quickstart()
while True:
    print(robot.wait_for_events())
"""


robot = Robot.Robot.robot_side_quickstart()
while True:
    robot.publish("moveArm", moveArm(1))
    print("sending something")


#c = Client()
#c.train()
