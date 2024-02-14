"""
Framework code for the Distance Vector router project

Authors:
  zhangwen0411, MurphyMc (ancient, 2021), lab352 (2020)
"""

#NOTE: This file is written in POX style.

from __future__ import print_function
import sim.api as api
from collections import namedtuple
from numbers import Number  # Available in Python >= 2.7.



# Used for a time ininitely in the future.
# (e.g., for routes that should never time out)
FOREVER = float("+inf")  # Denotes forever in time.



class AdvertisementPacket (api.Packet):
  """
  A DV route advertisement packet

  Note that these packets have both a .dst and a .destination.
  The former is the destination address for the packet, the same as any
  packet has a destination address.
  The latter is the destination for which this is a route advertisement.
  """
  def __init__ (self, destination, latency):
    super(AdvertisementPacket, self).__init__()
    self.latency = latency
    self.destination = destination
    self.outer_color = [1, 0, 1, 1]
    self.inner_color = [1, 0, 1, 1]

  def __repr__ (self):
    n = getattr(self.destination, "name", str(self.destination))
    return "<Advertisement to:%s cost:%s>" % (
        n, self.latency)



PortInfo = namedtuple("PortInfo", ("port","latency"))

class PortCollection (object):
  """
  Ports for a given router

  You can access it very much like a list.  It has an element for each
  port.  If the port/link is down, the corresponding element will be
  None, otherwise it's the latency of the link.

  Thus, if it is [None, None, 1], that means ports 0 and 1 are down,
  and port 2 has a latency of 1 second.

  You can get a list of only the ports that are up using the .up
  atribute, which gives (port_num,latency) pairs.
  """
  def __init__ (self):
    self._p = []

  def __getitem__ (self, n):
    if n < 0: return None
    if n >= len(self._p): return None
    return self._p[n]

  def get_latency (self, n):
    return self[n]

  def __iter__ (self):
    return iter(self._p)

  @property
  def up (self):
    """
    (Port,Latency) pairs for all up ports
    """
    return [PortInfo(n,l) for n,l in enumerate(self._p) if l is not None]

  @property
  def up_ports (self):
    """
    Port numbers of the up ports
    """
    return [n for n,l in enumerate(self._p) if l is not None]

  def __len__ (self):
    return len(self._p)

  def _set (self, p, l):
    while len(self) <= p:
      self._p.append(None)
    self._p[p] = l

  def __repr__ (self):
    return repr(self._p)



