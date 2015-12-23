from __future__ import print_function

import time

from bot import Bot, BotCmd, BotOptField, BotMod
from bot.event import *

class PingStatus:
  INIT = 0
  REQUESTED = 1
  ALIVE = 2
  TIMEOUT = 3

  NAMES = (
    "init",
    "requested",
    "alive",
    "timeout"
  )

  def __init__(self, ts):
    self.ts = ts
    self.state = self.INIT

  def set(self, ts, state):
    self.ts = ts
    self.state = state

  def get_state_name(self):
    return self.NAMES[self.state]


class PingerMod(BotMod):
  def __init__(self):
    BotMod.__init__(self, "pinger")
    self.cmds = [
      BotCmd("query",arg_types=(str,),callee=self.cmd_query)
    ]
    self.opts = [
      BotOptField("interval",int,10,desc="check interval for pings"),
    ]
    self.events = [
      BotEvent(BotEvent.MAIN,"pong",callee=self.event_pong),
      PeerConnectEvent(self.on_peer_connect),
      PeerDisconnectEvent(self.on_peer_disconnect),
      TickEvent(self.on_tick)
    ]
    self.ping_map = {}

  def on_peer_connect(self, peer):
    self.log("on_peer_connect",peer)
    # add peer to ping map
    ts = time.time()
    self.ping_map[peer] = PingStatus(ts)

  def on_peer_disconnect(self, peer):
    self.log("on_peer_disconnect",peer)
    # remove from ping map
    if peer in self.ping_map:
      del self.ping_map[peer]

  def on_tick(self, ts, delta):
    # check peer map
    interval = self.botopts.get_value('interval')
    for peer in self.ping_map:
      status = self.ping_map[peer]
      state = status.state
      if state == PingStatus.INIT:
        # send initial ping
        self._send_ping(peer)
        status.set(ts, PingStatus.REQUESTED)
        self._report_peer_status(peer, status)
      else:
        # check for time out
        delta = ts - status.ts
        if delta >= interval:
          # timeout after request
          if state == PingStatus.REQUESTED:
            status.set(ts, PingStatus.TIMEOUT)
            self._report_peer_status(peer, status)
          # retry after alive/timeout
          elif state in (PingStatus.ALIVE, PingStatus.TIMEOUT):
            self._send_ping(peer)
            status.set(ts, PingStatus.REQUESTED)
            self._report_peer_status(peer, status)

  def event_pong(self, sender):
    # an incoming pong sets alive state
    if sender in self.ping_map:
      status = self.ping_map[sender]
      ts = time.time()
      status.set(ts, PingStatus.ALIVE)
      self._report_peer_status(sender, status)

  def _send_ping(self, to):
    self.reply(["ping"], to=[to], main=True)

  def _report_peer_status(self, peer, status, to=None):
    name = status.get_state_name()
    self.reply(["check", peer, name], to=to)
    self.log("check", peer, name)

  def cmd_query(self, sender, args):
    peer = args[0]
    if peer in self.ping_map:
      status = self.ping_map[peer]
      self._report_peer_status(peer, status, to=[sender])

  def get_commands(self):
    return self.cmds

  def get_opts(self):
    return self.opts

  def get_events(self):
    return self.events

  def get_tick_interval(self):
    return 1
