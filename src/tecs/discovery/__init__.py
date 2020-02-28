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
import re
import threading
import uuid

import uritools

import tecs
from tecs.basetypes import constants
from tecs.basetypes.ttypes import DiscoverEvent, AdvertiseEvent, ServiceDescriptor, Version
from tecs.net.event import EventFactory
from tecs.net.udp import UDPEventSocket
import tecs.util


class MulticastServiceSelector:
    def __init__(self, type_regex, id="py-discovery", context="", mc_group=constants.MULTICAST_IPV4,
                 mc_port=constants.DEFAULT_PORT):
        self.__log = tecs.get_logger(self)
        self.__type_regex = type_regex
        self.__id = id
        self.__context = context
        self.__mc_group = mc_group
        self.__mc_port = mc_port
        self.__lock = threading.Lock()
        self.__socket = None

    def select(self):
        self.__log.debug("select()")
        self.__socket = UDPEventSocket(EventFactory(self.__id), self.__mc_port, True)
        self.__socket.bind()
        self.__socket.join_multicast_group(self.__mc_group)
        self.__socket.set_remote_endpoint(self.__mc_group, self.__mc_port)
        ih = tecs.util.IntervalHelper(2000)
        de = DiscoverEvent(self.__type_regex)
        de.context = self.__context
        while self.__socket:
            if ih.should_execute():
                self.__log.info("sending discovery request %s", de)
                self.__socket.send(".*", "DiscoverEvent", de)

            eve = self.__socket.recv(500)
            if eve is None:
                yield None
                continue

            if not eve.topic_is("AdvertiseEvent"):
                yield None
                continue

            try:
                ae = eve.parse_data(AdvertiseEvent())
            except ValueError as ve:
                self.__log.warn(
                    "could not deserialize event from %s:%s: %s ignored".format(eve.remote_host(), eve.remote_port(),
                                                                                ve.message))
                yield None
                continue

            # replacing localhost with remote ip
            for sd in ae.services:
                sd.uri = sd.uri.replace("0.0.0.0", eve.remote_host())

            self.__log.info("discovered %s from %s:%d", str(ae), eve.remote_host(), eve.remote_port())

            for sd in ae.services:
                if not re.match(self.__type_regex, sd.type):
                    self.__log.debug("filtered %s because of type mismatch (regex=%s)", sd, self.__type_regex)
                    yield None

                if self.__context and self.__context != sd.context:
                    self.__log.debug("filtered %s because of context '%s'", sd, self.__context)
                    yield None
                else:
                    yield sd

    def stop(self):
        self.__log.debug("stop()")
        if not self.__socket:
            return
        self.__socket.close()
        self.__socket = None


class ServiceDescriptorBuilder:
    def __init__(self, type, uri):
        self.__sd = ServiceDescriptor(None, type, None, uri)

    def random_uuid(self):
        return str(uuid.uuid4())

    def build(self):
        self.__sd.uuid = self.random_uuid()
        bin_sd = tecs.util.serialize(self.__sd)
        sd = tecs.util.deserialize(ServiceDescriptor(), bin_sd)
        return sd

    def add_arg(self, key, value):
        if self.__sd.arguments is None:
            self.__sd.arguments = {}

        self.__sd.arguments[key] = value
        return self

    def set_version(self, major, minor, patch):
        self.__sd.version = Version(major, minor, patch)
        return self

    def set_context(self, context):
        self.__sd.context = context
        return self


class ServiceProvider:
    def __init__(self, id="py-service-provider", mc_group=constants.MULTICAST_IPV4, mc_port=constants.DEFAULT_PORT):
        self.__socket = UDPEventSocket(EventFactory(id), mc_port, True)
        self.__mc_group = mc_group
        self.__mc_port = mc_port
        self.__log = tecs.get_logger(self)
        self.__services = []
        self.__lock = threading.Lock()
        self.__active = False
        self.__thread = None

    def add_service_descriptor(self, sd):
        sd_copy = self.__copy_sd(sd)
        self.__log.info("added %s", sd)
        self.__lock.acquire()
        self.__services.append(sd_copy)
        self.__lock.release()

    def remove_service_descriptor(self, sd_id):
        """
        :param sd_id: uuid of the service descriptor
        :return:
        """
        self.__lock.acquire()
        for sd in self.__services:
            if sd.uuid == sd_id:
                self.__services.remove(sd)
        self.__lock.release()

    def start(self):
        self.__lock.acquire()
        if self.__thread:
            self.__lock.release()
            raise RuntimeError("ServiceProvider can only be started once")
        self.__log.info("starting service_provider")
        self.__active = True
        self.__thread = threading.Thread(target=self.__run)
        self.__thread.setDaemon(True)
        self.__thread.start()
        self.__lock.release()

    def stop(self):
        self.__lock.acquire()
        self.__active = False
        self.__lock.release()

    def __run(self):
        self.__log.debug("__run()")
        self.__socket.bind()
        self.__socket.join_multicast_group(self.__mc_group)

        while True:
            self.__lock.acquire()
            if not self.__active:
                self.__lock.release()
                break
            self.__lock.release()

            eve = self.__socket.recv(1000)
            if eve is None:
                continue

            if not eve.topic_is("DiscoverEvent"):
                continue

            try:
                de = eve.parse_data(DiscoverEvent())
            except ValueError as ve:
                self.__log.debug("could not deserialize DiscoverEvent: %s", ve.message)
                continue
            self._on_request(de, (eve.remote_host(), eve.remote_port()))

        self.__socket.close()
        self.__log.debug("__run() exit")

    def _on_request(self, discover_event, remote_endpoint):
        self.__log.debug("received %s", discover_event)
        self.__lock.acquire()
        for sd in self.__services:
            # if on None and empty string returns False
            # => we only responsd if the remote does not specify a context or the context matches
            if discover_event.context and discover_event.context != sd.context:
                self.__log.debug("don't respond %s because of context mismatch: %s", sd, discover_event.context)
                continue

            if not re.match(discover_event.typeRegex, sd.type):
                continue

            ae = AdvertiseEvent([sd])
            self.__log.debug("answering discover request from %s:%d with {}", remote_endpoint[0], remote_endpoint[1],
                             sd)
            # TODO would be better, but does not work atm
            # self.__socket.set_remote_endpoint(remote_endpoint[0], remote_endpoint[1])
            self.__socket.set_remote_endpoint(self.__mc_group, self.__mc_port)
            self.__socket.send(".*", "AdvertiseEvent", ae)
        self.__lock.release()

    def __copy_sd(self, sd):
        bin = tecs.util.serialize(sd)
        return tecs.util.deserialize(ServiceDescriptor(), bin)
