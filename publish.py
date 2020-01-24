
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
 
    client.connect()

    ih = tecs.util.IntervalHelper(1000)

    while client.online():
        if ih.should_execute():
            # using IntervalHelper to sent the events approx every second
            print("online={} connected={}".format(client.online(), client.connected()))
            client.publish(".*","moveArm",moveArm(1))
            client.publish(".*","moveCategory",moveCategory(2))
            client.publish(".*","moveImg",moveImg(3))
            client.publish(".*","reset",reset())
            client.publish(".*","show",show(4))
            client.publish(".*","shown",shown(5))
            client.publish(".*","moved",moved(True))
        

def ps_tcp_example(uri="tecs://localhost:9000/ps"):
    ps_example(uri)



if __name__ == "__main__":
    ps_tcp_example()