class DVRouterBase (api.Entity):
  """
  Base class for implementing a distance vector router
  """

  # You can/should access these things without the leading
  # underscores!

  # The maximum legal route distance
  __INFINITY = 16

  # A route should time out after this interval
  __ROUTE_TTL = 15

  # Don't worry about this; just use the normal route TTL
  ## Poison entries should time out after this interval
  #__POISON_TTL = 15

  # Whether to drop "hairpin" packets
  __DROP_HAIRPINS = False

  # -----------------------------------------------
  # At most one of these should ever be on at once
  __SPLIT_HORIZON = False
  __POISON_REVERSE = False
  # -----------------------------------------------

  # Determines if you send poison for expired routes
  __POISON_EXPIRED = True

  # Determines if you send updates when a link comes up
  __SEND_ON_LINK_UP = True

  # Determines if you send poison when a link goes down
  __POISON_ON_LINK_DOWN = True

  # This is how often we should send periodic advertisements
  __PERIODIC_INTERVAL = 5

  # Whether to randomize router timers
  __RANDOMIZE_TIMERS = False

  @property
  def INFINITY (self):
    return DVRouterBase.__INFINITY

  @property
  def ROUTE_TTL (self):
    return DVRouterBase.__ROUTE_TTL

  #@property
  #def POISON_TTL (self):
  #  return DVRouterBase.__POISON_TTL

  @property
  def DROP_HAIRPINS (self):
    return DVRouterBase.__DROP_HAIRPINS

  @property
  def SPLIT_HORIZON (self):
    return DVRouterBase.__SPLIT_HORIZON

  @property
  def POISON_REVERSE (self):
    return DVRouterBase.__POISON_REVERSE

  @property
  def POISON_EXPIRED (self):
    return DVRouterBase.__POISON_EXPIRED

  @property
  def SEND_ON_LINK_UP (self):
    return DVRouterBase.__SEND_ON_LINK_UP

  @property
  def POISON_ON_LINK_DOWN (self):
    return DVRouterBase.__POISON_ON_LINK_DOWN

  @property
  def PERIODIC_INTERVAL (self):
    return DVRouterBase.__PERIODIC_INTERVAL

  @property
  def RANDOMIZE_TIMERS (self):
    return DVRouterBase.__RANDOMIZE_TIMERS

  @property
  def s_info (self):
    """
    Info to appear in NetVis Info window when this node is selected
    """
    return self._s_info

  @s_info.setter
  def s_info (self, info):
    info = str(info)
    self._s_info = info
    if api.netvis.selected is self:
      api.netvis.info = info

  @property
  def table (self):
    return self._table

  def __init__ (self):
    assert not (self.SPLIT_HORIZON and self.POISON_REVERSE), \
          "Split horizon and poison reverse can't both be on"

    # Make sure our NetVis integration is set up
    api.netvis.set_selection_callback(_on_netvis_select)

    self._s_info = None # Use self.s_info to set the Info window when selected

    self.start_timer() # Starts signaling the timer at correct rate.

    # Contains all current ports and their latencies.
    # See the write-up for documentation.
    self.ports = PortCollection()

    # This is the table that contains all current routes
    self._table = Table()
    self.table.owner = self

    self.initialize()

  def initialize (self):
    """
    Allows subclasses to do initialization
    """
    pass

  def start_timer (self, interval=None):
    """
    Start the timer that calls handle_timer()

    This should get called in the constructor.

    !!! DO NOT OVERRIDE THIS METHOD !!!
    """
    if interval is None:
      interval = DVRouterBase.__PERIODIC_INTERVAL
      if interval is None: return

    def real_start_timer ():
      api.create_timer(interval, self.handle_timer)

    if self.__RANDOMIZE_TIMERS:
      import random
      api.create_timer(interval * random.random(), real_start_timer,
                       recurring=False)
    else:
      real_start_timer()

  def handle_rx (self, packet, in_port):
    """
    Called by the framework when this router receives a packet.

    The implementation calls one of several methods to handle the specific
    type of packet that is received.  You should implement your
    packet-handling logic in those methods instead of modifying this one.

    !!! DO NOT OVERRIDE THIS METHOD !!!
    """
    if isinstance(packet, AdvertisementPacket):
      self.expire_routes()
      self.on_route_advertisement(packet.destination,
                                  packet.latency,
                                  in_port)
    elif isinstance(packet, HostDiscoveryPacket):
      self.add_static_route(packet.src, in_port)
    else:
      self.on_data_packet(packet, in_port)

  def handle_timer (self):
    """
    Called periodically when the router should send tables to neighbors

    You probably want to override this.
    """
    self.expire_routes()
    self.send_routes(force=True)

  def handle_link_up (self, port, latency):
    """
    Called by the simulator when a link goes up

    !!! DO NOT OVERRIDE THIS METHOD !!!
    """
    self.ports._set(port, latency)
    self.on_link_up(port, latency)

  def handle_link_down (self, port):
    """
    Called by the simulator when a link goes up

    !!! DO NOT OVERRIDE THIS METHOD !!!
    """
    latency = self.ports.get_latency(port)
    self.ports._set(port, None)
    self.on_link_down(port, latency)

  def send_routes (self, force=False, single_port=None):
    """
    Called when routes should (possibly) be sent

    This is called periodically with force=True to send periodic updates.
    It is called with force=False to (possibly) send triggered updates.
    If single_port is not specified, it should send advertisements to
    all neighors.  If single_port *is* specified, it's a single port
    out which to send advertisements.

    You should implement this method.  As part of your implementation,
    you'll want to call send_advertisement_packet().
    """
    pass

  def add_static_route (self, host, port):
    """
    Called when you should add a static route to your routing table

    You probably want to override this.
    """
    pass

  def on_route_advertisement (self, destination, latency, port):
    """
    Called when this router receives a route advertisement packet

    You probably want to override this.
    """
    pass

  def on_data_packet (self, packet, in_port):
    """
    Called when this router receives a data packet

    You probably want to override this.
    """
    pass

  def on_link_up (self, port, latency):
    """
    Called when a link attached to this router goes up.

    :param port: the port that the link is attached to.
    :param latency: the latency of the link that went up.

    You probably want to override this.
    """
    pass

  def on_link_down (self, port, latency):
    """
    Called when a link attached to this router does down.

    :param port: the port number used by the link.
    :param latency: the latency of the link that went down.

    You probably want to override this.
    """
    pass

  def send_advertisement_packet (self, port, destination, latency):
    """
    Creates a route advertisement packet and sends it out the given port

    !!! DO NOT OVERRIDE THIS METHOD !!!
    """
    pkt = AdvertisementPacket(destination=destination, latency=latency)
    self.send(pkt, port=port)

  def s_log (self, fmt, *args):
    """
    Logs a message if this node is selected in NetVis

    DO NOT remove any existing code from this method.

    :param message: message to be logged.
    :returns: nothing.
    """
    try:
      if api.netvis.selected == self.name:
        self.log(fmt, *args)
    except:
      self.log(fmt, *args)



