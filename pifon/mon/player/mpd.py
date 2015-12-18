import subprocess
import sys
import os

from base import BasePlayer

class PlayerMPD(BasePlayer):
  def __init__(self, mpc=None, host=None):
    BasePlayer.__init__(self)
    # setup mpc binary
    if mpc is not None:
      self.mpc = mpc
    else:
      if sys.platform.startswith('linux'):
        self.mpc = '/usr/bin/mpc'
      elif sys.platform == 'darwin':
        self.mpc = '/opt/local/bin/mpc'
      else:
        raise RuntimeError("unsupported system")
    # host where mpd runs
    if host is not None:
      self.host = host
    else:
      self.host = 'localhost'
    # command
    self.cmd = [self.mpc, '-h', self.host]

  def _run_mpc(self, args):
    cmd = self.cmd + args
    null = open('/dev/null','w')
    result=subprocess.call(cmd, stdout=null)
    null.close()
    return result

  def _clear_add_play(self, url):
    # clear playlist
    ret = self._run_mpc(['clear'])
    if ret != 0:
      return False
    # add url to playlist
    ret = self._run_mpc(['add', url])
    if ret != 0:
      return False
    # start play
    ret = self._run_mpc(['play'])
    if ret != 0:
      return False
    else:
      return True

  def play_chime(self, url):
    base = os.path.basename(url)
    ok = self._clear_add_play(base)
    # wait for playback
    self._run_mpc(['current', '--wait'])
    return ok

  def play(self, url):
    return self._clear_add_play(url)

  def stop(self):
    ret = self._run_mpc(['stop'])
    if ret != 0:
      return False
    else:
      return True

# ----- Test -----
if __name__ == '__main__':
  import time
  p = PlayerMPD(host='pimon')
  p.play_chime('prompt.wav')
  print("play")
  p.play('http://pifon.local:8000/pifon')
  time.sleep(2)
  p.stop()

