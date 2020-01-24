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
import threading
from multiprocessing import Pipe

from tecs import get_logger


class PSClient(object):
    class State:
        OFFLINE = 0
        ONLINE = 1
        STOPPED = 2

    def __init__(self, id):
        self.__log = get_logger(self)
        self._id = id
        self.__in_recv_pipe, self.__out_recv_pipe = Pipe()
        self.__in_send_pipe, self.__out_send_pipe = Pipe()
        self._subscriptions = set()
        # self.__event_factory = EventFactory(self.id)
        self._socket = None
        self.__state = self.State.OFFLINE
        self._lock = threading.Lock()

    def connect(self):
        """
        Starts the client. It will continously try to connect to a remote endpoint and exchange events until
        disconnect() is called. You can't call connect() again after calling disconnect()
        """
        self.__log.debug("connect()")
        self._lock.acquire()
        if self.__state != self.State.OFFLINE:
            self._lock.release()
            raise ValueError("can't connect: not offline")

        self.__state = self.State.ONLINE
        rthread = threading.Thread(target=self.__recv_loop)
        rthread.setDaemon(True)
        rthread.start()
        sthread = threading.Thread(target=self.__send_loop)
        sthread.setDaemon(True)
        sthread.start()
        self._lock.release()

    def disconnect(self):
        """
        Disconnects the client and stops the recv/send thread in the background. Nothing happens if the client is
        not online.
        """
        self.__log.debug("disconnect()")
        self._lock.acquire()
        if self.__state != self.State.ONLINE:
            self._lock.release()
            return

        self.__state = self.State.STOPPED
        if self._socket is not None:
            self._socket.close()
        self.__in_send_pipe.send(None)
        self._lock.release()

    def online(self):
        """
        :return: true iff connect() was called and disconnect() not yet.
        """
        self.__log.debug("online()")
        self._lock.acquire()
        online = self.__state == self.State.ONLINE
        self._lock.release()
        return online

    def connected(self):
        """
        :return: true iff the client is currently connected to a remote endpoint
        """
        self.__log.debug("connected()")
        self._lock.acquire()
        connected = self._socket is not None
        self._lock.release()
        return connected

    def publish(self, target, topic, data):
        """
        Publishes data to target using the topic. The method blocks until the
        data is transmitted. If the connection is lost. It will block until the
        connection is reestablished. If the timeout is reached it will drop the event
        silently and return.
        :param target: target regular expression limiting the receiving client ids.
        :param topic: topic of the data
        :param data: the payload of the event
        :return:
        """
        self.__log.debug("publish(%s, %s, <omitted>)", target, topic)
        self.__in_send_pipe.send((target, topic, data))

    def subscribe(self, topic):
        """
        Subscribes a new topic. Has to be done before connecting.
        :param topic:
        :return:
        """
        self.__log.debug("subscribe(%s)", topic)
        self._lock.acquire()
        if self.__state != self.State.OFFLINE:
            self._lock.release()
            raise ValueError("can only subscribe while offline. state is " + str(self.__state))

        if topic == "*":
            self._subscriptions.clear()
            self._subscriptions.add("*")
        elif "*" not in self._subscriptions:
            self._subscriptions.add(topic)

        self._lock.release()

    def subscribe_all(self):
        """
        Subscribes to all events. The server will forward all events to this client.
        :return:
        """
        self.__log.debug("subscribe_all()")
        self.subscribe("*")

    def can_recv(self, timeout_ms=0):
        """
        Checks if events are queued for receiving. If this method returns true, recv() will be non-blocking for the
        call.
        :param timeout_ms: if provided, waits up to the given amount of time for events. in milliseconds.
        :return:
        """
        self.__log.debug("can_recv(%d)", timeout_ms)
        events_available = self.__out_recv_pipe.poll(timeout_ms / 1000.0)
        return events_available

    def recv(self):
        """
        Blocks until a new event is available. Use it in combination with can_recv() for non_blocking behavior.
        :return: The next received event or None if disconnect() was called
        """
        self.__log.debug("recv()")
        return self.__out_recv_pipe.recv()

    def __recv_loop(self):
        """
        handles reconnecting and receiving of events
        """
        self.__log.debug("__recv_loop()")
        self.__service_selector_gen = None
        while True:
            # check if client should stop
            self._lock.acquire()
            if self.__state == self.State.STOPPED:
                if self._socket is not None:
                    self._socket.close()
                    self._socket = None
                self._lock.release()
                # release blocking recv() call
                self.__in_recv_pipe.send(None)
                self.__log.debug("quitting recv thread")
                return
            sock = self._socket
            self._lock.release()

            # create a new socket if none is available
            if not sock:
                new_socket = self._connect_socket()
                self._lock.acquire()
                self._socket = new_socket
                self._lock.release()
                continue

            try:
                event = sock.recv()
                if not event:
                    continue
                if self._filter_in_event(event):
                    self.__log.debug("filtered received event %s", event)
                    continue
                self.__log.debug("received event %s", event)
                self.__in_recv_pipe.send(event)
            except IOError as ioe:
                self.__log.info("io error during recv. disconnecting: %s", ioe)
                self._lock.acquire()
                self._socket.close()
                self._socket = None
                self._lock.release()

    def __send_loop(self):
        """
        handles sending of events
        """
        self.__log.debug("__send_loop()")
        sock = None
        while True:
            # check if there is a valid socket
            if sock is None:
                self._lock.acquire()
                # if self.state == self.State.STOPPED:
                #     print "quiting send thread"
                #     return
                sock = self._socket
                self._lock.release()

            if not self.__out_send_pipe.poll(1):
                continue
            msg = self.__out_send_pipe.recv()
            if not msg:
                self.__log.debug("quiting send thread")
                return
            (target, topic, tbase) = msg

            if not sock:
                # not connected
                continue

            try:
                sock.send(target, topic, tbase)
            except IOError as ioe:
                self.__log.info("could not send event: %s", ioe)
                sock = None

    def _connect_socket(self):
        # abstract method
        self.__log.debug("_connect_socket()")
        raise NotImplementedError("can't run _connect_socket() on abstract PSClient")

    def _filter_in_event(self, event):
        """
        :param event:
        :return: true iff the given event should be filtered
        """
        return False