class _ValidatedDict (dict):
  """
  Superclass for dicts with data validation
  """
  def __init__ (self, *args, **kwargs):
    super(_ValidatedDict, self).__init__(*args, **kwargs)
    for k, v in self.items():
      self.validate(k, v)

  def __setitem__ (self, key, value):
    self.validate(key, value)
    return super(_ValidatedDict, self).__setitem__(key, value)

  def update (self, *args, **kwargs):
    super(_ValidatedDict, self).update(*args, **kwargs)
    for k, v in self.items():
      self.validate(k, v)

  def validate (self, key, value):
    """Raises ValueError if (key, value) is invalid."""
    raise NotImplementedError("Dict validation not implemented")



class Table (_ValidatedDict):
  """
  A routing table

  You should use a `Table` instance as a `dict` that maps a
  destination host to a `TableEntry` object.
  """
  owner = None

  def validate (self, destination, entry):
    """Raises ValueError if destination and entry have incorrect types."""
    if not isinstance(destination, api.HostEntity):
      raise ValueError("destination %s is not a host" % (destination,))

    if not isinstance(entry, TableEntry):
      raise ValueError("entry %s isn't a table entry" % (entry,))

    if entry.destination != destination:
      raise ValueError("entry destination %s doesn't match key %s" %
               (entry.destination, destination))

  def __str__ (self):
    o = "=== Table"
    if self.owner and getattr(self.owner, 'name'):
      o += " for " + str(self.owner.name)
    o += " ===\n"

    if not self:
      o += "(empty table)"
    else:
      o += "%-6s %-3s %-4s %s\n" % ("name", "prt", "lat", "sec")
      o += "------ --- ---- -----\n"
      ent = lambda x: x.dump() if isinstance(x, TableEntry) else str(x)
      o += "\n".join(ent(v) for v in self.values())
    return o

  def add (self, entry):
    self[entry.destination] = entry



class TableEntry (namedtuple("TableEntry",
                             ["destination", "port", "latency",
                              "expire_time"])):
  """
  An entry in a Table, representing a route from a neighbor to some
  destination host.

  Example usage:
    rte = TableEntry(
      destination=h1, latency=10, expire_time=api.current_time()+10
    )
  """

  def __new__ (cls, destination, port, latency, expire_time):
    """
    Creates a table entry, denoting a route advertised by a neighbor.

    A TableEntry is immutable.

    :param destination: the route's destination host.
    :param port: the port that this route takes.
    :param latency: the route's advertised latency (DO NOT include the link
            latency to this neighbor). #FIXME: Yes, do include it?
    :param expire_time: time point (seconds) at which this route expires.
    """
    if not isinstance(destination, api.HostEntity):
      raise ValueError("Provided destination %s is not a host" % (destination,))

    if not isinstance(port, int):
      raise ValueError("Provided port %s is not an integer" % (port,))

    if not isinstance(expire_time, Number):
      raise ValueError("Provided expire time %s is not a number"
               % (expire_time,))

    if not isinstance(latency, Number):
      raise ValueError("Provided latency %s is not a number" % latency)

    self = super(TableEntry, cls).__new__(cls, destination, port,
                        latency, expire_time)
    return self

  @property
  def is_expired (self):
    return api.current_time() > self.expire_time

  def __str__ (self):
    latency = self.latency
    if int(latency) == latency: latency = int(latency)
    return "%-6s p:%-3s l:%-4s e:%0.2f" % (
         api.get_name(self.destination), self.port, latency,
         self.expire_time - api.current_time())

  def dump (self):
    latency = self.latency
    if int(latency) == latency: latency = int(latency)
    return "%-6s %-3s %-4s %0.2f" % (
         api.get_name(self.destination), self.port, latency,
         self.expire_time - api.current_time())



# Host discovery packets are treated as an implementation detail --
# they're how we know when to call add_static_route().  Thus, we make
# them invisible in the simulator.
from sim.basics import HostDiscoveryPacket
HostDiscoveryPacket.outer_color = [0, 0, 0, 0]
HostDiscoveryPacket.inner_color = [0, 0, 0, 0]



# This enables the s_info feature.  See help(api.NetVis) for more ways
# to customize your interaction with NetVis.
def _on_netvis_select (which):
  if which == 'selected':
    if api.netvis.selected and isinstance(api.netvis.selected, DVRouterBase):
      info = api.netvis.selected.s_info
      if info is not None:
        api.netvis.info = info
