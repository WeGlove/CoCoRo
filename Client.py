import Robot
import Net
import time
import random
from yee.de.dfki.tecs.robot.baxter.ttypes import *
from EEG import EEG
from enum import Enum
import os
import json
import numpy
import Classifier
from keras.utils import to_categorical

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

    BREAKTIME = 1.5
    URI = "tecs://localhost:9000/ps"  # URI of the TECS server
    SHAPE = (2000,6800,8000)  # (Numpy) shape for the input for the net
    PATH = "Recordings\\"  # Filepath and name to the keras model
    PATH_CNN = PATH + "cnn_model.h5" # PATH to the CNN
    NO_IMAGES = 12  # Number of images in the trials
    P = 0.66  # Probability of being right on an image in training
    EPOCHS = 42  # How long to train the net for
    DURATION = 8 * 60

    def __init__(self, amt_trials):
        print(self.SHAPE)
        self.robot = Robot.Robot.eeg_side_quickstart(self.URI)
        self.eeg = EEG.EEG(self.PATH)
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
        begin = time.time()
        index = 0

        while time.time() - begin < self.DURATION:
            index += 1
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
            self.eeg.set_event(Events.MOVEARMLEFT if actual_image < 6 else Events.MOVEARMRIGHT)
            event = self.robot.wait_for_events()
            moved_event = event.parse(moved())
            time.sleep(1)  # To make sure the recording is long enough
            self.eeg.toggle_recording()
            if not moved_event.success:
                raise Exception("Error")
            self.eeg.write_to_file(str(index), str(index))
            self.eeg.clear()
            if (image < 6 and actual_image >= 6) or (image >= 6 and actual_image < 6):
                self.labels.append("ErrP")
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
            self.eeg.set_event(Events.MOVECATEGROYLEFT if actual_image < 6 else Events.MOVECATEGROYRIGHT)
            event = self.robot.wait_for_events()
            moved_event = event.parse(moved())
            time.sleep(1)
            self.eeg.toggle_recording()
            if not moved_event.success:
                raise Exception("Error")
            self.eeg.write_to_file(str(index), str(index))
            self.eeg.clear()
            if (image % 6 < 3 and actual_image % 6 >= 3) or (image % 6 >= 3 and actual_image % 6 < 3):
                self.labels.append("ErrP")
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
                (Events.MOVEIMAGETWO if actual_image % 3 == 1 else Events.MOVEIMAGETHREE))
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
            self.eeg.write_to_file(str(index), str(index))
            self.eeg.clear()
            self.robot.publish("reset", 0)
            event = self.robot.wait_for_events()
            moved_event = event.parse(moved())

        with open(self.PATH + "LABELS.json", "w+") as f:
            json.dump(f, self.labels)

    def run(self):
        classifier = Classifier.Classifier()
        begin = time.time()
        index = 0

        while time.time() - begin < self.DURATION:
            index += 1
            self.robot.publish("show", show(12))
            event = self.robot.wait_for_events()
            shown_event = event.parse(shown())
            while True:
                image_text = input("Enter the next image")
                words = ["bring", "give", "put", "conference_room", "entrance", "lab", "1", "2", "3", "Hammer", "Level", "Wrench"]
                try:
                    image = words.index(image_text)
                    break
                except Exception:
                    print("Entered unknown command. Try again")

            self.robot.publish("show", show(image))
            event = self.robot.wait_for_events()
            shown_event = event.parse(shown())
            if shown_event.shown < 0:
                raise Exception("Error")

            classification = classifier.classify(image)
            self.robot.publish("moveArm", moveArm(0 if classification < 6 else 1))
            self.eeg.toggle_recording()
            event = self.robot.wait_for_events()
            moved_event = event.parse(moved())
            time.sleep(1)  # To make sure the recording is long enough
            self.eeg.toggle_recording()
            if not moved_event.success:
                raise Exception("Error")
            prediction = self.net.predict(self.eeg.get_data())
            if prediction == 1:
                self.robot.publish("reset", reset())
                event = self.robot.wait_for_events()
                moved_event = event.parse(moved())
                continue
            else:
                self.eeg.clear()

            self.robot.publish(moveCategory(0 if classification < 3 else
                                            (1 if classification < 6 else
                                             (2 if classification < 9 else 3))))
            self.eeg.toggle_recording()
            event = self.robot.wait_for_events()
            moved_event = event.parse(moved())
            time.sleep(1)
            self.eeg.toggle_recording()
            if not moved_event.success:
                raise Exception("Error")
            if (image % 6 < 3 and classification % 6 >= 3) or (image % 6 >= 3 and classification % 6 < 3):
                self.robot.publish("reset", reset())
                event = self.robot.wait_for_events()
                moved_event = event.parse(moved())
                continue
            else:
                self.eeg.clear()

            self.robot.publish(moveImg(classification % 3))
            self.eeg.toggle_recording()
            event = self.robot.wait_for_events()
            moved_event = event.parse(moved())
            time.sleep(1)
            self.eeg.toggle_recording()
            if not moved_event.success:
                raise Exception("Error")
            # ELSE reset to original position and restart whole trial as success
            self.robot.publish("reset", 0)
            event = self.robot.wait_for_events()
            moved_event = event.parse(moved())

        with open(self.PATH + "LABELS.json", "w+") as f:
            json.dump(f, self.labels)

    def train_net(self):
        files = [file for file in os.listdir(self.PATH) if file.endswith(".npy")]
        recordings = self.__load_recordings(files)
        labels = json.load(self.PATH + "LABELS.json")
        labels = [0 if label == "ErrP" else 1 for label in labels]
        labels = to_categorical(labels)
        self.net.fit(recordings, labels, self.EPOCHS, batch_size=len(self.labels))  # TODO correct batch size
        self.net.save(self.PATH_CNN)

    def __load_recordings(self, files):
        return [numpy.load(self.PATH + file) for file in files]

    def createDistribution(self, selected, targetdistr):
        amt = 1
        distr = amt/self.NO_IMAGES
        output = list(range(12))
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
            input.append(random.choice(sel))
            return input
        elif selected < 6:
            sel = list(range(3,6))
            sel.remove(selected)
            input.append(random.choice(sel))
            return input
        elif selected < 9:
            sel = list(range(6, 9))
            sel.remove(selected)
            input.append(random.choice(sel))
            return input
        else:
            sel = list(range(9, 12))
            sel.remove(selected)
            input.append(random.choice(sel))
            return input



