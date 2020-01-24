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
import uritools
import tecs
import tecs.util
from tecs.net.http import HttpHeader
from tecs.net.tcp import TCPEventSocket
from tecs.ps.client import PSClient


class TCPPSClient(PSClient):
    def __init__(self, id, service_selector):
        super(TCPPSClient, self).__init__(id)
        self.__log = tecs.get_logger(self)

        self.__service_selector = service_selector
        self.__uri_str = None
        self.__service_selector_gen = None

    def service_descriptor(self):
        """
        :return: The sd used to connect to a remote endpoint. None if not connected
        """
        self.__log.debug("service_descriptor()")
        self._lock.acquire()
        uri_str = self.uri_str
        self._lock.release()
        return uri_str

    def __create_sub_header(self):
        self.__log.debug("__create_sub_header()")
        sub_str = ""
        i = 0
        for topic in self._subscriptions:
            sub_str += topic
            if i < len(self._subscriptions) - 1:
                sub_str += ","
            i += 1

        sub_header = HttpHeader("Subscription", sub_str)
        return sub_header

    def _connect_socket(self):
        self._lock.acquire()
        headers = None
        if len(self._subscriptions) > 0:
            headers = [self.__create_sub_header()]
        self._lock.release()

        if not self.__service_selector_gen:
            self.__service_selector_gen = self.__service_selector.select()

        sd = next(self.__service_selector_gen)
        if not sd:
            # TODO this delays the discovery too much if many advertiseevents are received
            tecs.util.sleep(50)
            return None

        if tecs.ps.tecs_server_filter(sd):
            return None

        self.__log.debug("discovered %s", sd)
        uri = uritools.urisplit(sd.uri)
        uri_str = "{}://{}@{}:{}{}".format(uri.scheme, self._id, uri.host, uri.port, uri.path)
        self.__log.info("connecting to %s", uri_str)
        try:
            new_sock = TCPEventSocket.connect(uri_str, headers)
        except (IOError, ValueError) as ex:
            self.__log.info("could not connect to %s: %s", uri_str, ex)
            tecs.util.sleep(1000)  # could be avoided => remember if the service_selector starts repeating
            return None

        self.__service_selector.stop()
        self.__service_selector_gen = None
        return new_sock
