from __future__ import print_function
import subprocess
import os
import sys

class Recorder:
  def __init__(self, rate=48000, interval=250, channels=1, recorder="rec",
               device="mixin", tool="tools/vumeter",
               zero_range=0, sox_filter="highpass 500"):
    if not os.path.isfile(tool):
      raise ValueError("Given tool script '%s' not found!" % tool)
    cmd = [tool, str(rate), str(interval), str(channels), recorder, device, str(zero_range), sox_filter]
    self.line_size = 0 # 12 # fixed size of rms output
    self.p = subprocess.Popen(cmd, bufsize=self.line_size, shell=False, stdout=subprocess.PIPE)

  def read_rms(self):
    """read the next rms value"""
    # process exit?
    if self.p.returncode != None:
      return None
    # read line
    stdout = self.p.stdout
    if self.line_size == 0:
      line = stdout.readline()
    else:
      line = stdout.read(self.line_size)
    line = line.strip()
    try:
      items = line.split(" ")
      if len(items) == 2:
        return map(int, items)
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
