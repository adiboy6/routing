import sim
import random
import topos.rand as rand

def launch (switch_type = sim.config.default_switch_type, host_type = sim.config.default_host_type,
            s = 6, h = None, latency = 1, seed = None):
    """
    Creates a random tree topology

    The tree will have *s* switches.
    If you specify *h*, it will also randomly scatter that many hosts among
    the switches.  If you don't specify *h*, you get one host per switch.

    This is really just a convenient wrapper for the "rand" topology generator.
    """
    if h is None:
      h = s
      mh = False
    else:
      mh = True

    rand.launch(switch_type = switch_type,
                host_type = host_type,
                switches = s,
                hosts = h,
                multiple_hosts = mh,
                links = 0, # It'll set this to be a tree
                latency = latency,
                seed = seed)
