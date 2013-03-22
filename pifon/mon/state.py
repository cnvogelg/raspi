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
    self.is_audio_listen = False
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
    self.control.update_audio_state('offline', False, False)
  
  def connected(self):
    """connected event from bot"""
    self._log("connected")
    self.is_connected = True
    self.control.update_audio_state('online', False, True)
    
  def disconnected(self):
    """disconnected event from bot"""
    self._log("disconnected")
    self.is_connected = False
    self.control.update_audio_state('offline', False, False)
    
  def report_audio_state(self, state):
    """incoming audio state update from bot"""
    self._log("report_audio_state",state)
    self.is_audio_active = (state in ('active', 'sustain'))
    self.control.update_audio_state(state, self.is_audio_active, self.is_connected)
    self._update_play_state()
    
  def report_audio_level(self, max_level, cur_level):
    """incoming audio level from bot"""
    self._log("report_audio_level",max_level,cur_level)
    self.control.update_audio_level(max_level,cur_level)
  
  def report_audio_pong(self):
    """incoming audio pong reply for ping request"""
    self._log("report_audio_pong",value)
  
  def execute_audio_mute(self, on, from_bot):
    """execute mute/unmute either from bot or via control"""
    self._log("execute_mute",on,from_bot)
    if not from_bot:
      self.writer.send_audio_mute(on)
    self.is_audio_muted = on
    if on:
      self.is_audio_listen = False
    self._update_play_state()
    self.control.update_audio_override(self.is_audio_muted, self.is_audio_listen)
  
  def execute_audio_listen(self, on, from_bot):
    """execute listen/unlisten audio from bot or via control"""
    self._log("execute_force",on,from_bot)
    if not from_bot:
      self.writer.send_audio_listen(on)
    if on:
      self.is_audio_muted = False
    self.is_audio_listen = on
    self._update_play_state()
    self.control.update_audio_override(self.is_audio_muted, self.is_audio_listen)
  
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
    if self.is_audio_listen:
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
