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
import tecs.basetypes
from tecs.net.http_server import HttpHandler
from tecs.net.tcp import SocketOutputStream, HttpResponse, TCPEventSocket


class MPHandler(HttpHandler):
    def __init__(self, resource):
        self.__log = tecs.get_logger(self)
        self._resource = resource
        pass

    def accept(self, http_req, client_socket):
        if http_req.header("Connection") != "Upgrade":
            return False

        if http_req.header("Upgrade") != tecs.basetypes.constants.HTTP_UPGRADE_HEADER:
            return False

        if http_req.resource() != self._resource:
            return False

        client_name = http_req.header("Client-Name")
        if not client_name:
            client_name = http_req.header("Client-Id")

        sos = SocketOutputStream(client_socket)
        if not client_name:
            rsp = HttpResponse(400, "Missing Header: Client-Name")
            rsp.add_header("Connection", "Close")
            rsp.transmit(sos)
            return True

        rsp = HttpResponse(101, "Switching Protocols")
        rsp.add_header("Connection", "Upgrade")
        rsp.add_header("Upgrade", tecs.basetypes.constants.HTTP_UPGRADE_HEADER)
        rsp.transmit(sos)
        event_socket = TCPEventSocket(client_name, client_socket)
        self.__log.info("accepted client %s", client_name)
        self._on_socket(event_socket)
        return True

    def _on_socket(self, event_socket):
        # override this method
        event_socket.close()
