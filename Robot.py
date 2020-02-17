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
        while not self.client.connected():
            pass

    def disconnect(self):
        self.client.disconnect()

    def wait_for_events(self):
        while not self.client.can_recv():
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

    def answer_movement(self, success=True):
        self.client.publish(".*", "moved", moved(success))

    def answer_show(self, shownImg=-1):
        self.client.publish(".*", "shown", shown(shownImg))

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

