#!/usr/bin/env python

from __future__ import print_function

from bot import Bot, BotCmd, BotOptField, BotMod
from bot.event import *

import create
import control

class PlayerMod(BotMod):
  def __init__(self):
    BotMod.__init__(self, "player")
    self.cmds = [
      BotCmd("mute",callee=self.cmd_mute),
      BotCmd("monitor",callee=self.cmd_monitor),
      BotCmd("listen",callee=self.cmd_listen,arg_types=(str,)),
      BotCmd("chime",callee=self.cmd_chime,arg_types=(bool,)),
      BotCmd("query_mode",callee=self.cmd_query_mode),
      BotCmd("query_chime",callee=self.cmd_query_chime)
    ]
    self.events = [
      PeerConnectEvent(self.on_peer_connected),
      PeerDisconnectEvent(self.on_peer_disconnected),
      BotEvent("audio","active",callee=self.on_player_active,arg_types=(bool,)),
      BotEvent("audio","listen_src",callee=self.on_player_listen_src,arg_types=(str,str)),
    ]

  def setup(self, send, log, cfg, botopts):
    BotMod.setup(self, send, log, cfg, botopts)

    def_cfg = {
      'name' : 'dummy',
      'mpc' : '/usr/bin/mpc',
      'host' : 'localhost',
      'mpv' : '/usr/bin/mpv',
      'chime_start' : 'sounds/prompt.wav',
      'chime_stop' : 'sounds/finish.wav'
    }
    self.log("player_cfg:", def_cfg)
    player_cfg = cfg.get_section('player', def_cfg)

    self.player = create.create_player(**player_cfg)
    self.control = control.Control(self.player, self.send_event)

  def get_commands(self):
    return self.cmds

  def get_events(self):
    return self.events

  # --- commands ---

  def cmd_mute(self, sender):
    self.control.mute()

  def cmd_monitor(self, sender):
    self.control.monitor()

  def cmd_listen(self, sender, args):
    self.control.listen(args[0])

  def cmd_chime(self, sender, args):
    self.player.set_allow_chimes(args[0])
    self._report_chime(None)

  def cmd_query_mode(self, sender):
    self.control.report_mode(sender)

  def cmd_query_chime(self, sender):
    self._report_chime([sender])

  def _report_chime(self, to):
    self.send_event(['chime',self.player.get_allow_chimes()],to)

  # --- events ---

  def on_peer_connected(self, peer):
    if peer.startswith('audio@'):
      self.log("CONNECT", peer)
      self.control.audio_connect(peer)

  def on_peer_disconnected(self, peer):
    if peer.startswith('audio@'):
      self.log("DISCONNECT", peer)
      self.control.audio_disconnect(peer)

  def on_player_listen_src(self, sender, args):
    self.log("player_listen_src", args)
    self.control.audio_src(sender, args[1])

  def on_player_active(self, sender, args):
    self.log("player_active", sender, args)
    self.control.audio_active(sender, args[0])
