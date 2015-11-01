import subprocess

class Recorder:
  def __init__(self):
    cmd = ["tools/vumeter"]
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

# test
if __name__ == '__main__':
  r = Recorder()
  while True:
    rms = r.read_rms()
    if rms is None:
      break
    print(rms)
