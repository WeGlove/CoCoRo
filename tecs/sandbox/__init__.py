#
# The Creative Commons CC-BY-NC 4.0 License
#
# http://creativecommons.org/licenses/by-nc/4.0/legalcode
#
# Creative Commons (CC) by DFKI GmbH
#  - Christian Buerckert <Christian.Buerckert@DFKI.de>
#  - Yannick Koerber <Yannick.Koerber@DFKI.de>
#  - Magdalena Kaiser <Magdalena.Kaiser@DFKI.de>
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#

# activate console logging, need to import tecs, logging
import logging
import tecs
tecs.enable_console_logging(logging.INFO)


def ps_example(uri):
    """
    publish-subscribe over tcp
    :param uri:
    :return:
    """
    import tecs.ps
    import tecs.basetypes
    client = tecs.ps.create(uri)
    # client.subscribe_all()
    client.subscribe("SheepEvent")
    client.connect()

    ih = tecs.util.IntervalHelper(1000)

    while client.online():
        if ih.should_execute():
            # using IntervalHelper to sent the events approx every second
            print("online={} connected={}".format(client.online(), client.connected()))
            client.publish(".*", "SheepEvent", tecs.basetypes.ttypes.SheepEvent("hello"))
            client.publish(".*", "BinaryEvent", tecs.basetypes.ttypes.BinaryEvent(bytearray(1024)))
        if client.can_recv(200):
            eve = client.recv()
            print("received " + str(eve))
            # client.disconnect()


def ps_tcp_example(uri="tecs://py@localhost:9000/ps"):
    ps_example(uri)


def ps_discover_example(uri="tecs-dis://py@224.0.0.1:9000"):
    """
    publish-subscribe example over tcp, which uses udp multicast to discover the host and port of a tecs-server
    Append the context as if you want to discover a tecs-server within a specific context.
    e.g. tecs-dis://py@224.0.0.1:9000/YOUR_CONTEXT
    :param uri:
    :return:
    """
    ps_example(uri)


def ps_udp_example(uri="tecs-udp://py@224.0.0.1:11000"):
    ps_example(uri)


def ps_socket_example(uri="tecs://py@localhost:9000/ps"):
    """
    publish-subscribe can also be used with a simple event socket.
    in contrast to the PSClient you have to handle reconnect manually and
    connect, send, recv are blocking
    :return:
    """
    import tecs.net
    from tecs.basetypes.ttypes import SheepEvent, SubscribeEvent
    socket = tecs.net.tcp.TCPEventSocket.connect(uri)
    se = SheepEvent("hello")
    # you have to handle the connection state and the subscriptions yourself:
    socket.send(".*", "SubscribeEvent", SubscribeEvent("SheepEvent"))
    for i in range(0, 3):
        socket.send(".*", "SheepEvent", se)
        in_eve = socket.recv()
        print("received " + str(in_eve))
        tecs.util.sleep(1000)
    socket.close()


def mp_client_example(uri="tecs://py@localhost:15000/sheep"):
    # the code is similar for the ps socket example with the exception that the SubscribeEvent can be omitted
    try:
        ps_socket_example(uri)
    except IOError as ioe:
        print("io error: " + str(ioe))


def mp_service_example(port=15000):
    import tecs.mp
    import tecs.basetypes.ttypes
    import threading
    from tecs.net.http_server import HttpServer

    def socket_behavior(event_socket):
        """
        Called after a succesful socket upgrade.
        :param event_socket: The socket for the remote connection
        :return:
        """
        while True:
            event = event_socket.recv()
            print ("received " + str(event))
            if event.topic_is("SheepEvent"):
                se = event.parse(tecs.basetypes.ttypes.SheepEvent())
                event_socket.send(".*", "SheepEvent", se)

    class MyHandler(tecs.mp.MPHandler):
        def __init__(self):
            tecs.mp.MPHandler.__init__(self, "/sheep")

        def _on_socket(self, event_socket):
            t = threading.Thread(target=socket_behavior, args=[event_socket])
            t.setDaemon(True)
            t.start()

    http_server = HttpServer(port)
    http_server.add_handler(MyHandler())
    http_server.bind()
    while True:
        http_server.accept()
    raw_input("\n===================== press enter to quit =====================\n")


