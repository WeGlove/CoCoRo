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
import time

from thrift.Thrift import TException
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol


def serialize(msg):
    """
    :raise ValueError if serialization fails
    :param msg:
    :return:
    """
    try:
        transport_out = TTransport.TMemoryBuffer()
        prot_out = TBinaryProtocol.TBinaryProtocol(transport_out)
        msg.write(prot_out)
        bytes = transport_out.getvalue()
        return bytes
    except TException as tex:
        raise ValueError(tex.message)


def deserialize(msg, buf):
    """
    :raise ValueError if deserialization fails
    :param msg:
    :param buf:
    :return:
    """
    try:
        transport_in = TTransport.TMemoryBuffer(buf)
        prot_in = TBinaryProtocol.TBinaryProtocol(transport_in)
        msg.read(prot_in)
        return msg
    except TException as tex:
        raise ValueError(tex.message)


def current_millis():
    millis = int(round(time.time() * 1000))
    return millis


def sleep(ms):
    time.sleep(ms / 1000.0)



def is_multicast(address_str):
    is_ipv4 = is_ipv4_multicast(address_str)
    is_ipv6 = is_ipv6_multicast(address_str)
    return is_ipv4 or is_ipv6


def is_ipv4_multicast(address_str):
    try:
        first_byte = int(address_str.split(".")[0])
        if first_byte > 239:
            return False
        if first_byte < 224:
            return False
        return True
    except:
        return False


def is_ipv6_multicast(address_str):
    return address_str.startswith("ff00")


def compatible_version(user_version, provider_version):
    if user_version.major != provider_version.major:
        return False
    if user_version.minor > provider_version.minor:
        return False
    return True


def random_uuid():
    import uuid
    return str(uuid.uuid4())


class IntervalHelper:
    def __init__(self, interval=1000):
        self._execute_interval = interval
        self.last = 0

    # Returns true iff the time elapsed since the last call it returned true
    # is higher than the execution interval given in the constructor.
    # Otherwise it returns false.
    def should_execute(self):
        if self._execute_interval < 0:
            return False
        now = int(round(time.time() * 1000))
        diff = now - self.last
        if diff >= self._execute_interval:
            self.last = now
            return True
        else:
            return False

    # IntervalHelper::shouldExecute will return at most once true during the given time interval.
    # Given executeInterval < 0 IntervalHelper::shouldExecute will always return false.
    def set_interval(self, interval):
        self._execute_interval = interval

    def interval(self):
        return self._execute_interval

    # Rewinds the timer such that whole interval has to elapse again such that IntervalHelper::shouldExecute returns true again.
    def reset(self):
        lastTime = int(round(time.time() * 1000))


class Result:
    """
    Encapsulates a value xor an error. Used to represent the result of an operation that may fail.
    """
    def __init__(self, ex=None, value=None):
        self.__ex = ex
        self.__value = value

    def successful(self):
        return self.__value is not None

    def failed(self):
        return self.__ex is not None

    def value(self):
        return self.__value

    def error(self):
        return self.__ex

    def __str__(self):
        if self.failed():
            return "Failure{" + str(self.__ex) + "}"
        else:
            return "Success{" + str(self.__value) + "}"

    @staticmethod
    def failure(ex):
        return Result(ex=ex)

    @staticmethod
    def success(value=value):
        return Result(value=value)
