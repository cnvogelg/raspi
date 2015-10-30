import os
import subprocess
import sys

class Recorder:

  def __init__(self):
    self.env = dict(os.environ)
    if sys.platform == 'darwin':
      self.rec_bin = '/opt/local/bin/rec'
    else:
      self.rec_bin = '/usr/bin/rec'
      # setup env for SoX
      self.env['AUDIODRIVER'] = 'alsa'
      self.env['AUDIODEV'] = 'mixin'
    self.channels = 1
    self.rate = 16000
    self.bits = 16

  def _get_cmd(self):
    cmd = [self.rec_bin, '-q', '-c', str(self.channels), '-r', str(self.rate), '-b', str(self.bits), '-t', 'raw', '-']
    # filters
    cmd += [ 'highpass', '500' ]
    return cmd

  def start(self, bufsize=1024):
    """run the audio recording tool in a seperate process and receive its samples
       via stdout pipe.
       the passed handler will be called for each received sample buffer
    """
    # start rec
    cmd = self._get_cmd()
    self.p = subprocess.Popen(cmd, shell=False, bufsize=bufsize, stdout=subprocess.PIPE, env=self.env)

  def read_buf(self, bufsize=1024):
    """read the next buffer
       return None if no buffer was receved, False on end
    """
    # process exit?
    if self.p.returncode != None:
      return False
    data = self.p.stdout.read(bufsize)
    if len(data) > 0:
      return data
    else:
      return None

