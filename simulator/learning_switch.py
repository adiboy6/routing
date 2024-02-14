"""
Skeleton for your Learning Switch

Start it up with a commandline like...

  ./simulator.py --default-switch-type=learning_switch topos.rand_tree --links=3

"""

from __future__ import print_function
import sim.api as api
import sim.basics as basics
from ls.learning_switch_base import LearningSwitchBase


class LearningSwitch (LearningSwitchBase):
  """
  A learning switch

  Looks at source addresses to learn where endpoints are.  When it doesn't
  know where the destination endpoint is, floods.

  This will surely have problems with topologies that have loops!  If only
  someone would invent a helpful poem for solving that problem...
  """

  # Learned table entries should only live for a given amount of time.
  # It should be settable by changing this (you may want to do that for
  # testing purposes).
  TIMEOUT = 15
  
  def _init_ (self):
    self.routing_table=dict()

  def on_link_up (self, port):
    """
    Called when a port goes up (because a link is added)

    Do you want to do anything here?
    """
    
    for dst, (p, _) in self.routing_table.items():
      if(p==port):
        self.routing_table[dst]=[p, api.current_time()]
    
  def on_link_down (self, port):
    """
    Called when a port goes down (because a link is removed)

    You probably want to remove table entries which are no longer valid here.
    """
    
    for dst, (p, _) in self.routing_table.items():
      if(p==port):
        # invalidating the entry
        self.routing_table[dst]=[p, api.current_time()+self.TIMEOUT+1]

  def on_timer (self):
    """
    Called once per second

    You may want to do something in this method.

    You can use api.current_time() to get the current time (in seconds).
    """
    try:
      for i in self.routing_table:
        if (api.current_time()-self.routing_table[i][1])>self.TIMEOUT:
          print(self.name,"adios..",i,self.routing_table[i])
          del self.routing_table[i]  
    except Exception as e:
      pass

  def on_data_packet (self, packet, in_port):
    """
    Called when a packet is received

    You most certainly want to process packets here, learning where they're
    from, and either forwarding them toward the destination or flooding them.
    """

    # The source of the packet can obviously be reached via the input port, so
    # we should "learn" that the source host is out that port.  If we later see
    # a packet with that host as the *destination*, we know where to send it!
    # But it's up to you to implement that.  For now, we just implement a
    # simple hub.

    # Flood out all ports except the input port
    
    self.routing_table[packet.src.name]=[in_port,api.current_time()]
    if packet.dst.name in self.routing_table:
      self.send(packet, self.routing_table[packet.dst.name][0])
    else:
      for port,latency in self.ports.up:
        if port != in_port:
          self.send(packet, port)
