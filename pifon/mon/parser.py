from __future__ import print_function
import sys

class Parser:
  
  def __init__(self, state):
    self.state = state
  
  def _warn(self, *args):
    print("parser?:",*args,file=sys.stderr)
    
  def audio_state(self,*args):
    if len(args) == 2:
      state = args[1]
      self.state.report_audio_state(state)
    else:
      self._warn(args);
    
  def audio_level(self,*args):
    if len(args) == 3:
      try:
        max_level = int(args[1])
        cur_level = int(args[2])
        self.state.report_audio_level(max_level, cur_level)
      except ValueError:
        self._warn(args)
    else:
      self._warn(args)
    
  def audio_pong(self,*args):
    if len(args) == 1:
      self.state.report_audio_pong()
    else:
      self._warn(args)
    
  def mute(self,*args):
    if len(args) == 1:
      self.state.execute_audio_mute(True,True)
    else:
      self._warn(args)
  
  def unmute(self,*args):
    if len(args) == 1:
      self.state.execute_audio_mute(False,True)
    else:
      self._warn(args)

  def listen(self,*args):
    if len(args) == 1:
      self.state.execute_audio_listen(True,True)
    else:
      self._warn(args)
  
  def unlisten(self,*args):
    if len(args) == 1:
      self.state.execute_audio_listen(False,True)
    else:
      self._warn(args)
  
  def connected(self,*args):
    if len(args) == 1:
      self.state.connected()
    else:
      self._warn(args)
    
  def disconnected(self,*args):
    if len(args) == 1:
      self.state.disconnected()
    else:
      self._warn(args)
  
  valid_commands = {
    'audio_state' : audio_state,
    'audio_level' : audio_level,
    'audio_pong' : audio_pong,
    'mute' : mute,
    'unmute' : unmute,
    'listen' : listen,
    'unlisten' : unlisten,
    'connected' : connected,
    'disconnected' : disconnected
  }
  
  def dispatch(self, args):
    if len(args) == 0:
      return False
    cmd = args[0]
    for a in self.valid_commands:
      if a == cmd:
        f = self.valid_commands[a]
        return f(self, *args)
    print("huh? ",args,file=sys.stderr)
    return False
