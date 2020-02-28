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
import tecs
from tecs.net.event import EventFactory
from tecs.net.udp import UDPEventSocket
from tecs.ps.client import PSClient


class UDPPSClient(PSClient):
    def __init__(self, id, mc_addr, mc_port):
        super(UDPPSClient, self).__init__(id)
        self.__log = tecs.get_logger(self)
        self.__event_factory = EventFactory(id)
        self.__mc_addr = mc_addr
        self.__mc_port = mc_port

    def _connect_socket(self):
        new_sock = UDPEventSocket(self.__event_factory, self.__mc_port, True)
        try:
            new_sock.bind()
            new_sock.join_multicast_group(self.__mc_addr)
            new_sock.set_remote_endpoint(self.__mc_addr, self.__mc_port)
        except IOError as ioe:
            self.__log.warn("could not create udp socket: %s", ioe)
            new_sock.close()
            return None

        return new_sock

    def _filter_in_event(self, event):
        # filter for sub
        self._lock.acquire()
        for sub in self._subscriptions:
            if event.topic() == sub:
                self._lock.release()
                return False
        self._lock.release()

        return True
