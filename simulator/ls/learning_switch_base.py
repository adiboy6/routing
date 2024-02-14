"""
Base class for Learning Switches

These are implementation details you probably don't need to worry about.
"""

import sim.api as api
import sim.basics as basics
from collections import namedtuple

PortInfo = namedtuple("PortInfo", ("port","latency"))


class PortCollection (object):
  def __init__ (self):
    self._p = []

  def __getitem__ (self, n):
    if n < 0: return None
    if n >= len(self._p): return None
    return self._p[n]

  def __iter__ (self):
    return iter(self._p)

  @property
  def up (self):
    """
    (Port,Latency) pairs for all up ports
    """
    return [PortInfo(i,p) for i,p in enumerate(self._p) if p is not None]

  def __len__ (self):
    return len(self._p)

  def _set (self, p, l):
    while len(self) <= p:
      self._p.append(None)
    self._p[p] = l


class LearningSwitchBase (api.Entity):
  TIMER_INTERVAL = 1  # Default timer interval.

  def __init__ (self):
    self.ports = PortCollection()
    self._init_()

    interval = self.TIMER_INTERVAL
    if interval is not None:
      api.create_timer(interval, self.on_timer)

  def handle_rx (self, packet, in_port):
    if isinstance(packet, basics.HostDiscoveryPacket):
      # Don't forward discovery messages
      return

    self.on_data_packet(packet, in_port)

  def s_log (self, format, *args):
    """
    Logs the message.

    DO NOT remove any existing code from this method.

    :param message: message to be logged.
    :returns: nothing.
    """
    try:
      if api.netvis.selected == self.name:
        self.log(format, *args)
    except:
      self.log(format, *args)

  def handle_link_up (self, port, latency):
    self.ports._set(port, latency)
    self.on_link_up(port)

  def handle_link_down (self, port):
    self.ports._set(port, None)
    self.on_link_down(port)
