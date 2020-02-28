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
import tecs.basetypes

import uritools

import tecs.util
from tecs.basetypes import constants
from tecs.discovery import ServiceDescriptorBuilder, MulticastServiceSelector
from tecs.net import StaticServiceSelector
from tecs.ps.udp import UDPPSClient
from tecs.ps.tcp import TCPPSClient


def create(uri):
    parsed_uri = uritools.urisplit(uri)
    if parsed_uri.scheme == "tecs" or parsed_uri.scheme == "tecs-tcp":
        sd = ServiceDescriptorBuilder(constants.SERVICE_TYPE_TECS_SERVER, uri).set_version(
            constants.TECS_VERSION.major, constants.TECS_VERSION.minor, constants.TECS_VERSION.patch).build()
        ss = StaticServiceSelector([sd])
        return TCPPSClient(parsed_uri.userinfo, ss)
    elif parsed_uri.scheme == "tecs-dis":
        if not tecs.util.is_multicast(parsed_uri.host):
            raise ValueError("host of uri is not a valid multicast address. uri was " + uri)
        port = int(parsed_uri.port)
        context = parsed_uri.path
        if context.startswith("/"):
            context = context[1:]
        ss = MulticastServiceSelector(constants.SERVICE_TYPE_TECS_SERVER, parsed_uri.userinfo, context,
                                      parsed_uri.host, port)
        return TCPPSClient(parsed_uri.userinfo, ss)
    elif parsed_uri.scheme == "tecs-udp":
        if not tecs.util.is_multicast(parsed_uri.host):
            raise ValueError("host of uri is not a valid multicast address. uri was " + uri)
        port = int(parsed_uri.port)
        return UDPPSClient(parsed_uri.userinfo, parsed_uri.host, port)

    raise ValueError("could not create ps client: invalid uri: " + uri)


def tecs_server_filter(sd):
    if sd.type != tecs.basetypes.constants.SERVICE_TYPE_TECS_SERVER:
        return True
    if sd.version is None:
        return True
    if not tecs.util.compatible_version(tecs.basetypes.constants.TECS_VERSION, sd.version):
        return True

    return False
