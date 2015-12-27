#!/usr/bin/env python

from __future__ import print_function
import time

class AudioInstance:
  """an audio server instance"""
  def __init__(self, name):
    self.name = name
    self.state = None
    self.level = None
    self.max_level = None
    self.state_ts = None
    self.level_ts = None
    self.got_ping = True
    self.ping_ts = 0
    self.src_name = None
    self.listen_url = None
    self.src_ts = None
    self.opts = None

  def __str__(self):
    return "[%s,%s,%s,%s,%s,%s,%s]" % \
      (self.name, self.state, self.level, self.max_level, self.got_ping,
       self.src_name, self.listen_url)


class AudioSrv:
  """handle xmpp calls from audio servers and maintain
     instance objects.

     also performs ping checks
  """
  def __init__(self, botio, ping_interval=1):
    self.botio = botio
    self.callback = None
    self.ping_interval = ping_interval
    self.instances = {}

  def set_callback(self, callback):
    self.callback = callback

  def handle_msg(self, msg):
    """parse an xmpp message and check if its from audio
       return True if msg was handled otherwise False
    """
    sender = msg.sender
    # is an internal message
    cmd = msg.int_cmd
    if cmd == 'connected':
      self._add_instance(msg.int_nick)
      self._handle_msg_in_instances(msg)
      return True
    elif cmd == 'disconnected':
      self._del_instance(msg.int_nick)
      self._handle_msg_in_instances(msg)
      return True
    elif cmd is None:
      # regular message
      args = msg.args
      n = len(args)
      if n > 0:
        cmd = args[0]
        if cmd == 'audio_state' and n > 1:
          state = args[1]
          self._update_state(msg.ts, msg.sender, state)
          return True
        elif cmd == 'audio_level' and n > 2:
          max_level = int(args[1])
          level = int(args[2])
          self._update_level(msg.ts, msg.sender, max_level, level)
          return True
        elif cmd == 'audio_pong':
          self._got_pong(msg.ts, msg.sender)
        elif cmd == 'audio_src' and n > 2:
          src_name = args[1]
          listen_url = args[2]
          self._update_src(msg.ts, msg.sender, src_name, listen_url)
        else:
          self._handle_msg_in_instances(msg)
    return False

  def _handle_msg_in_instances(self, msg):
    for i in self.instances.values():
      opts = i.opts
      if opts is not None:
        opts.handle_command(msg)

  def tick(self):
    """call this method in regular intervals. it will handle the ping
       state of the connected audio instances
    """
    ts = time.time()
    for nick in self.instances:
      i = self.instances[nick]
      delta = ts - i.ping_ts
      if delta >= self.ping_interval:
        # no ping received?
        if not i.got_ping:
          if self.callback is not None:
            self.callback.audio_ping(i, False)
        # send new ping
        i.got_ping = False
        i.ping_ts = ts
        self.botio.write_line("audio_ping", receivers=[i.name])

  def _got_pong(self, ts, sender):
    i = self._get_instance(sender)
    if i is not None:
      i.got_ping = True
      i.ping_ts = ts
      if self.callback is not None:
        self.callback.audio_ping(i, True)

  def _update_src(self, ts, sender, src_name, listen_url):
    i = self._get_instance(sender)
    if i is not None:
      i.src_name = src_name
      i.src_ts = ts
      i.listen_url = listen_url
      self._mark_ping(i, ts)
      if self.callback is not None:
        self.callback.audio_update_src(i)

  def _update_state(self, ts, sender, state):
    i = self._get_instance(sender)
    if i is not None:
      i.state = state
      i.state_ts = ts
      self._mark_ping(i, ts)
      if self.callback is not None:
        self.callback.audio_update_state(i)

  def _update_level(self, ts, sender, max_level, level):
    i = self._get_instance(sender)
    if i is not None:
      i.max_level = max_level
      self._mark_ping(i, ts)
      if self.callback is not None:
        self.callback.audio_update_level(i)

  def _mark_ping(self, i, ts):
    i.ping_ts = ts
    i.got_ping = True

  def _get_instance(self, nick):
    if nick in self.instances:
      return self.instances[nick]
    else:
      return None

  def _add_instance(self, nick):
    if not nick.startswith("audio@"):
      return
    if nick not in self.instances:
      i = AudioInstance(nick)
      self.instances[nick] = i
      if self.callback is not None:
        self.callback.audio_add_instance(i)
      # query initial state
      self.botio.write_line("query_audio_state", receivers=[nick])
      # setup options
      i.opts = botoptsctl.BotOptsCtl(self.botio, nick)
      def notify(field):
        self._opt_update(i, field)
      def notify_all(fields):
        self._opt_update_all(i, fields)
      i.opts.set_notifier(notify, notify_all)

  def _del_instance(self, nick):
    if nick in self.instances:
      i = self.instances[nick]
      del self.instances[nick]
      if self.callback is not None:
        self.callback.audio_del_instance(i)

  def _opt_update(self, i, field):
    if self.callback is not None:
      self.callback.audio_update_option(i, field)

  def _opt_update_all(self, i, fields):
    if self.callback is not None:
      self.callback.audio_update_all_options(i, fields)


# test
if __name__ == '__main__':
  import sys
  sys.path.append("../../tools")
  import botio

  class Callbacks:
    def audio_add_instance(self, i):
      print("add_instance", i, file=sys.stderr)
    def audio_del_instance(self, i):
      print("del_instance", i, file=sys.stderr)
    def audio_update_level(self, i):
      print("update_level", i, file=sys.stderr)
    def audio_update_state(self, i):
      print("update state", i, file=sys.stderr)
    def audio_ping(self, i, valid):
      print("ping", i, valid, file=sys.stderr)
    def audio_update_option(self, i, field):
      print("update_option", i, field, file=sys.stderr)
    def audio_update_all_options(self, i, fields):
      print("update_all_options", i, fields, file=sys.stderr)
    def audio_update_src(self, i):
      print("update_src", i, file=sys.stderr)

  bio = botio.BotIO()
  asrv = AudioSrv(bio)
  asrv.set_callback(Callbacks())
  print("--- main loop ---", file=sys.stderr)
  while True:
    msg = bio.read_args(timeout=1)
    if msg:
      asrv.handle_msg(msg)
    asrv.tick()
