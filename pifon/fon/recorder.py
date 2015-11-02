from __future__ import print_function
import subprocess
import os
import sys

class Recorder:
  rate_file = "~/.sample_rate"

  def __init__(self):
    rate = self._get_rate()
    if rate is None:
      print("No rate file '%s'! Using default..." % self.rate_file, file=sys.stderr)
      rate = 22050
    cmd = ["tools/vumeter", str(rate)]
    self.p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)

  def _get_rate(self):
    # try to get sample rate
    try:
      rate_file = os.path.expanduser(self.rate_file)
      if os.path.exists(rate_file):
        fh = open(rate_file)
        l = fh.readline()
        l = l.strip()
        rate = int(l)
        fh.close()
        return rate
    except:
      pass
    return None

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

# test
if __name__ == '__main__':
  r = Recorder()
  while True:
    rms = r.read_rms()
    if rms is None:
      break
    print(rms)
