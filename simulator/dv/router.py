"""
Skeleton for your awesome Distance Vector router
"""

from __future__ import print_function
import sim.api as api
from dv.dv_base import (Table,
                        TableEntry,
                        DVRouterBase,
                        FOREVER)



class DVRouter (DVRouterBase):
  """
  Your own distance-vector router
  """

  # The following are set up for you by the superclass.
  # If you want to override them, for experimentation/testing, use
  # the command line.  The relevant option is shown after the name
  # in the list below.  For example, to change the route TTL and
  # turn on poison reverse, insert the following into your
  # simulator.py command line *before* specifying the topology:
  #   dv --ttl=5 --pr

  # Maximum legal route distance
  # INFINITY = 16 # --inf=X

  # A route should time out after this interval
  # ROUTE_TTL = 15 # --ttl=X

  # Whether to drop "hairpin" packets
  # DROP_HAIRPINS = False # --drop-hairpins

  # -----------------------------------------------
  # At most one of these should ever be on at once
  # SPLIT_HORIZON = False # --sh
  # POISON_REVERSE = False # --pr
  # -----------------------------------------------

  # Determines if you send poison for expired routes
  # POISON_EXPIRED = True # --p

  # Determines if you send updates when a link comes up
  # SEND_ON_LINK_UP = True # --link-up

  # Determines if you send poison when a link goes down
  # POISON_ON_LINK_DOWN = True # --link-down

  # How often we should send periodic advertisements
  # PERIODIC_INTERVAL = 5 # --period=X

  # Whether to randomize router timers
  # RANDOMIZE_TIMERS = False # --unsync


  def initialize (self):
    """
    You can do whatever setup you like here.

    Everything (including .table and .ports) has already been initialized.
    """
    # stores the previously recently advertised routes or the historical routes
    self.prev_adv_table = Table()


  def add_static_route(self, host, port):
    """
    Adds a static route to this router's table.

    Called automatically by the framework whenever a host is connected
    to this router.

    :param host: the host that the route is for.
    :param port: the port towards the host.
    """
    if host not in self._table:
      self._table[host]=TableEntry(destination=host, port=port, latency=self.ports.get_latency(port),expire_time=FOREVER)
    
    # send and immediate update about the new route
    self.send_routes(force=False)

  def on_data_packet (self, packet, in_port):
    """
    Called when a data packet arrives at this router.

    You may want to forward the packet, drop the packet, etc. here.

    :param packet: the packet that arrived.
    :param in_port: the port from which the packet arrived.
    """
    if packet.dst in self._table:
      # latency of that route is greater than or equal to INFINITY, then drop that packet
      if self._table[packet.dst].latency >= self.INFINITY:
          return
      if (in_port != self._table[packet.dst].port) or ( in_port == self._table[packet.dst].port and self.DROP_HAIRPINS == False ):
        self.send(packet,self._table[packet.dst].port)


  def send_routes (self, force=False, single_port=None):
    """
    Send route advertisements for all routes in the table.

    :param force: if True, advertises ALL routes in the table;
                  otherwise, advertises only those routes that have
                  changed since the last advertisement.  (force will
                  be True when called for periodic advertisements.)
    :single_port: if not None, sends updates only to that port; to
                  be used in conjunction with on_link_up().
    """
    # before sending, check if there's any expired routes..
    self.expire_routes()
    
    if single_port==None:
      for port in self.ports.up_ports:
        self.send_single_route(force, port)
    else:
      self.send_single_route(force, single_port)
    self.prev_adv_table = self._table
    self._table = Table(self.prev_adv_table)


  def send_single_route(self, force=False, port=None):
    """
    Send route advertisements for a single port in the table.
    
    :param force: if True, advertises ALL routes in the table;
                  otherwise, advertises only those routes that have
                  changed since the last advertisement.  (force will
                  be True when called for periodic advertisements.)
    :single_port: if not None, sends updates only to that port; to
                  be used in conjunction with on_link_up().
    """
    for host in self._table:
      table_entry = self._table[host]
      
      if table_entry.port != port or not self.POISON_REVERSE:
        curr_latency = table_entry.latency 
      else:
        curr_latency = self.INFINITY
      
      if host in self.prev_adv_table and not force:
        prev = self.prev_adv_table[host]
        if prev.port != port or not self.POISON_REVERSE:
          prev_latency = prev.latency 
        else:
          prev_latency = self.INFINITY
        
        if prev_latency == curr_latency:
          continue
      
      if port != table_entry.port or not self.SPLIT_HORIZON:
        self.send_advertisement_packet(port,host,curr_latency)


  def expire_routes (self):
    """
    Clears expired routes out of table.

    This will be called periodically for you (you shouldn't call
    it yourself).
    """
    hosts = list(self.table.keys())
    for host in hosts:
      table_entry = self.table[host]
      # don't delete hosts routes
      if table_entry.expire_time == FOREVER:
        return

      # delete the route if it's expired
      if not self.POISON_EXPIRED and api.current_time() > table_entry.expire_time:
        del self.table[host]
      # delete the route if it's poisoned
      elif api.current_time() > table_entry.expire_time:
        current_route = self.table[host]
        poison_route = TableEntry(host, current_route.port, latency=self.INFINITY, expire_time=self.ROUTE_TTL)
        self.table[host] = poison_route
            

  def on_route_advertisement (self, destination, latency, port):
    """
    Called when the router receives a route advertisement from a neighbor.

    :param destination: the destination of the advertised route.
    :param latency: latency from the neighbor to the destination.
    :param port: the port that the advertisement arrived on.
    """
    if latency != self.INFINITY:
      # if no record is found, then the new route should be added by default
      if (destination not in self._table) or (latency + self.ports.get_latency(port) < self._table[destination].latency) or (port == self._table[destination].port):
        self._table[destination]=TableEntry(destination=destination, port=port, latency=latency + self.ports.get_latency(port), expire_time=api.current_time()+self.ROUTE_TTL)
    else:
      # if route is poisned
      if destination in self._table and port == self._table[destination].port:
        table_entry=self._table[destination]
        if table_entry.latency<self.INFINITY:
          self._table[destination]=TableEntry(destination=destination, port=port, latency=self.INFINITY,
                                              expire_time=api.current_time()+self.ROUTE_TTL)
        else:
          self._table[destination]=TableEntry(destination=destination, port=port, latency=self.INFINITY,
                                              expire_time=table_entry.expire_time)

    # send updates only about changed routes
    self.send_routes(force=False)


  def on_link_up (self, port, latency):
    """
    Called by the framework when a link attached to this router goes up.

    :param port: the port that the link is attached to.
    :param latency: the latency of the link that went up.
    """
    self.ports._set(port, latency)
    if self.SEND_ON_LINK_UP:
        self.send_routes(force=True, single_port=port)


  def on_link_down (self, port, latency):
    """
    Called by the framework when a link attached to this router does down.

    :param port: the port number used by the link.
    :param latency: the latency of the link that went down.
    """
    self.ports._set(port, None)
    if self.POISON_ON_LINK_DOWN:
        for destination in self._table:
            if self._table[destination].port == port:
                self.table[destination] = TableEntry(destination=self._table[destination].destination, port=port, latency=self.INFINITY,
                                           expire_time=api.current_time()+self.ROUTE_TTL)
    self.send_routes(force=False)

# Feel free to add any helper methods!
