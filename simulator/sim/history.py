import sim.boot
import os
import sys

def launch (filename=None):
  """
  Saves history from the Python interpreter across sessions
  """
  if filename is None:
    filename = "sim.history"
    if sys.platform != "darwin":
      filename = "." + filename

  if os.path.splitext(filename)[1] != ".history":
    filename += ".history"

  sim.boot.history_file = filename
