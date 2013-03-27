from __future__ import print_function
import sys
import time

class State:
  """manage pifon mon application state"""
  ping_delay = 5 # in s
  
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
    self.is_pinging = False
    self.is_audio_active = False
    self.is_audio_muted = False
    self.is_audio_listen = False
    self.is_playing = False
    self.allow_chime = True
    self.allow_blank = True
    self.last_chime = False
  
  def set_control(self, control):
    self.control = control
  
  def set_player(self, player):
    self.player = player  
  
  def _log(self, *args):
    print("state:",*args,file=sys.stderr)
  
  def setup(self):
    """setup stat by querying state via bot"""
    self._log("setup")
    # query options and current state
    self.writer.send_query_audio()
    self.writer.send_audio_state()
    self.control.update_audio_state('offline', False, False)
  
  def _init_ping(self):
    self.last_ping_ts = 0
    self.ping_flag = False
    self.ping_complete = True
    self.pong_arrived = False
  
  def _handle_ping(self,t):
    if self.ping_complete:
      # check time for next ping
      delay = t - self.last_ping_ts
      if delay >= self.ping_delay:
        # send a new ping
        print("-> ping",file=sys.stderr)
        self.control.update_audio_ping(None)
        self.writer.send_audio_ping()
        self.ping_complete = False
        self.pong_arrived = False
        self.last_ping_ts = t
    else:
      # wait for ping
      delta = t - self.last_ping_ts
      if self.pong_arrived:
        self.ping_complete = True
        self.control.update_audio_ping(True)
        print("<- pong",delta,file=sys.stderr)
        if not self.is_pinging:
          self.is_pinging = True
          self.control.update_audio_state('online', False, True)
      else:
        # timeout ?
        if delta >= self.ping_delay:
          self.ping_complete = True
          self.control.update_audio_ping(False)
          print("?? pong",file=sys.stderr)
          if self.is_pinging:
            self.is_pinging = False
            self.control.update_audio_state('no ping', False, False)
  
  def handle(self):
    """do periodic tasks"""
    if self.is_connected:
      t = time.time()
      self._handle_ping(t)
        
  def connected(self):
    """connected event from bot"""
    self._log("connected")
    self.is_connected = True
    self.is_pinging = False
    self.control.update_audio_state('connect', False, False)
    self._init_ping()
    
  def disconnected(self):
    """disconnected event from bot"""
    self._log("disconnected")
    self.is_connected = False
    self.is_pinging = False
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
    self.pong_arrived = True
  
  def _update_my_state(self):
    self.control.update_mon_state(
      self.is_audio_muted, self.is_audio_listen,
      self.allow_chime, self.allow_blank)    
  
  def execute_audio_mute(self, on, from_bot):
    """execute mute/unmute either from bot or via control"""
    self._log("execute_mute",on,from_bot)
    if not from_bot:
      self.writer.send_audio_mute(on)
    self.is_audio_muted = on
    if on:
      self.is_audio_listen = False
    self._update_play_state()
    self._update_my_state()
  
  def execute_audio_listen(self, on, from_bot):
    """execute listen/unlisten audio from bot or via control"""
    self._log("execute_listen",on,from_bot)
    if not from_bot:
      self.writer.send_audio_listen(on)
    if on:
      self.is_audio_muted = False
    self.is_audio_listen = on
    self._update_play_state()
    self._update_my_state()
  
  def execute_audio_chime(self, on, from_bot):
    """execute chime/unchime audio from bot or via control"""
    self._log("execute_chime",on,from_bot)
    if not from_bot:
      self.writer.send_audio_chime(on)
    self.allow_chime = on
    self._update_my_state()
  
  def execute_blank(self, on, from_bot):
    """execute chime/unchime audio from bot or via control"""
    self._log("execute_chime",on,from_bot)
    if not from_bot:
      self.writer.send_blank(on)
    self.allow_blank = on
    self._update_my_state()
  
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
        self.player.stop(self.last_chime)
      else:
        # start player
        self.is_playing = True
        self.last_chime = self.is_audio_active and self.allow_chime
        self.player.start(self.last_chime)
      self.control.update_audio_play(self.is_playing)
