from __future__ import print_function
import sys
import subprocess

class AudioPlay:
  def __init__(self):
    self.is_playing = False
    self.last_error = None
    self.cfg = {
      'reset':None,
      'init':None,
      'start':None,
      'stop':None,
      'player':None,
      'start_sound':None,
      'stop_sound':None
    }
  
  def _run(self, cmd):
    print("player:",cmd,file=sys.stderr)
    result=subprocess.call(cmd,shell=True,stdout=open('/dev/null','w'))
    if result != 0:
      self.last_error = result
    print("result:",result,file=sys.stderr)
    return result == 0
    
  def get_last_error(self):
    return self.last_error
  
  def set_option(self, key, value):
    if key in self.cfg:
      self.cfg[key] = value
  
  def setup(self):
    """initialize external player to start playing"""
    cmd = self.cfg['reset']
    if cmd != None:
      if not self._run(cmd):
        return False
    cmd = self.cfg['init']
    if cmd != None:
      return self._run(cmd)
    else:
      return True

  def start(self, use_signals):
    """start playing"""
    if self.is_playing:
      return False
    # play sound?
    player = self.cfg['player']
    sound = self.cfg['start_sound']
    if player and sound and use_signals:
      ok = self._run(player + " " + sound)
      if not ok:
        return False
    # start streaming
    start = self.cfg['start']
    if start:
      ok = self._run(start)
    self.is_playing = ok
    return ok

  def stop(self, use_signals):
    if not self.is_playing:
      return False
    self.is_playing = False
    # stop streaming
    stop = self.cfg['stop']
    if stop:
      ok = self._run(stop)
      if not ok:
        return False
    # play sound?
    player = self.cfg['player']
    sound = self.cfg['stop_sound']
    if player and sound and use_signals:
      ok = self._run(player + " " + sound)
      return ok
    else:
      return True
