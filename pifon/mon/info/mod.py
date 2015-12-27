from __future__ import print_function

import time

from bot import Bot, BotCmd, BotOptField, BotMod
from bot.event import *

class AudioInfo:

  FLAG_PING = 1
  FLAG_AUDIO_LEVEL = 2
  FLAG_AUDIO_STATE = 4
  FLAG_AUDIO_ACTIVE = 8
  FLAG_AUDIO_LISTEN_SRC = 16
  FLAG_IS_PLAYING = 32

  def __init__(self, name):
    self.name = name
    self.ping = None
    self.audio_level = None
    self.audio_state = None
    self.audio_active = None
    self.audio_listen_src = None
    self.is_playing = False

  def __repr__(self):
    return "[%s:ping=%s,audio=(%s,%s,%s,%s)],play=%s" % (self.name,
      self.ping,
      self.audio_level, self.audio_state, self.audio_active,
      self.audio_listen_src,
      self.is_playing)


class PlayerInfo:

  FLAG_PLAY_SERVER = 1
  FLAG_MODE = 2

  def __init__(self, name):
    self.name = name
    self.play_server = None
    self.mode = None

  def __repr__(self):
    return "<%s:play:%s:%s>" % (self.name,
      self.play_server, self.mode)


class ServerInfoMod(BotMod):
  def __init__(self, listener=None, tick=1):
    BotMod.__init__(self, "info")
    self.events = [
      ConnectEvent(self.on_connect),
      DisconnectEvent(self.on_disconnect),
      PeerConnectEvent(self.on_peer_connect),
      PeerDisconnectEvent(self.on_peer_disconnect),
      TickEvent(self.on_tick),
      # custom events
      BotEvent("audio", "level", arg_types=(int,int,int), callee=self.event_audio_level),
      BotEvent("audio", "state", arg_types=(str,), callee=self.event_audio_state),
      BotEvent("audio", "active", arg_types=(str,), callee=self.event_audio_active),
      BotEvent("audio", "listen_src", arg_types=(str, str), callee=self.event_audio_listen_src),
      BotEvent("pinger", "check", arg_types=(str, str), callee=self.event_pinger_check),
      BotEvent("player", "play", arg_types=(str, str), callee=self.event_player_play),
      BotEvent("player", "stop", arg_types=(str,), callee=self.event_player_stop),
      BotEvent("player", "mode", arg_types=(str,str), callee=self.event_player_mode)
    ]
    self.servers = {}
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
      return
    # check if listener has method
    if hasattr(self.listener, name):
      func = self.listener.getattr(name)
      func(*args)
    else:
      self.log("call", name, *args)
      return

  def on_connect(self):
    self._call('on_connect')

  def on_disconnect(self):
    self._call('on_disconnect')

  def on_peer_connect(self, peer):
    pass

  def on_peer_disconnect(self, peer):
    if peer in self.servers:
      si = self.servers[peer]
      self._call("gone_audio",si)
      del self.servers[peer]
    if peer in self.players:
      p = self.players[peer]
      self._call("gone_player",p)

  def on_tick(self, ts, delta):
    # forward to listener
    self._call('on_tick', ts, delta)

  # audio events

  def _get_audio(self, sender):
    if sender in self.servers:
      si = self.servers[sender]
    else:
      si = AudioInfo(sender)
      self.servers[sender] = si
    return si

  def event_audio_level(self, sender, args):
    si = self._get_audio(sender)
    si.audio_level = args
    self._call('update_audio', si, AudioInfo.FLAG_AUDIO_LEVEL)

  def event_audio_state(self, sender, args):
    si = self._get_audio(sender)
    si.audio_state = args[0]
    self._call('update_audio', si, AudioInfo.FLAG_AUDIO_STATE)

  def event_audio_active(self, sender, args):
    si = self._get_audio(sender)
    si.audio_active = args[0]
    self._call('update_audio', si, AudioInfo.FLAG_AUDIO_ACTIVE)

  def event_audio_listen_src(self, sender, args):
    si = self._get_audio(sender)
    si.audio_listen_src = args
    self._call('update_audio', si, AudioInfo.FLAG_AUDIO_LISTEN_SRC)

  def event_pinger_check(self, sender, args):
    peer = args[0]
    si = self._get_audio(sender)
    si.ping = args[1]
    self._call('update_audio', si, AudioInfo.FLAG_PING)

  # player events

  def _get_player(self, sender):
    if sender not in self.players:
      p = PlayerInfo(sender)
      self.players[sender] = p
    else:
      p = self.players[sender]
    return p

  def _get_si_player(self, sender, peer):
    if peer in self.servers:
      si = self.servers[peer]
      p = self._get_player(sender)
      # find player
      return (si, p)
    else:
      return None

  def event_player_play(self, sender, args):
    sip = self._get_si_player(sender, args[0])
    if sip is not None:
      si = sip[0]
      p = sip[1]
      si.is_playing = True
      p.play_server = si
      self._call('update_player', p, si, PlayerInfo.FLAG_PLAY_SERVER)

  def event_player_stop(self, sender, args):
    sip = self._get_si_player(sender, args[0])
    if sip is not None:
      si = sip[0]
      p = sip[1]
      si.is_playing = True
      p.play_server = None
      self._call('update_player', p, si, PlayerInfo.FLAG_PLAY_SERVER)

  def event_player_mode(self, sender, args):
    p = self._get_player(sender)
    p.mode = args[0]
    self._call('update_player', p, None, PlayerInfo.FLAG_MODE)
