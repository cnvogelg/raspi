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
      # custom events
      BotEvent("audio", "level", arg_types=(int,int,int), callee=self.event_audio_level),
      BotEvent("audio", "state", arg_types=(str,), callee=self.event_audio_state),
      BotEvent("audio", "active", arg_types=(bool,), callee=self.event_audio_active),
      BotEvent("audio", "listen_src", arg_types=(str, str), callee=self.event_audio_listen_src),
      BotEvent("pinger", "check", arg_types=(str, str), callee=self.event_pinger_check),
      BotEvent("player", "play", arg_types=(str, str), callee=self.event_player_play),
      BotEvent("player", "stop", arg_types=(str,), callee=self.event_player_stop),
      BotEvent("player", "mode", arg_types=(str,str), callee=self.event_player_mode)
    ]
    self.audios = {}
    self.players = {}
    self.listener = listener
    self.tick = tick

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
      a = self._create_audio(peer)
      self.log("added audio from", peer)
      self._call('audio_add', a)
    elif mod_name == 'player':
      p = self._create_player(peer)
      self.log("added player from",peer)
      self._call('player_add', p)

  def on_tick(self, ts, delta):
    # forward to listener
    res = self._call('on_tick', ts, delta)
    # shutdown?
    if res == False:
      self.log("requesting shutdown on behalf of listener")
      self.bot.request_shutdown()

  # audio events

  def _create_audio(self, sender):
    a = AudioInfo(sender)
    self.audios[sender] = a
    return a

  def _get_audio(self, sender):
    if sender in self.audios:
      return self.audios[sender]
    else:
      return None

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
      self._call('audio_update', a, flags)

  def event_audio_active(self, sender, args):
    a = self._get_audio(sender)
    if a is not None:
      a.audio_active = args[0]
      self._call('audio_update', a, AudioInfo.FLAG_AUDIO_ACTIVE)

  def event_audio_listen_src(self, sender, args):
    a = self._get_audio(sender)
    if a is not None:
      a.audio_listen_src = args
      self._call('audio_update', a, AudioInfo.FLAG_AUDIO_LISTEN_SRC)

  def event_pinger_check(self, sender, args):
    peer = args[0]
    a = self._get_audio(peer)
    if a is not None:
      a.ping = args[1]
      self._call('audio_update', a, AudioInfo.FLAG_PING)

  # player events

  def _create_player(self, sender):
    p = PlayerInfo(sender)
    self.players[sender] = p
    return p

  def _get_player(self, sender):
    if sender in self.players:
      return self.players[sender]
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
      self._call('player_update', p, PlayerInfo.FLAG_MODE)
