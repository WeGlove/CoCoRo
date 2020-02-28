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
import re

import tecs.net.http
from tecs.discovery import ServiceProvider
from tecs.net.tcp import SocketOutputStream, SocketInputStream, HttpRequest, HttpResponse


class HttpServer:
    def __init__(self, port, host="0.0.0.0"):
        self.__log = tecs.get_logger(self)
        self.__port = port
        self.__host = host
        self.__bound = False
        self.__handlers = []
        self.__service_provider = ServiceProvider()
        self.__server_socket = None

    def add_handler(self, handler):
        if self.__bound:
            raise ValueError("can't add handler: already bound")
        self.__handlers.append(handler)

    def bind(self):
        if self.__bound:
            raise ValueError("can't bind: already bound")

        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server_socket.setblocking(1)
        self.__server_socket.bind((self.__host, self.__port))
        self.__server_socket.listen(1)

        server_uri = str.format("0.0.0.0:{}", self.__server_socket.getsockname()[1])
        self.__log.debug("server uri is %s", server_uri)
        for handler in self.__handlers:
            sd = handler.service_descriptor(server_uri)
            if sd:
                self.__service_provider.add_service_descriptor(sd)

        self.__service_provider.start()
        self.__bound = True

    def accept(self):
        if not self.__bound:
            raise ValueError("can't accept: not bound")
        try:
            client_socket, addr = self.__server_socket.accept()
            # clientsock.setblocking(0)
            self.__log.info("new connection %s", addr)

            sis = SocketInputStream(client_socket)
            req = HttpRequest()
            req.receive(sis)

            for handler in self.__handlers:
                if handler.accept(req, client_socket):
                    return

            sos = SocketOutputStream(client_socket)
            rsp = HttpResponse(404, "Not Found")
            rsp.transmit(sos)
        except socket.error as e:
            if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                return None
            self.__log.warn("could not accept client: %s", e)

        except IOError as ioe:
            self.__log.warn("could not accept client: %s", ioe)
            pass


class HttpHandler(object):
    def __init__(self):
        pass

    def accept(self, http_req, client_socket):
        return False

    def service_descriptor(self, server_uri):
        return None


class HttpRequestResponse(tecs.net.http.HttpResource):
    def __init__(self, resource_regex, method_regex):
        self.__res_matcher = resource_regex
        self.__method_matcher = method_regex

    def handle_request(self, request):
        """
        :param request:
        :return: a HttpResponse
        """
        raise NotImplementedError("abstract method 'HttpRequestResponse::handle_request' called")

    def accept(self, socket, httprequest):
        if re.match(self.__res_matcher, httprequest.resource()):
            if re.match(self.__method_matcher, httprequest.method()):
                response = self.handle_request(httprequest)
                response.transmit(SocketOutputStream(socket))
                socket.close()
                return True
        return False
