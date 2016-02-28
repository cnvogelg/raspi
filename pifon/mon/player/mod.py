#!/usr/bin/env python

from __future__ import print_function

from bot import Bot, BotCmd, BotOptField, BotMod
from bot.event import *

import worker
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
      PeerModListEvent(self.on_peer_modlist),
      PeerDisconnectEvent(self.on_peer_disconnected),
      StopEvent(self.on_stop),
      BotEvent("audio","active",callee=self.on_player_active,arg_types=(bool,)),
      BotEvent("audio","listen_url",callee=self.on_player_listen_url,arg_types=(str,)),
    ]
    self.audio_peers = []

  def setup(self, send, log, cfg, botopts):
    BotMod.setup(self, send, log, cfg, botopts)

    def_cfg = {
      'chime_start_sound' : 'sounds/prompt.wav',
      'chime_stop_sound' : 'sounds/finish.wav',
      'play_start_cmd' : '',
      'play_stop_cmd' : '',
      'chime_start_cmd' : 'play %s',
      'chime_stop_cmd' : 'play %s',
      'start_stream_cmd' : 'tools/stream_ssh %s',
      'stop_stream_cmd' : '',
      'play_chimes' : True,
      'start_muted' : False
    }
    cfg = cfg.get_section('player', def_cfg)
    self.log("player_cfg:", cfg)

    self.worker = worker.Worker()
    self.worker.set_chime_sound('start', cfg['chime_start_sound'])
    self.worker.set_chime_sound('stop', cfg['chime_stop_sound'])
    self.worker.set_command('play_start', cfg['play_start_cmd'])
    self.worker.set_command('play_stop', cfg['play_stop_cmd'])
    self.worker.set_command('chime_start', cfg['chime_start_cmd'])
    self.worker.set_command('chime_stop', cfg['chime_stop_cmd'])
    self.worker.set_command('start_stream', cfg['start_stream_cmd'])
    self.worker.set_command('stop_stream', cfg['stop_stream_cmd'])
    self.worker.set_play_chimes(cfg['play_chimes'])
    self.worker.set_callback('state', self._state_cb)
    self.worker.set_callback('error', self._error_cb)
    self.worker.set_callback('info', self._info_cb)

    start_muted = cfg['start_muted']
    self.control = control.Control(self, self.send_event, start_muted)

  def get_commands(self):
    return self.cmds

  def get_events(self):
    return self.events

  # --- commands ---

  def cmd_mute(self, sender):
    self.log("cmd_mute")
    self.control.mute()

  def cmd_monitor(self, sender):
    self.log("cmd_monitor")
    self.control.monitor()

  def cmd_listen(self, sender, args):
    url = args[0]
    self.log("cmd_listen", url)
    self.control.listen(url)

  def cmd_chime(self, sender, args):
    on = args[0]
    self.log("cmd_chime", on)
    self.worker.set_play_chimes(on)
    self._report_chime(None)

  def cmd_query_mode(self, sender):
    self.control.report_mode(sender)

  def cmd_query_chime(self, sender):
    self._report_chime([sender])

  def _report_chime(self, to):
    self.send_event(['chime',self.worker.get_play_chimes()],to)

  # --- events ---

  def on_stop(self):
    self.log("shutting down worker")
    self.worker.shutdown()
    self.log("done")

  def on_peer_modlist(self, peer, modlist):
    self.log("on_peer_modlist", peer, modlist)
    if 'audio' in modlist:
      self.audio_peers.append(peer)
      self.log("CONNECT", peer)
      self.control.audio_connect(peer)
      self.send_command(['audio', 'query_listen_url'], to=[peer])
      self.send_command(['audio', 'query_active'], to=[peer])

  def on_peer_disconnected(self, peer):
    if peer in self.audio_peers:
      self.log("DISCONNECT", peer)
      self.control.audio_disconnect(peer)
      self.audio_peers.remove(peer)

  def on_player_listen_url(self, sender, args):
    self.log("got player_listen_url", args)
    self.control.audio_src(sender, args[0])

  def on_player_active(self, sender, args):
    self.log("got player_active", sender, args)
    self.control.audio_active(sender, args[0])

  # --- callbacks from worker ---

  def _state_cb(self, worker, state):
    self.log("worker state:", state)

  def _error_cb(self, worker, context, cmd, error):
    self.log("ERROR: calling", context, "cmd=", cmd, "->", error)

  def _info_cb(self, worker, context, cmd):
    self.log("calling", context, "cmd=", cmd)

  # --- callbacks from control ---

  def play(self, url):
    self.log("play stream", url)
    self.worker.play(url)
    return True

  def stop(self):
    self.log("stop stream")
    self.worker.stop()
    return True

  def is_playing(self):
    isp = self.worker.is_playing()
    self.log("is_playing", isp)
    return isp
