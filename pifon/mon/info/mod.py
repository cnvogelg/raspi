from __future__ import print_function

import time

from bot import Bot, BotCmd, BotOptField, BotMod
from bot.event import *

from audioinfo import AudioInfo
from playerinfo import PlayerInfo

class InfoMod(BotMod):
  def __init__(self, name="info", listener=None, tick=1):
    BotMod.__init__(self, name)
    self.events = [
      ConnectEvent(self.on_connect),
      DisconnectEvent(self.on_disconnect),
      PeerConnectEvent(self.on_peer_connect),
      PeerDisconnectEvent(self.on_peer_disconnect),
      ModListEvent(self.on_modlist),
      PeerModListEvent(self.on_peer_modlist),
      TickEvent(self.on_tick),
      StartEvent(self.on_start),
      StopEvent(self.on_stop),
      # custom events
      BotEvent("audio", "level", arg_types=(int,int,int), callee=self.event_audio_level),
      BotEvent("audio", "state", arg_types=(str,), callee=self.event_audio_state),
      BotEvent("audio", "active", arg_types=(bool,), callee=self.event_audio_active),
      BotEvent("audio", "listen_url", arg_types=(str,), callee=self.event_audio_listen_url),
      BotEvent("audio", "location", arg_types=(str,), callee=self.event_audio_location),
      BotEvent("pinger", "check", arg_types=(str, str), callee=self.event_pinger_check),
      BotEvent("player", "play", arg_types=(str, str), callee=self.event_player_play),
      BotEvent("player", "stop", arg_types=(str,), callee=self.event_player_stop),
      BotEvent("player", "mode", arg_types=(str,str), callee=self.event_player_mode),
      BotEvent("player", "chime", arg_types=(bool,), callee=self.event_player_chime)
    ]
    self.audios = {}
    self.pending_audios = {}
    self.players = {}
    self.pending_players = {}
    self.listener = listener
    self.tick = tick
    self.ping_lost = []
    self.non_idle_audios = []
    self.primary_non_idle_audio = None
    self.active_audios = []
    self.primary_active_audio = None

  def get_events(self):
    return self.events

  def get_tick_interval(self):
    return self.tick

  def _call(self, name, *args):
    # no listener
    if self.listener is None:
      self.log("call", name, *args)
      return None
    # check if listener has method
    if hasattr(self.listener, name):
      func = getattr(self.listener, name)
      return func(*args)
    else:
      self.log("call", name, *args)
      return None

  def on_start(self):
    self._call('on_start', self.nick)

  def on_stop(self):
    self._call('on_stop', self.nick)

  def on_connect(self):
    self._call('on_connect')

  def on_disconnect(self):
    self._call('on_disconnect')

  def on_peer_connect(self, peer):
    self.log("on_peer_connect", peer)

  def on_peer_disconnect(self, peer):
    self.log("on_peer_disconnect", peer)
    if peer in self.audios:
      a = self.audios[peer]
      self._call("audio_del",a)
      del self.audios[peer]
      self._remove_ping(a)
      self._remove_non_idle(a)
    if peer in self.players:
      p = self.players[peer]
      self._call("player_del",p)

  def on_peer_modlist(self, sender, modlist):
    self.log("on_peer_modlist", sender, modlist)
    for mod in modlist:
      self._add_mod(mod, sender)

  def on_modlist(self, my_modlist):
    self.log("on_modlist", my_modlist)
    for mod in my_modlist:
      self._add_mod(mod, self.nick)

  def _add_mod(self, mod_name, peer):
    if mod_name == 'audio':
      a = self._create_pending_audio(peer)
      self.log("added audio from", peer)
      # request state
      self.send_command(['audio','query_state'],to=[peer])
      self.send_command(['audio','query_active'],to=[peer])
      self.send_command(['audio','query_listen_url'],to=[peer])
      self.send_command(['audio','query_location'],to=[peer])
    elif mod_name == 'player':
      p = self._create_pending_player(peer)
      self.log("added player from",peer)
      # request mode
      self.send_command(['player','query_mode'],to=[peer])
      self.send_command(['player','query_chime'],to=[peer])

  def on_tick(self, ts, delta):
    # forward to listener
    res = self._call('on_tick', ts, delta)
    # shutdown?
    if res == False:
      self.log("requesting shutdown on behalf of listener")
      self.bot.request_shutdown()

  # audio events

  def _create_pending_audio(self, sender):
    a = AudioInfo(sender)
    self.pending_audios[sender] = a
    return a

  def _make_audio_live(self, a):
    if a.is_ready():
      sender = a.name
      if sender in self.pending_audios:
        del self.pending_audios[sender]
        self.audios[sender] = a
        self.log("audio going -- LIVE --",sender)
        self._call('audio_add', a)
        self._check_ping(a)
        if a.audio_state != 'idle':
          self._add_non_idle(a)
        if a.audio_active:
          self._add_active(a)
        return True
      else:
        return False

  def _get_audio(self, sender):
    if sender in self.audios:
      return self.audios[sender]
    elif sender in self.pending_audios:
      return self.pending_audios[sender]
    else:
      return None

  def _update_audio(self, a, flags):
    if not self._make_audio_live(a):
      self._call('audio_update', a, flags)
    if flags & AudioInfo.FLAG_PING:
      self._check_ping(a)

  def _check_ping(self, a):
    if a.ping == "timeout":
      self.ping_lost.append(a)
      change = True
    elif a.ping == "alive" and a in self.ping_lost:
      self.ping_lost.remove(a)
      change = True
    else:
      change = False
    if change:
      self._call('ping_lost_update', self.ping_lost)

  def _remove_ping(self, a):
    if a in self.ping_lost:
      self.ping_lost.remove(a)

  def _add_non_idle(self, a):
    if a not in self.non_idle_audios:
      self.non_idle_audios.append(a)
      if len(self.non_idle_audios) == 1:
        self.primary_non_idle_audio = a
      self._call('non_idle_audio_update', self.non_idle_audios, self.primary_non_idle_audio)

  def _remove_non_idle(self, a):
    if a in self.non_idle_audios:
      self.non_idle_audios.remove(a)
      if a == self.primary_non_idle_audio:
        if len(self.non_idle_audios) > 0:
          self.primary_non_idle_audio = self.non_idle_audios[0]
        else:
          self.primary_non_idle_audio = None
      self._call('non_idle_audio_update', self.non_idle_audios, self.primary_non_idle_audio)

  def _add_active(self, a):
    if a not in self.active_audios:
      self.active_audios.append(a)
      if len(self.active_audios) == 1:
        self.primary_active_audio = a
      self._call('active_audio_update', self.active_audios, self.primary_active_audio)

  def _remove_active(self, a):
    if a in self.active_audios:
      self.active_audios.remove(a)
      if a == self.primary_active_audio:
        if len(self.active_audios) > 0:
          self.primary_active_audio = self.active_audios[0]
        else:
          self.primary_active_audio = None
      self._call('active_audio_update', self.active_audios, self.primary_active_audio)

  def event_audio_level(self, sender, args):
    a = self._get_audio(sender)
    if a is not None:
      a.audio_level = args
      self._call('audio_update', a, AudioInfo.FLAG_AUDIO_LEVEL)

  def event_audio_state(self, sender, args):
    a = self._get_audio(sender)
    if a is not None:
      state = args[0]
      flags = AudioInfo.FLAG_AUDIO_STATE
      a.audio_state = state
      if state == 'idle':
        a.audio_level = None
        flags |= AudioInfo.FLAG_AUDIO_LEVEL
        self._remove_non_idle(a)
      else:
        self._add_non_idle(a)
      # handle active
      if a.audio_active:
        self._add_active(a)
      else:
        self._remove_active(a)
      # push update
      self._update_audio(a, flags)

  def event_audio_active(self, sender, args):
    a = self._get_audio(sender)
    if a is not None:
      a.audio_active = args[0]
      self._update_audio(a, AudioInfo.FLAG_AUDIO_ACTIVE)

  def event_audio_listen_url(self, sender, args):
    a = self._get_audio(sender)
    if a is not None:
      a.audio_listen_url = args[0]
      self._update_audio(a, AudioInfo.FLAG_AUDIO_LISTEN_URL)

  def event_audio_location(self, sender, args):
    a = self._get_audio(sender)
    if a is not None:
      a.audio_location = args[0]
      self._update_audio(a, AudioInfo.FLAG_AUDIO_LOCATION)

  def event_pinger_check(self, sender, args):
    peer = args[0]
    a = self._get_audio(peer)
    if a is not None:
      a.ping = args[1]
      self._update_audio(a, AudioInfo.FLAG_PING)

  # player events

  def _create_pending_player(self, sender):
    p = PlayerInfo(sender)
    self.pending_players[sender] = p
    return p

  def _make_player_live(self, p):
    if p.is_ready():
      sender = p.name
      if sender in self.pending_players:
        del self.pending_players[sender]
        self.players[sender] = p
        self.log("player going -- LIVE --",sender)
        self._call('player_add', p)
        return True
    return False

  def _get_player(self, sender):
    if sender in self.players:
      return self.players[sender]
    elif sender in self.pending_players:
      return self.pending_players[sender]
    else:
      return None

  def event_player_play(self, sender, args):
    audio = args[0]
    a = self._get_audio(audio)
    p = self._get_player(sender)
    if a is not None:
      a.is_playing = True
      self._call('audio_update', a, AudioInfo.FLAG_IS_PLAYING)
    if p is not None:
      p.play_server = a
      self._call('player_update', p, PlayerInfo.FLAG_PLAY_SERVER)

  def event_player_stop(self, sender, args):
    audio = args[0]
    a = self._get_audio(audio)
    p = self._get_player(sender)
    if a is not None:
      a.is_playing = False
      self._call('audio_update', a, AudioInfo.FLAG_IS_PLAYING)
    if p is not None and a is not None:
      p.play_server = None
      self._call('player_update', p, PlayerInfo.FLAG_PLAY_SERVER)

  def event_player_mode(self, sender, args):
    p = self._get_player(sender)
    if p is not None:
      p.mode = args[0]
      if not self._make_player_live(p):
        self._call('player_update', p, PlayerInfo.FLAG_MODE)

  def event_player_chime(self, sender, args):
    p = self._get_player(sender)
    if p is not None:
      p.chime = args[0]
      if not self._make_player_live(p):
        self._call('player_update', p, PlayerInfo.FLAG_CHIME)
