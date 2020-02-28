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
import random
import sys
import time
from tecs.basetypes.ttypes import EventHeader
import tecs.util


class Event:
    def __init__(self, header, data, remote=(None, None)):
        self.__event_header = header
        self.__data = data
        self.__remote_host = remote[0]
        self.__remote_port = remote[1]

    def remote_host(self):
        return self.__remote_host

    def remote_port(self):
        return self.__remote_port

    def topic(self):
        return self.__event_header.topic

    def uuid(self):
        return self.__event_header.uuid

    def source(self):
        return self.__event_header.source

    def target(self):
        return self.__event_header.target

    def timestamp(self):
        return self.__event_header.time

    def __str__(self):
        return "Event({}, data: {}B, from={}:{})".format(str(self.__event_header), len(self.__data),
                                                         self.__remote_host, self.remote_port())

    def header(self):
        return self.__event_header

    def data(self):
        return self.__data

    def hash_code(self):
        hash = 3
        hash = 13 * hash + int(self.timestamp() ^ (self.timestamp() >> 32))
        hash = 13 * hash + int(self.uuid() ^ (self.uuid() >> 32))
        return hash

    def topic_is(self, topic):
        return topic == self.__event_header.topic

    def parse(self, base):
        """
        :raise ValueError if deserialization fails
        :param base:
        :return:
        """
        base = tecs.util.deserialize(base, self.__data)
        return base

    def parse_data(self, base):
        """
        :raise ValueError if deserialization fails
        :param base:
        :return:
        """
        return self.parse(base)

    def context(self):
        return self.__event_header.context


class EventFactory:
    def __init__(self, id):
        if not id:
            raise RuntimeError("Must have an id")

        self.__id = id

    def has_context(self):
        return self.__context is not None

    def new_event(self, target, topic, data):
        # if self.context:
        #     header.context = self.context

        header = self.create_header(target, topic)
        return Event(header, tecs.util.serialize(data))

    def create_header(self, target, topic):
        header = tecs.basetypes.ttypes.EventHeader(target, source=self.__id, time=tecs.util.current_millis(),
                                                   uuid=random.randint(0, 2.30584301e18),
                                                   topic=topic)
        return header

    def serialize(self, tbase):
        return tecs.util.serialize(tbase)

    def serialize_event(self, event):
        header = tecs.util.serialize(event.header())
        dataRaw = event.data()

        return (header + (dataRaw))

    def deserialize_header(self, header_bytes):
        output = tecs.util.deserialize(tecs.basetypes.ttypes.EventHeader(), header_bytes)

        return output

    def deserialize(self, tbase, data):
        return tecs.util.deserialize(tbase, data)
