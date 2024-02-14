import sim
import os.path

def _try_load (fn):
  fs = [fn]

  def maybe_local (f):
    if not f: return None
    if "/" in f: return None
    if "\\" in f: return None
    if os.path.sep in f: return None
    return os.path.join(os.path.dirname(__file__), f)

  def maybe_topo (f):
    if not f: return None
    if os.path.splitext(f)[1] != '': return None
    return f + ".topo"

  def add (f):
    if f: fs.append(f)

  add(maybe_topo(fn))
  add(maybe_local(fn))
  add(maybe_local(maybe_topo(fn)))

  #print(fs)
  for f in fs:
    try:
      return open(f, 'r')
    except (IOError, OSError):
      pass

  raise RuntimeError("Could not load topology '%s'" % (fn,))



def launch (filename="", switch_type = sim.config.default_switch_type, host_type = sim.config.default_host_type, topo=None):
  """
  Loads a topology from a file.

  The file format consists of lines beginning with "h" (for hosts), "s" (for
  switches), or "l" (links).  Host and switch lines specify a node name.
  Link lines specify the two nodes to link and optionally a link latency.

  Example:
    # The topology of THE ENTIRE INTERNET
    # (the important parts, anyway)
    h Me
    h GoogleServer
    h CatVideoServer
    s Berkeley
    s Comcast
    s GoogleNet
    s YouTubeNet
    l Me Berkeley 0.1
    l Berkeley Comcast 0.5
    l Comcast GoogleNet 0.5
    l GoogleNet GoogleServer 0.1
    l Comcast YouTubeNet 0.5
    l YouTubeNet CatVideoServer 0.1
  """
  assert filename or topo
  assert not (filename and topo)

  if filename:
    reader = _try_load(filename)
  else:
    reader = topo.split("\n")

  edges = []
  hosts = {}
  switches = {}

  def get_node (n):
    r = hosts.get(n)
    if r: return r
    return switches.get(n)

  for line in reader:
    line = line.strip()
    if not line: continue
    if line.startswith("#"): continue
    line = line.split(None, 1)
    assert len(line) >= 2
    t,rest = line

    t = t.lower()

    if t == "h":
      hosts[rest] = host_type.create(rest)
    elif t == "s":
      switches[rest] = switch_type.create(rest)
    elif t == "l":
      edges.append(rest)

  for rest in edges:
    rest = rest.split()
    assert len(rest) >= 2
    extra = {}
    if len(rest) == 3:
      # Latency
      extra['latency'] = float(rest[2])
    u,v = rest[:2]
    get_node(u).linkTo(get_node(v), **extra)
