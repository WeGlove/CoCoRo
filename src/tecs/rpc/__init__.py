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
import threading
import uritools
import thrift.transport.TSocket
import thrift.protocol.TBinaryProtocol
import thrift.server.TServer
import tecs.util
import tecs.basetypes.ttypes


class RPCClient:
    def __init__(self, client_factory, uri_supplier):
        self.__log = tecs.get_logger(self)
        self.__client_factory = client_factory
        self.__uri_supplier = uri_supplier

        # TODO check if factory and uri_supplier are valid
        # if not hasattr(client_factory.__class__, "get_client"):
        #     raise ValueError("RPC client factory needs a method 'get_client'")
        #
        # if not callable(getattr(client_factory.__class__, "get_client")):
        #     raise ValueError("RPC client factory needs a method 'get_client'")

    def call(self, t_consumer):
        uri = self.__uri_supplier()
        host = uri.host
        port = uri.port
        trans = thrift.transport.TSocket.TSocket(host, port)
        prot = thrift.protocol.TBinaryProtocol.TBinaryProtocol(trans)
        try:
            client = self.__client_factory(prot)
            trans.open()
            result = t_consumer(client)
            return tecs.util.Result.success(result)
        except Exception as ex:
            self.__log.warn("could not complete rpc call: %s", ex.message)
            trans.close()
            return tecs.util.Result.failure(ex)


class RPCClientFactory:
    @staticmethod
    def create_client(type, host, port):
        parsed_uri = uritools.urisplit("thrift-bin://{}:{}".format(host, port))
        uri_supplier = lambda: parsed_uri
        client_factory = RPCClientFactory.client_factory(type)
        client = RPCClient(client_factory, uri_supplier)
        return client

    @staticmethod
    def client_factory(type):
        def get_client_(protocol):
            client = type(protocol)
            return client

        return get_client_


class RPCServiceBuilder:
    def __init__(self, processor):
        self._sd = tecs.basetypes.ttypes.ServiceDescriptor(uuid="", uri="")
        self._proc = processor
        self._trans = None
        self._server = None
        self._port = 0

    def build(self):
        self._trans = thrift.transport.TSocket.TServerSocket("0.0.0.0", self._port)
        self._server = thrift.server.TServer.TThreadPoolServer(self._proc, self._trans, daemon=True)
        self._trans.listen()
        self._port = self._trans.handle.getsockname()[1]
        # print("port is {}".format(self._port))
        self._sd.uuid = tecs.util.random_uuid()
        uri = "{}://0.0.0.0:{}".format("thrift-bin", self._port)
        self._sd.uri = uri
        return RPCService(self)

    def set_port(self, port):
        self._port = port
        return self

    def set_type(self, type):
        self._sd.type = type
        return self

    def add_arg(self, key, value):
        if not self._sd.arguments:
            self._sd.arguments = map()
        self._sd.arguments[key] = value
        return self

    def set_context(self, context):
        self._sd.context = context
        return self

    def set_version(self, major, minor, patch):
        self._sd.version = tecs.basetypes.ttypes.Version(major, minor, patch)
        return self

    def set_data(self, data):
        self._sd.data = data
        return self


class RPCService:
    def __init__(self, builder):
        self.__sd = builder._sd
        self.__proc = builder._proc
        self.__trans = builder._trans
        self.__server = builder._server
        self.__thread = threading.Thread(target=self.__serve)
        self.__thread.setDaemon(True)
        self.__thread.start()

    def __serve(self):
        self.__server.serve()

    def service_descriptor(self):
        return self.__sd  # TODO copy sd

    def id(self):
        return self.__sd.uuid

    def close(self):
        self.__trans.close()

    def port(self):
        parsed_uri = uritools.urisplit(self.__sd.uri)
        return parsed_uri.port

    def join(self):
        self.__thread.join()

    @staticmethod
    def create(processor):
        return RPCServiceBuilder(processor)
