from sim.core import TopoNode
import logging

def _to_bool (s):
  s = str(s).lower()
  if not s: return False # ???
  s = s[0]
  if s in "ty1e": return True
  return False

def _setup (opts):
  r = {}
  for oo in opts.strip().split("\n"):
    oo = oo.strip().split()
    if not oo: continue
    t = oo[0]
    t = {"b":_to_bool, "f":float}[t]
    c = oo[1]
    oo = oo[1:]
    for o in oo:
      o = o.lstrip("-").lower()
      r[o] = (t,c)

  return r

_opts = _setup("""
f ROUTE_TTL --ttl
f POISON_TTL --pttl
f INFINITY --inf
f PERIODIC_INTERVAL --period
b SPLIT_HORIZON --sh
b POISON_REVERSE --pr
b POISON_EXPIRED --p
b SEND_ON_LINK_UP --link-up
b POISON_ON_LINK_DOWN --link-down
b RANDOMIZE_TIMERS --unsync
b DROP_HAIRPINS --nohairpin
""")


from dv.dv_base import DVRouterBase

def launch (**kw):
  """
  Configure distance-vector router options

  See the list of options above
  """

  if TopoNode.ANY_CREATED:
    raise RuntimeError("You must adjust DV options *before* you specify "
                       + "the topology")

  for k,v in kw.items():
    convert,xcanon = _opts[k.lower()]
    v = convert(v)
    canon = "_DVRouterBase__" + xcanon

    assert hasattr(DVRouterBase, canon)

    setattr(DVRouterBase, canon, v)
    logging.getLogger("dv").debug("Setting DV %s = %s", xcanon, v)

  if  (DVRouterBase._DVRouterBase__SPLIT_HORIZON
   and DVRouterBase._DVRouterBase__POISON_REVERSE):
    raise RuntimeError("You should not simultaneously enable both split "
                       + "horizon and poison reverse")
