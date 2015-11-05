import subprocess
import sys

class PlayerMPV:
  def __init__(self, mpv=None):
    if mpv is not None:
      self.mpv = mpv
    else:
      if sys.platform.startswith('linux'):
        self.mpv = '/usr/bin/mpv'
      elif sys.platform == 'darwin':
        self.mpv = '/opt/local/bin/mpv'
      else:
        raise RuntimeError("unsupported system")

  def play_chime(self, url):
    null = open('/dev/null','w')
    ret = subprocess.call([self.mpv, url], stdout=null, stderr=null)
    null.close()
    return ret == 0

  def play(self, url):
    self.null = open('/dev/null','w')
    self.p = subprocess.Popen([self.mpv, url], stdout=self.null, stderr=self.null)

  def stop(self):
    self.p.kill()
    self.p.wait()
    self.null.close()
    return self.p.returncode == 0

# ----- Test -----
if __name__ == '__main__':
  import time
  p = PlayerMPV()
  p.play_chime('../sounds/prompt.wav')
  print("play")
  p.play('http://pifon.local:8000/pifon')
  time.sleep(2)
  p.stop()
  p.play_chime('../sounds/finish.wav')
