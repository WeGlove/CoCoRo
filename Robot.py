import logging
import tecs
import tecs.ps
import tecs.basetypes
from yee.de.dfki.tecs.robot.baxter.ttypes import *

tecs.enable_console_logging(logging.INFO)


class Robot:

    def __init__(self, uri):
        self.client = tecs.ps.create(uri)
        self.subscriptions = []

    def subscribe(self, subscription):
        self.client.subscribe(subscription)
        self.subscriptions.append(subscription)

    def connect(self):
        self.client.connect()

    def disconnect(self):
        self.client.disconnect()

    def wait_for_events(self):
        while not self.client.can_recv(200):
            pass

        eve = self.client.recv()
        print("received " + str(eve))
        events = []
        for subscription in self.subscriptions:
            if subscription == eve.topic() == "moveArm":
                events.append(eve.parse(moveArm()))
            elif subscription == eve.topic() == "moveCategory":
                events.append(eve.parse(moveCategory()))
            elif subscription == eve.topic() == "moveImg":
                events.append(eve.parse(moveImg()))
            elif subscription == eve.topic() == "moved":
                events.append(eve.parse(moved()))
            elif subscription == eve.topic() == "reset":
                events.append(eve.parse(reset()))
            elif subscription == eve.topic() == "show":
                events.append(eve.parse(show()))
            elif subscription == eve.topic() == "shown":
                events.append(eve.parse(shown()))
        return events

    def answer_events(self, lastActed, success=True, Shown=-1):
        """
        This method sends answeres coressponding to certain events, AFTER the robot has finished exexuting said event
        :param lastActed: What Event has been last acted upon? This decides what response will be sent
        :param success: Did a move command succeed? - only needed for the response of a movement command
        :param Shown: What image was shown? - only needed for the response of a show command
        :return: None
        """
        if lastActed == "moveArm" or lastActed == "moveCategory" or lastActed == "moveImg" or lastActed == "reset":
            print("moving")
            self.client.publish(".*", "moved", moved(success))
        elif lastActed == "show":
            self.client.publish(".*", "shown", shown(Shown))
        else:
           raise("Invalid Event")

    def publish(self, command_text, command_attribute):
        self.client.publish(".*", command_text, command_attribute)

    @staticmethod
    def ps_tcp_example(uri="tecs://localhost:9000/ps"):
        rob = Robot(uri)
        rob.subscribe("moved")
        rob.subscribe("shown")
        rob.connect()

    @staticmethod
    def eeg_side_quickstart(uri="tecs://localhost:9000/ps"):
        robot = Robot(uri)
        robot.subscribe("moved")
        robot.subscribe("shown")
        robot.connect()
        return robot

    @staticmethod
    def robot_side_quickstart(uri="tecs://localhost:9000/ps"):
        robot = Robot(uri)
        robot.subscribe("moveArm")
        robot.subscribe("moveCategory")
        robot.subscribe("moveImg")
        robot.subscribe("show")
        robot.subscribe("reset")
        robot.connect()
        return robot


robot = Robot.eeg_side_quickstart()
print(robot.wait_for_events())

