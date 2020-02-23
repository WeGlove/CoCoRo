#import Robot
import Net
import time
import random
#from yee.de.dfki.tecs.robot.baxter.ttypes import *
from EEG import EEG
from EEG import Filtering
from enum import Enum
import os
import json
import numpy
import Classifier
from keras.utils import to_categorical
from EEG import Plot

class Events(Enum):
    DEFAULT =           0b0000000

    ERRP =              0b10000000
    NOERRP =            0b10000001

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
    URI = "tecs://192.168.1.132:9000/ps"  # URI of the TECS server
    SHAPE = (2000,6800,8000)  # (Numpy) shape for the input for the net
    PATH = ".\Ressources\Recordings\\"  # Filepath and name to the keras model
    print(PATH)
    PATH_CNN = PATH + "cnn_model.h5" # PATH to the CNN
    NO_IMAGES = 12  # Number of images in the trials
    P = 0.66  # Probability of being right on an image in training
    EPOCHS = 1  # How long to train the net for
    DURATION = 8 * 60
    SFREQ = 250

    def __init__(self, amt_trials):
        print(self.SHAPE)
        #self.robot = Robot.Robot.eeg_side_quickstart(self.URI)
        self.eeg = EEG.EEG(self.PATH)
        self.net = Net.Net(self.SHAPE)
        self.labels = []
        self.datalist = []
        self.eventlist = []
        self.amt_trials = amt_trials  # Amount of trials
        #Plot.GUI_thread().run()


        #try:
        #    model_file = open(self.PATH_CNN)
        #    model_file.close()
        #    self.net.load(self.PATH_CNN)
        #except IOError:
        #    self.net.createCNN()

    def train(self):
        print("Started Training")

        index = 0
        for l in range(6):
            begin = time.time()
            print(f"Starting section{l}")
            while time.time() - begin < self.DURATION:
                print("Time left of", time.time() - begin, self.DURATION)
                index += 1
                print(f'Index: {index}')
                self.robot.publish("show", show(12))
                event = self.robot.wait_for_events()[0]
                print(f"got event {event}")
                if not isinstance(event, shown):
                    print("something is wrong!")
                time.sleep(self.BREAKTIME)
                print("Started trial")

                image = random.randrange(self.NO_IMAGES)  # Get display image
                self.robot.publish("show", show(image))
                shown_event = self.robot.wait_for_events()[0]
                if not isinstance(event, shown):
                    print("something is wrong!")
                if shown_event.image_shown < 0:
                    raise Exception("Error")

                time.sleep(1)

                actual_image = random.choice(self.createDistribution(image, self.P))  # Get actually shown image
                self.robot.publish("moveArm", moveArm(0 if actual_image < 6 else 1))
                self.eeg.toggle_recording()
                self.eeg.set_event(Events.MOVEARMLEFT.value if actual_image < 6 else Events.MOVEARMRIGHT.value)
                moved_event = self.robot.wait_for_events()[0]
                if not isinstance(event, moved):
                    print("something is wrong!")
                time.sleep(1)  # To make sure the recording is long enough
                self.eeg.toggle_recording()
                Plot.data = self.eeg.get_data().copy()
                print(Filtering.Filtering.check_quality(self.eeg.get_data().copy(), self.SFREQ))
                if not moved_event.success:
                    raise Exception("Error")
                if (image < 6 and actual_image >= 6) or (image >= 6 and actual_image < 6):
                    self.eeg.set_event(Events.ERRP.value)
                else:
                    self.eeg.set_event(Events.NOERRP.value)
                self.eeg.write_to_file(str(index*10+1), str(index*10+1))
                self.eeg.clear()
                if (image < 6 and actual_image >= 6) or (image >= 6 and actual_image < 6):
                    self.labels.append("ErrP")
                    self.robot.publish("reset", reset())
                    event = self.robot.wait_for_events()[0]
                    if not isinstance(event, moved):
                        print("something is wrong!")
                    continue
                else:
                    self.labels.append("noErrP")


                self.robot.publish("moveCategory", moveCategory(0 if actual_image < 3 else
                                                (1 if actual_image < 6 else
                                                 (2 if actual_image < 9 else 3))))
                self.eeg.toggle_recording()
                self.eeg.set_event(Events.MOVECATEGROYLEFT.value if actual_image < 6 else Events.MOVECATEGROYRIGHT.value)
                moved_event = self.robot.wait_for_events()[0]
                if not isinstance(event, shown):
                    print("something is wrong!")
                time.sleep(1)
                self.eeg.toggle_recording()
                Plot.data = self.eeg.get_data().copy()
                print(Filtering.Filtering.check_quality(self.eeg.get_data().copy(), self.SFREQ))
                if not moved_event.success:
                    raise Exception("Error")
                if (image % 6 < 3 and actual_image % 6 >= 3) or (image % 6 >= 3 and actual_image % 6 < 3):
                    self.eeg.set_event(Events.ERRP.value)
                else:
                    self.eeg.set_event(Events.NOERRP.value)
                self.eeg.write_to_file(str(index*10+2), str(index*10+2))
                self.eeg.clear()
                if (image % 6 < 3 and actual_image % 6 >= 3) or (image % 6 >= 3 and actual_image % 6 < 3):
                    self.labels.append("ErrP")
                    self.robot.publish("reset", reset())
                    moved_event = self.robot.wait_for_events()[0]
                    if not isinstance(event, moved):
                        print("something is wrong!")
                    continue
                else:
                    self.labels.append("noErrP")

                self.robot.publish("moveImg", moveImg(actual_image))
                self.eeg.toggle_recording()
                self.eeg.set_event(
                    Events.MOVEIMAGEONE.value if actual_image % 3 == 0 else
                    (Events.MOVEIMAGETWO.value if actual_image % 3 == 1 else Events.MOVEIMAGETHREE.value))
                moved_event = self.robot.wait_for_events()[0]
                if not isinstance(event, moved):
                    print("something is wrong!")
                time.sleep(1)
                self.eeg.toggle_recording()
                Plot.data = self.eeg.get_data().copy()
                print(Filtering.Filtering.check_quality(self.eeg.get_data().copy(), self.SFREQ))
                if image != actual_image:
                    self.labels.append("ErrP")
                    self.eeg.set_event(Events.ERRP.value)
                else:
                    self.labels.append("noErrP")
                    self.eeg.set_event(Events.NOERRP.value)
                if not moved_event.success:
                    raise Exception("Error")
                # ELSE reset to original position and restart whole trial as success
                self.eeg.write_to_file(str(index*10+3), str(index*10+3))
                self.eeg.clear()
                self.robot.publish("reset", reset())
                moved_event = self.robot.wait_for_events()[0]
                if not isinstance(event, shown):
                    print("something is wrong!")

            print("Commence waiting for 2 minutes")
            time.sleep(60)
            print("Waited 1:00")
            time.sleep(30)
            print("Waited 1:30")
            time.sleep(30)
            print("Continuing")

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
            if shown_event.image_shown < 0:
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

            self.robot.publish("moveCategory", moveCategory(0 if classification < 3 else
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

            self.robot.publish("moveImg", moveImg(classification % 3))
            self.eeg.toggle_recording()
            event = self.robot.wait_for_events()
            moved_event = event.parse(moved())
            time.sleep(1)
            self.eeg.toggle_recording()
            if not moved_event.success:
                raise Exception("Error")
            # ELSE reset to original position and restart whole trial as success
            self.robot.publish("reset", reset())
            event = self.robot.wait_for_events()
            moved_event = event.parse(moved())

        with open(self.PATH + "LABELS.json", "w+") as f:
            json.dump(f, self.labels)

    def train_net(self):
        #files = [file for file in os.listdir(self.PATH) if file.endswith(".npy")]
        self.net.createCNN()
        recordings = self.datalist
        #labels = json.load(self.PATH + "LABELS.json")
        labels = self.eventlist
        labels = [0 if label == "ErrP" else 1 for label in labels]
        labels = to_categorical(labels)
        self.net.fit(recordings[0], labels[0], self.EPOCHS, batch_size=1)
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

    def readFiles (self):
        #129 == noErrP
        #npy stores data
        #json stores events
        outputData = []
        outputEvents = []
        errorlist = []
        errorfilelist = []
        errorCount = 0
        total = 0
        for i in range(6):
            addendum = "Recordings"+str(i)+"\\"
            curdir = os.listdir(".\Ressources\Recordings\\"+addendum)
            lendir = len(curdir)
            j = 0
            while (j < lendir):
                total += 1
                eventpath = curdir[j]
                j += 1
                datapath = curdir[j]
                j += 1
                self.eeg.read_from_file(addendum + datapath, addendum + eventpath)
                allEvents = self.eeg.get_events()
                try:
                    if (allEvents[1][1] == 128):
                        outputEvents.append("ErrP")
                    else:
                        outputEvents.append("noErrP")
                except:
                    errorCount += 1
                    errorlist.append(allEvents)
                    errorfilelist.append(eventpath)
                    continue
                outputData.append(self.eeg.get_data())
        self.datalist = outputData
        self.eventlist = outputEvents

        print("Errors: " + str(errorCount) + "with total of: " + str(total) + "with Events" + str(errorlist)+ ", " + str(errorfilelist))





        data = self.eeg.get_data()
        events = self.eeg.get_events()
        #print("Data: ", data)
        #print ("Events: ", events)

client = Client(0)
client.readFiles()
client.train_net()

#client.train()
#print("Done Recording")
#input()


"""
gui = Plot.GUI_thread()
gui.run()
while True:
    Plot.data = numpy.random.rand(8, 1250)
    Plot.confidence = 0.3

print("Hey")
input()
client = Client(0)
client.train()
"""
# "tecs://172.31.1.132:9000/ps"

"""
robot = Robot.Robot.robot_side_quickstart()
while True:
    print(robot.wait_for_events())
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

"""
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



