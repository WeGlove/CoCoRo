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

from tecs.net.event import EventFactory, Event
from tecs.net.http import *
import uritools
from tecs.basetypes import constants
import socket
import struct

from tecs.util import current_millis
import tecs


class TCPEventSocket:
    def __init__(self, id, socket):
        self.__log = tecs.get_logger(self)
        self.__socket = socket
        self.__sos = SocketOutputStream(self.__socket);
        self.__sis = SocketInputStream(self.__socket);
        self.__event_factory = EventFactory(id)

    @staticmethod
    def connect(uri_str, additional_headers=None):
        """
        :param uri_str:
        :param additional_headers: list of HttpHeader
        :raise IOError on failure
        :return:
        """
        uri = uritools.urisplit(uri_str)
        if not uri.userinfo:
            raise ValueError("TCPEventSocket::connect requires 'userinfo'. uri was " + uri_str)
        if uri.scheme != "tecs" and uri.scheme != "tecs-tcp":
            raise ValueError("TCPEventSocket::connect requires 'tecs' or 'tecs-tcp' as scheme. got " + uri.scheme)

        req = HttpRequest(HttpMethod.CONNECT, uri.host, uri.path)
        req.add_header("Upgrade", constants.HTTP_UPGRADE_HEADER)
        req.add_header("Connection", "Upgrade")
        req.add_header("Client-Time", str(current_millis()))
        req.add_header("Client-Id", uri.userinfo)
        req.add_header("Client-Name", uri.userinfo)
        if additional_headers is not None:
            for header in additional_headers:
                req.add_header(header.get_key(), header.get_value())

        eve_socket = TCPEventSocket(uri.userinfo, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        tecs.get_logger(eve_socket).info("connecting to %s", uri_str)

        try:
            eve_socket.__socket.connect((uri.host, int(uri.port)))
        except socket.error as s_err:
            raise IOError(s_err.strerror)
        except OSError as os_err:
            raise IOError(os_err.strerror)

        req.transmit(eve_socket.__sos)
        # TODO set socket read timeout for detecting invalid behavior of remote endpoint
        http_rsp = HttpResponse()
        http_rsp.receive(eve_socket.__sis)

        if http_rsp.code() != 101:
            eve_socket.__socket.close()
            raise IOError("unexpected http code " + str(http_rsp.code()))

        tecs.get_logger(eve_socket).info("connected to %s", uri_str)
        return eve_socket

    def close(self):
        self.__log.debug("close()")
        try:
            self.__socket.shutdown(socket.SHUT_RDWR)
            self.__socket.close()
        except socket.error as e:
            self.__log.debug("disconnect failed: %s", e)

    def send_event(self, event):
        self.__log.debug("send_event %s", event)
        header_bytes = self.__event_factory.serialize(event.header())
        total_size = len(header_bytes) + len(event.data()) + 4
        self.__sos.writeI32(total_size)
        self.__sos.writeI32(len(header_bytes))
        self.__sos.write(header_bytes)
        self.__sos.write(event.data())

    def send(self, target, topic, tbase):
        self.__log.debug("send(%s,%s,%s)", target, topic, tbase.__class__)
        event = self.__event_factory.new_event(target, topic, tbase)
        self.send_event(event)

    def recv(self):
        self.__log.debug("recv()")
        frame_size = self.__sis.readI32()
        header_size = self.__sis.readI32()
        header_bytes = bytearray(header_size)
        self.__sis.read(header_bytes)
        header = self.__event_factory.deserialize_header(header_bytes)
        payload_bytes = bytearray(frame_size - header_size - 4)
        self.__sis.read(payload_bytes)
        remote_ep = self.__socket.getpeername()
        event = Event(header, payload_bytes, remote_ep)
        self.__log.debug("received %s from %s", header, remote_ep)
        return event


class SocketOutputStream:
    def __init__(self, socket):
        self.__socket = socket

    def write(self, buffer):
        self.__socket.sendall(buffer)
        # totalsent = 0
        # while totalsent < len(buffer):
        #     sent = self.__socket.send(buffer[totalsent:])
        #     if sent == 0:
        #         raise IOError("Socket Closed")
        #     if self.__stats:
        #         self.__stats.bytesSentTcp += sent
        #     totalsent += sent
        #     self.__bytes += sent
        # return totalsent

    def writeI32(self, i):
        self.write(struct.pack("!i", i))

    def writeLine(self, line_str):
        line_str = line_str + "\r\n"
        line_bytes = line_str.encode('ascii')
        # line_bytes = bytes(line_str + "\r\n", 'ASCII')
        self.write(line_bytes)


class SocketInputStream:
    def __init__(self, socket):
        self.__socket = socket

    def read(self, buffer):
        totalrecv = 0
        while totalrecv < len(buffer):
            data = self.__socket.recv(len(buffer) - totalrecv)
            if not data:
                raise IOError("Socket closed")
            buffer[totalrecv:totalrecv + len(data)] = data[0:len(data)]
            totalrecv += len(data)

        return totalrecv

    def readI32(self):
        buffer = bytearray(4)
        self.read(buffer)
        return struct.unpack('!i', buffer)[0]

    def readLine(self):
        sb = bytearray(0)
        while True:
            buffer = bytearray(1)
            self.read(buffer)
            # io error is thrown automatically
            c = buffer[0]
            if c == 0x0d:  # \r
                continue
            if c == 0x0a:  # \n
                return sb.decode('windows-1252')  # HTML uses ASCII
            sb.extend(buffer)
