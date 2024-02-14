import sim

def launch (n = 3, h = None, tail = False, latency = 1,
            switch_type = sim.config.default_switch_type,
            host_type = sim.config.default_host_type):
  """
  Creates a ring topology

  If --tail, one switch has an extra "tail" switch which always has a host.

  --n=X specifies the ring has X switches (not counting the tail)

  --h=X can be used to give a number of switches which should have hosts
  (these are assigned deterministically using different methods for
  tailed and tailless topologies).

  --h can also be given a list of switches which should have hosts, e.g.,
  --h=1,3,5

  --latency sets the link latency (defauling to 1)
  """

  base = 1

  n = int(n)
  latency = float(latency)

  has_tail = tail

  if has_tail:
    tail = switch_type.create("s1")
    base += 1
    if h is None: h = 0
  else:
    if h is None: h = n

  sws = {}

  for i in range(base,n+base):
    sws[i] = switch_type.create("s"+str(i))

  for i in range(base,n+base-1):
    sws[i].linkTo(sws[i+1], latency=latency)
  sws[base].linkTo(sws[n+base-1], latency=latency)

  if has_tail:
    sws[1] = tail
    tail.linkTo(sws[2], latency=latency)

    h1 = host_type.create("h1")
    h1.linkTo(tail, latency=latency)

  try:
    h = int(h)
  except Exception:
    h = h.replace(","," ").lower().split()
    h = [x[1:] if x.startswith("s") else x for x in h]

  if isinstance(h, int) and has_tail:
    x = h
    first = n // 2 + base
    h = []
    phase = -1
    for i in range(1,x+1):
      hh = ((i+0.5)//2) * phase + first
      if hh == n+base: hh = base
      if hh not in sws or hh in h:
        raise RuntimeError("Too many hosts")
      h.append(hh)
      phase = -phase
  elif isinstance(h, int):
    nodes = sorted(list(sws.keys()))
    if len(nodes) & 1: nodes.append(-1)
    step = len(nodes) // 2
    half = step
    x = h
    h = []
    done = set()
    cur = 0
    while len(done) < len(nodes):
      if nodes[cur] not in done:
        h.append(nodes[cur])
        done.add(nodes[cur])
      if nodes[cur+half] not in done:
        h.append(nodes[cur+half])
        done.add(nodes[cur+half])
      cur += step
      if cur >= half:
        step //= 2
        cur = step

    h = [z for z in h if z != -1]
    h = h[:x]

  h = [int(x) for x in h]

  for i in h:
    host = host_type.create('h' + str(i))
    sws[i].linkTo(host, latency=latency)
