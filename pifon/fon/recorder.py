from __future__ import print_function
import subprocess
import os
import sys

class Recorder:
  def __init__(self, rate=11025, interval=1000, channels=1):
    cmd = ["tools/vumeter", str(rate), str(interval), str(channels)]
    self.p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)

  def read_rms(self):
    """read the next rms value"""
    # process exit?
    if self.p.returncode != None:
      return None
    # read line
    l = self.p.stdout.readline()
    try:
      return int(l)
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
