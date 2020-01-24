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

import errno
import socket
import struct
from socket import error

import tecs
from tecs.net.event import Event


class UDPEventSocket():
    MAX_DATAGRAM_SIZE = 65536

    def __init__(self, event_factory, port=0, reuse_addr=False):
        self.__log = tecs.get_logger(self)
        self.__event_factory = event_factory
        self.__port = port
        self.__reuseAddr = reuse_addr
        self.__bound = False
        self.__socket = None
        self.__remote_addr = ("localhost", port)
        self.__duplicate_filter = DuplicateEventFilter()

    def set_remote_endpoint(self, host, port):
        """
        :param host:
        :param port:
        :return: Outgoing events are sent to the given addr
        """
        self.__log.debug("set_remote_addr(%s,%d)", host, port)
        self.__remote_addr = (host, port)

    def port(self):
        return self.__port

    def join_multicast_group(self, mc_group):
        self.__log.info("join_multicast_group(%s)", mc_group)
        host = socket.gethostbyname(mc_group)
        group = socket.inet_aton(host)
        # group = socket.inet_aton("224.0.0.0")

        mreq = struct.pack("4sl", group, socket.INADDR_ANY)
        self.__socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def bound(self):
        return self.__bound

    def bind(self):
        self.__log.debug("bind()")
        if self.bound():
            self.__log.warn("Can't bind: Already bound.")
            return
        # self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        if self.__reuseAddr:
            self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # else:
        #     self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.__socket.bind(('0.0.0.0', self.__port))
        # TODO try catch for logging bind failure
        self.__bound = True
        self.__log.info("Bound to %s", self.__socket.getsockname())

    def close(self):
        self.__log.debug("close()")
        if not self.bound():
            self.__log.debug("Can't shutdown: Not bound.")
            return
        self.__socket.close()
        self.__bound = False
        self.__log.info("closed on port=%d", self.__port)

    def send(self, target, topic, tbase):
        self.__log.debug("send(%s, %s, <omitted>) to %s", target, topic, self.__remote_addr)
        """
        """
        try:
            header = self.__event_factory.create_header(target, topic)
            header_buf = tecs.util.serialize(header)
            header_size_buf = struct.pack("!i", len(header_buf))
            data_buf = tecs.util.serialize(tbase)
            out_buf = header_size_buf + header_buf + data_buf  # TODO creates a copy
            self.__socket.sendto(out_buf, self.__remote_addr)
        except error as e:
            self.__log.warn("Could not send message: cause=%s. ignored", e)

    def recv(self, timeout_ms=0):
        """
        :param timeout_ms: timeout until the method returns
        :return: an incoming event if available. otherwise None
        """
        self.__log.debug("recv(%d)", timeout_ms)
        recv_buf = None
        if not self.bound():
            self.__log.warn("Can't receive: Not bound")
            return None

        try:
            if timeout_ms == 0:
                self.__socket.settimeout(None)
            else:
                self.__socket.settimeout(timeout_ms / 1000.0)
            recv_buf = self.__socket.recvfrom(UDPEventSocket.MAX_DATAGRAM_SIZE)
        except socket.error as e:
            if not errno.EWOULDBLOCK:
                self.__log.debug("could not recv: no data available")
                return None

        if not recv_buf:
            return None

        try:
            event_buf = memoryview(recv_buf[0])
            remote = recv_buf[1]
            # unpack with !i parses an int_32 from network byte order
            header_size = struct.unpack('!i', event_buf[0:4])[0]
            header_buf = event_buf[4:header_size + 4]
            # Note: we have to take data_buf directly from the event_buf.
            # using a memoryview will fail putting the event into a pipe
            # TODO maybe create ByteBuffer class to avoid the copy
            data_buf = recv_buf[0][header_size + 4:]
            header = self.__event_factory.deserialize(tecs.basetypes.ttypes.EventHeader(), header_buf)
            event = Event(header, data_buf, remote)
            if self.__duplicate_filter.drop(event):
                self.__log.debug("dropped duplicate event: %s", event)
                return None

            return event
        except:
            self.__log.info("error while deserializing received event from %s. ignored", recv_buf[1])
            # TODO exceptions ValueError, struct.error
            return None

    def id(self):
        return self.__event_factory.id()

    def context(self):
        return self.__event_factory.context()


class DuplicateEventFilter:
    def __init__(self, backlog_size=50):
        if backlog_size < 0:
            raise ValueError("backlog_size of DuplicateFilter has to be > 0")
        self.__backlog = [None] * backlog_size
        self.__index = 0

    def drop(self, event):
        """
        :param event:
        :return: true iff the event was received earlier (last self.__backlog_size many events)
        """
        if len(self.__backlog) == 0:
            return False

        for entry in self.__backlog:
            if not entry:
                continue
            if event.uuid() == entry[0] and event.timestamp() == entry[1]:
                return True

        self.__backlog[self.__index] = (event.uuid(), event.timestamp())
        self.__index += 1
        self.__index %= len(self.__backlog)
        return False
