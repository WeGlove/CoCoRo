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
from tecs import get_logger
import re



class HttpMethod:
    GET = "GET"
    POST = "POST"
    HEAD = "HEAD"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    TRACE = "TRACE"
    OPTIONS = "OPTIONS"
    CONNECT = "CONNECT"


class HttpResource(object):
    def accept(self, socket, httprequest):
        pass


class HttpHeader:

    def __init__(self, key, value):
        if key is None:
            raise ValueError("Key cannot be None")
        self.key = key
        self.value = value

    def get_key(self):
        return self.key

    def get_value(self):
        return self.value

    def __str__(self):
        return self.key + ": " + self.value


class HttpRequest(object):
    def __init__(self, method=None, host=None, res=None):
        self.__log = get_logger(self)
        self.__method = method
        self.__host = host
        self.__res = res
        self.__headers = []
        self.__contentLength = 0
        self.__body = None
        self.add_header("Host", host)

    def headers(self):
        return self.__headers

    def method(self):
        return self.__method

    def content_length(self):
        return self.__contentLength

    def body(self):
        return self.__body

    def resource(self):
        return self.__res

    def header(self, key):
        for val in self.__headers:
            if (val.get_key() == key):
                return val.get_value()
        return None

    def add_header(self, key, value):
        self.__headers.append(HttpHeader(key, value))
        if key == "Content-Length":
            self.__contentLength = int(value)
        if key == "Host":
            self.__host = value

    def transmit(self, socketoutputstream):
        socketoutputstream.writeLine(self.__method + " " + self.__res + " HTTP/1.1")
        for header in self.__headers:
            socketoutputstream.writeLine(header.key + ": " + header.value)
        socketoutputstream.writeLine("")
        if not self.__body:
            return

        if len(self.__body) != self.__contentLength:
            self.log.warn("Content-Length Header %s not set or does not match body length %s. Using body length.",
                          self.__contentLength, len(self.__body))
            self.__contentLength = len(self.__body);
        socketoutputstream.write(self.__body)

    def receive(self, socketinputstream):
        request_line = socketinputstream.readLine()
        request_line_ar = request_line.split(" ")
        self.__log.debug("Parsing Request Line %s to %s", request_line, request_line_ar)

        self.__method = request_line_ar[0]
        self.__res = request_line_ar[1]
        if ("HTTP/1.1" != request_line_ar[2]):
            raise IOError("HTTP/1.1 expected but " + request_line_ar[2] + " found")
        line = socketinputstream.readLine()
        while line != "":
            self.__log.debug("Parsing Header %s", line)
            split = line.split(": ", 1)
            self.add_header(split[0], split[1])
            line = socketinputstream.readLine()

        if self.__host is None:
            raise IOError("No host header specified")

        if self.__contentLength != 0:
            self.__body = bytearray(self.__contentLength)
            socketinputstream.read(self.__body)


class HttpResponse(object):

    def __init__(self, code=None, message=None):
        self.__code = code
        self.__message = message
        self.__headers = []
        self.__contentLength = 0
        self.__body = None

    def code(self):
        return self.__code

    def set_code(self, code):
        self.__code = code

    def message(self):
        return self.__message

    def set_message(self, message):
        self.__message = message

    def add_header(self, key, value):
        self.__headers.append(HttpHeader(key, value))
        if key == "Content-Length":
            self.__contentLength = int(value)

    def header(self, key):
        for header in self.__headers:
            if header.key == key:
                return header.value
        return None

    def set_body(self, buffer):
        self.__body = buffer

    def transmit(self, socketoutputstream):
        socketoutputstream.writeLine("HTTP/1.1 {} {}".format(self.__code, self.__message))
        for header in self.__headers:
            socketoutputstream.writeLine("{}: {}".format(header.key, header.value))

        socketoutputstream.writeLine("")

        if self.__body:
            if len(self.__body != self.__contentLength):
                self.log.warn("Content-Length not set. Transmitting all.")
            socketoutputstream.write(self.__body)

    def receive(self, socketinputstream):
        line = socketinputstream.readLine()
        responseLine = line.split(" ", 2)

        if responseLine[0] != "HTTP/1.1":
            raise RuntimeError("HTTP/1.1 expected but was " + responseLine[0])
        self.__code = int(responseLine[1])
        self.__message = responseLine[2]

        line = socketinputstream.readLine()
        while line != "":
            split = line.split(": ", 1)
            self.add_header(split[0], split[1])
            line = socketinputstream.readLine()

        if self.__contentLength != 0:
            self.__body = bytearray(self.__contentLength)
            socketinputstream.read(self.__body)



