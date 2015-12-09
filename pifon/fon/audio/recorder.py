from __future__ import print_function
import subprocess
import os
import sys

class Recorder:
  def __init__(self, rate=11025, interval=1000, channels=1, recorder="auto"):
    cmd = ["tools/vumeter", str(rate), str(interval), str(channels), recorder]
    self.p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)

  def read_rms(self):
    """read the next rms value"""
    # process exit?
    if self.p.returncode != None:
      return None
    # read line
    line = self.p.stdout.readline().strip()
    try:
      items = line.split(" ")
      if len(items) == 2:
        items = map(int, items)
        return(items[0] / 1000, items[1])
      return None
    except:
      return None

  def stop(self):
    self.p.terminate()


# test
if __name__ == '__main__':
  r = Recorder()
  try:
    while True:
      rms = r.read_rms()
      if rms is None:
        break
      print(rms)
  except KeyboardInterrupt:
    pass
  r.stop()