def mp_udp_example(id="py", port=0):
    """
    message-passing over UDP
    :param id:
    :param port:
    :param context:
    :return:
    """
    import tecs.net
    from tecs.basetypes.ttypes import SheepEvent
    s = tecs.net.udp.UDPEventSocket(tecs.net.event.EventFactory("py"), port=port)
    s.bind()
    while True:
        se = SheepEvent("hello")
        s.set_remote_endpoint("127.0.0.1", 15000)
        s.send(".*", "SheepEvent", se)
        datagram = s.recv(1000)
        if datagram:
            print("received " + str(datagram))
        tecs.util.sleep(1000)
    s.close()


def discover_example(filter=None, context=""):
    import tecs.discovery
    dis = tecs.discovery.MulticastServiceSelector(".*", "py-discovery-sandbox", context)
    for sd in dis.select():
        print("discovered: " + str(sd))
        # the discover frequently yields None such that you can interrupt the discovery here
        if filter and filter(sd):  # <- replace with external condition to stop discovery
            dis.stop()
            return sd

        if not sd:
            print(".")
            continue

    # sd = discover(constants.SERVICE_TYPE_TECS_SERVER, tecs.ps.tecs_server_filter, "looooooad", "tecs")
    # uri = urisplit(sd.uri)
    # uri = "http://py@" + uri.host + ":" + uri.port + uri.path
    # print(uri)
    # example_tcp_event_socket(uri)


def advertise_example(type="example-service-py", uri="http://localhost:8000", context=""):
    import tecs.discovery
    sd = tecs.discovery.ServiceDescriptorBuilder(type, uri) \
        .set_version(1, 2, 3).add_arg("arg1", "value1").set_context(context).build()

    service_provider = tecs.discovery.ServiceProvider("py-example-advertise")
    service_provider.add_service_descriptor(sd)
    service_provider.start()

    import sys
    if sys.version_info.major == 3:
        input("press enter to quit")
    elif sys.version_info.major == 2:
        raw_input("press enter to quit")
    service_provider.stop()
    tecs.util.sleep(1000)


def rpc_client_example(host="0.0.0.0", port=15000):
    import tecs.rpc
    import tecs.basetypes.SheepService
    # create client with fixed host and port
    client = tecs.rpc.RPCClientFactory.create_client(tecs.basetypes.SheepService.Client, host, port)

    def my_consumer(client):
        client.sheep("wool1 from py")
        client.sheep("wool2 from py")
        return "OK"  # in general this should return a value from the rpc call

    result = client.call(my_consumer)
    print(result)
    # check for success / failure
    if result.success():
        pass
    if result.failed():
        pass
    # get the return value
    print("result value is " + str(result.value()))


import tecs.basetypes.SheepService
class SheepHandler(tecs.basetypes.SheepService.Iface):
    def sheep(self, wool):
        print(wool)


def rpc_service_example(port=15000, discovery=True):
    import tecs.rpc
    import tecs.basetypes.SheepService
    handler = SheepHandler()
    proc = tecs.basetypes.SheepService.Processor(handler)
    service = tecs.rpc.RPCService.create(proc).set_type("sheep-service").set_port(port).build()
    sd = service.service_descriptor()
    print(sd)
    if discovery:
        import tecs.discovery
        service_provider = tecs.discovery.ServiceProvider("py-rpc_service_example")
        service_provider.add_service_descriptor(sd)
        service_provider.start()

    raw_input("press enter to quit\n")
    service.close()
    if service_provider:
        service_provider.stop()


if __name__ == "__main__":
    # ps_tcp_example()
    ps_discover_example()
    # ps_udp_example()
    # ps_socket_example()

    # mp_client_example()
    # mp_service_example()


    # rpc_client_example()
    # rpc_service_example()

    # discover_example()
    # advertise_example()
