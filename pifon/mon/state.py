from __future__ import print_function
import sys

class State:
  """manage pifon mon application state"""
  
  def __init__(self, writer):
    self.writer = writer
    self.control = None
    self.player = None
    # state
    self.audio_options = {
      'trace' : 0,
      'level' : 0,
      'update' : 0,
      'silence' : 0
    }
    self.is_connected = False
    self.is_audio_active = False
    self.is_audio_muted = False
    self.is_audio_forced = False
    self.is_playing = False
    self.use_signals = False
  
  def set_control(self, control):
    self.control = control
  
  def set_player(self, player):
    self.player = player  
  
  def _log(self, *args):
    print("state:",*args,file=sys.stderr)
  
  def setup(self):
    """setup stat by querying state via bot"""
    self._log("setup")
    self.writer.send_query_audio()
  
  def connected(self):
    """connected event from bot"""
    self._log("connected")
    self.is_connected = True
    self.control.update_connected(True)
    
  def disconnected(self):
    """disconnected event from bot"""
    self._log("disconnected")
    self.is_connected = False
    self.control.update_connected(False)
    
  def report_audio_begin(self, value):
    """incoming audio begin event from bot"""
    self._log("report_audio_begin",value)
    self.is_audio_active = True
    self.control.update_audio_active(True)
    self._update_play_state()
    self.control.update_audio_value(value)
    
  def report_audio_update(self, value):
    """incoming audio update event from bot"""
    self._log("report_audio_update",value)
    if not self.is_audio_active:
      self.is_audio_active = True
      self.control.update_audio_active(True)
      self._update_play_state()
    self.control.update_audio_value(value)
  
  def report_audio_end(self, value):
    """incoming audio end event from bot"""
    self._log("report_audio_end",value)
    self.control.update_audio_value(None)
    self.is_audio_active = False
    self.control.update_audio_active(False)
    self._update_play_state()
  
  def execute_audio_mute(self, on, from_bot):
    """execute mute/unmute either from bot or via control"""
    self._log("execute_mute",on,from_bot)
    if not from_bot:
      self.writer.send_audio_mute(on)
    self.is_audio_muted = on
    if on:
      self.is_audio_forced = False
    self._update_play_state()
    self.control.update_audio_override(self.is_audio_muted, self.is_audio_forced)
  
  def execute_audio_force(self, on, from_bot):
    """execute force/unforce audio from bot or via control"""
    self._log("execute_force",on,from_bot)
    if not from_bot:
      self.writer.send_audio_force(on)
    if on:
      self.is_audio_muted = False
    self.is_audio_forced = on
    self._update_play_state()
    self.control.update_audio_override(self.is_audio_muted, self.is_audio_forced)
  
  def set_audio_option(self, key, value, from_bot):
    """set an audio option either from bot or via control"""
    self._log("set_audio_option",key,value,from_bot)
    if key in self.audio_options:
      self.audio_options[key] = value
      if from_bot:
        self.control.update_audio_option(key, value)
      else:
        self.writer.send_audio_option(key, value)

  def _update_play_state(self):
    """check player state"""
    shall_play = self.is_audio_active
    if self.is_audio_muted:
      shall_play = False
    if self.is_audio_forced:
      shall_play = True
    self._log("play state: is=",self.is_playing," shall=",shall_play)
    if self.is_playing != shall_play:
      if self.is_playing:
        # stop player
        self.is_playing = False
        self.player.stop(self.use_signals)
      else:
        # start player
        self.is_playing = True
        self.use_signals = self.is_audio_active
        self.player.start(self.use_signals)
      self.control.update_audio_play(self.is_playing)
