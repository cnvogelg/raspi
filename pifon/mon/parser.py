from __future__ import print_function
import sys

class Parser:
  
  def __init__(self, state):
    self.state = state
  
  def _warn(self, *args):
    print("parser?:",*args,file=sys.stderr)
    
  def audio_begin(self,*args):
    if len(args) == 2:
      value = int(args[1])
      self.state.report_audio_begin(value)
    else:
      self._warn(args);
    
  def audio_update(self,*args):
    if len(args) == 2:
      value = int(args[1])
      self.state.report_audio_update(value)
    else:
      self._warn(args)
    
  def audio_end(self,*args):
    if len(args) == 2:
      value = int(args[1])
      self.state.report_audio_end(value)
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

  def force(self,*args):
    if len(args) == 1:
      self.state.execute_audio_force(True,True)
    else:
      self._warn(args)
  
  def unforce(self,*args):
    if len(args) == 1:
      self.state.execute_audio_force(False,True)
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
    'audio_begin' : audio_begin,
    'audio_update' : audio_update,
    'audio_end' : audio_end,
    'mute' : mute,
    'unmute' : unmute,
    'force' : force,
    'unforce' : unforce,
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
