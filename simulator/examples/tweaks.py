"""
Tweaks parameters
"""

import sim.core as core

def _fix (n):
  try:
    n = float(n)
    if n == int(n): n = int(n)
  except:
    pass
  return n

def _tobool (s):
  if not s : return False
  return str(s).lower()[0] in "1tye"


def launch (seed = None, pong = None):
  """
  Tweaks various parameters.

  You probably want to initialize this module before most others.
  """
  if seed is not None:
    import random
    random.seed(_fix(seed))

  if pong is not None:
    import sim.basics
    sim.basics.BasicHost.ENABLE_PONG = _tobool(pong)
