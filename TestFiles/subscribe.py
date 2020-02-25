
import logging
import tecs
import tecs.ps
import tecs.basetypes
from yee.de.dfki.tecs.robot.baxter.ttypes import *
tecs.enable_console_logging(logging.INFO)


def ps_example(uri):
    """
    publish-subscribe over tcp
    :param uri:
    :return:
    """

    client = tecs.ps.create(uri)
    # client.subscribe_all()
    client.subscribe("moveArm")
    client.subscribe("moveCategory")
    client.subscribe("moveImg")
    client.connect()

    ih = tecs.util.IntervalHelper(1000)

    while client.online():
       
        if client.can_recv(200):
            eve = client.recv()
            print("received " + str(eve))
            se = eve.parse(moveArm())
            ce = eve.parse(moveCategory())
            print(se)
            print(ce)
            # client.disconnect()


def ps_tcp_example(uri="tecs://localhost:9000/ps"):
    ps_example(uri)



if __name__ == "__main__":
    ps_tcp_example()
   