# "tecs://172.31.1.132:9000/ps"

"""
robot = Robot.Robot.robot_side_quickstart()
while True:
    print(robot.wait_for_events())
"""
"""
def cont_test(robot):
    time.sleep(1)
    while True:
        text = input("object:")
        before = time.time()
        if text == "arm":
            text = input("condition")
            before = time.time()
            robot.publish("moveArm", moveArm(int(text)))
            robot.wait_for_events()
        elif text == "cat":
            text = input("condition")
            before = time.time()
            robot.publish("moveCategory", moveCategory(int(text)))
            robot.wait_for_events()
        elif text == "img":
            text = input("condition")
            before = time.time()
            robot.publish("moveImg", moveImg(int(text)))
            robot.wait_for_events()
        elif text == "reset":
            before = time.time()
            robot.publish("reset", reset())
            robot.wait_for_events()
        elif text == "show":
            text = input("condition")
            before = time.time()
            robot.publish("show", show(int(text)))
            robot.wait_for_events()
        elif text == "quit":
            break
        print("Got out!")
        after = time.time()
        print("Command finished in {}s".format(after - before))

def automatic(robot):
    while True:
        if (input("quit?") == "yes"):
            break
        arm = int(input("arm"))
        cat = int(input("cat"))
        img = int(input("img"))
        input("Proceed with conditions arm={} cat={} img={}?".format(arm,cat,img))

        before = time.time()

        robot.publish("moveArm", moveArm(arm))
        robot.wait_for_events()
        robot.publish("moveCategory", moveCategory(cat))
        robot.wait_for_events()
        robot.publish("moveImg", moveImg(img))
        robot.wait_for_events()

        after = time.time()
        print("Command finished in {}s".format(after - before))

        robot.publish("reset", reset())
        robot.wait_for_events()


client = Client(10)
client.train()

robot = Robot.Robot.eeg_side_quickstart("tecs://192.168.1.132:9000/ps")

while True:
    text = input("Next Command")
    if text == "auto":
        automatic(robot)
    elif text == "pick":
        cont_test(robot)

"""




"""
from EEG import EEG
from EEG import SuperPrinter
from EEG import Filtering
import time
import numpy
eeg = EEG.EEG('')
printer = SuperPrinter.SuperPrinter()

eeg.toggle_recording()
time.sleep(10)
eeg.toggle_recording()
data = eeg.get_data()
printer.plot(data)
print(Filtering.Filtering.check_quality(data[:250],250))
#data = numpy.random.rand(8,250)
#print(Filtering.Filtering.check_quality(data, 250))
"""



