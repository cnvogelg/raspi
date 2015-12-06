#!/usr/bin/env python

from __future__ import print_function
import time
import sys

from bot.io import BotIO
from bot.cmd import BotCmd
from bot.opts import BotOpts

class Bot:
  """main class for a bot instance"""
  def __init__(self, verbose=False):
    self.modules = []
    self.bio = None
    self.nick = None
    self.cmd_name = None
    self.cfg_path = None
    self.verbose = verbose
    self.connected = False

  def add_module(self, module):
    """add a module to the bot"""
    self.modules.append(module)

  def _log(self, *args):
    if self.verbose:
      t = time.time()
      a = ["%10.3f" % t] + list(args)
      print(*a,file=sys.stderr)

  def run(self):
    """run the bot"""
    if len(self.modules) == 0:
      raise Error("No modules added!")
    self._setup()
    self._setup_modules()
    self._setup_cmds()
    self._main_loop()

  def _setup(self):
    self._log("bot: setup")
    self.bio = BotIO(verbose=False)
    self.nick = self.bio.get_nick()
    self.cmd_name = self.bio.get_cmd_name()
    self.cfg_path = self.bio.get_cfg_path()
    self._log("bot: got nick='%s' cmd_name='%s' cfg_path='%s'" % \
      (self.nick, self.cmd_name, self.cfg_path))

  def _setup_modules(self):
    self.bot_tick_interval = 1
    for m in self.modules:
      name = m.get_name()

      # set reply function for module
      def reply(args, to=None):
        a = [name] + list(args)
        self.bio.write_args(a, receivers=to)

      # set log function
      def log(*args):
        a = [name + ":"] + list(args)
        self._log(*a)

      # get bot config
      cfg = self.bio.get_cfg()

      # has options?
      opts = m.get_opts()
      bo = None
      if opts is not None:
        cfg_name = m.get_opts_name()
        bo = BotOpts(reply, opts, cfg=cfg, cfg_name=cfg_name)
        bo.set_notifier(m.on_update_opt_field)
        self._log("bot: module",name,"opts:", bo.get_values())

      # setup bot
      m.setup(reply, log, cfg, bo)

      # get tick (after setup of bot)
      tick = m.get_tick_interval()
      self._log("bot: module",name,"tick",tick)
      if tick > 0 and tick < self.bot_tick_interval:
        self.bot_tick_interval = tick

    # report bot tick
    self._log("bot: tick", self.bot_tick_interval)

  def _setup_cmds(self):
    self.cmds = [
      BotCmd("lsmod",callee=self._cmd_lsmod)
    ]

  def _cmd_lsmod(self, sender):
    self._log("cmd: lsmod")
    for a in self.modules:
      self._reply(["module", a.get_name()], to=[sender])

  def _main_loop(self):
    self._init_tick()

    # report start
    for m in self.modules:
      m.on_start()

    while True:
      try:
        # handle tick
        self._tick()
        # handle incoming messages
        msg = self.bio.read_args(timeout=self.bot_tick_interval)
        if msg:
          if msg.is_internal:
            if not self._handle_internal_msg(msg):
              break
          else:
            self._handle_msg(msg)
      except KeyboardInterrupt:
        self._log("bot: Break")
        break

   # report stop
    for m in self.modules:
      m.on_stop()

  def _init_tick(self):
    ts = time.time()
    for m in self.modules:
      m.last_ts = ts

  def _tick(self):
    """call tick in modules"""
    ts = time.time()
    for m in self.modules:
      tick = m.get_tick_interval()
      if tick > 0:
        delta = ts - m.last_ts
        if delta >= tick:
          m.on_tick(ts, delta)
          m.last_ts = ts

  def _reply(self, args, to=None):
    self.bio.write_args(args, receivers=to)

  def _error(self, msg, to):
    self._reply(["error", msg], [to])

  def _handle_internal_msg(self, msg):
    """handle internal message"""
    if msg.int_cmd == 'exit':
      self._log("exit")
      return False
    # connected?
    my_nick = self.bio.get_nick()
    msg_nick = msg.int_nick
    self._log("internal", msg_nick, msg.int_cmd)
    if msg.int_cmd == 'connected':
      if msg.int_nick == my_nick:
        if not self.connected:
          self._log("I am connected")
          self.connected = True
          for m in self.modules:
            m.on_connected()
      else:
        for m in self.modules:
          m.on_peer_connected(msg_nick)
    # disconnected?
    elif msg.int_cmd == 'disconnected':
      if msg.int_nick == my_nick:
        if self.connected:
          self._log("I am disconnected")
          self.connected = False
          for m in self.modules:
            m.on_disconnected()
      else:
        for m in self.modules:
          m.on_peer_disconnected(msg_nick)
    return True

  def _handle_msg(self, msg):
    # get command name
    a = msg.args
    n = len(a)
    to = msg.sender
    # no command given?
    if n == 0:
      self._error("huh?", to)
      return
    # get command name
    cmd_name = a[0]
    # check internal command
    for cmd in self.cmds:
      if cmd_name == cmd.get_name():
        res = cmd.handle_cmd(a, msg.sender)
        if type(res) is str:
          self._error(cmd_name + ": " + res, to)
        return
    # is it a module prefix
    for mod in self.modules:
      if cmd_name == mod.get_name():
        # need a sub command!
        if n == 1:
          self._error(cmd_name + ": huh?", to)
        else:
          # parse module command
          res = self._handle_mod_cmd(mod, a[1:], msg.sender)
          if type(res) is str:
            self._error(cmd_name + ": " + res, to)
        return
    # unknown
    #self._error("Unknown command: " + cmd_name, to)

  def _handle_mod_cmd(self, mod, args, to):
    """handle a module command"""
    cmd_name = args[0]
    # check bot commands
    cmds = mod.get_commands()
    if cmds is not None:
      for c in cmds:
        if cmd_name == c.get_name():
          return c.handle_cmd(args, to)
    # check options
    bo = mod.botopts
    if bo is not None:
      res = bo.handle_command(args, to)
      if res is not None:
        return res
    # nothing found
    return "huh? " + cmd_name


# ----- test -----
if __name__ == '__main__':
  from mod import BotMod
  bot = Bot(True)
  bm = BotMod("test")
  bot.add_module(bm)
  bot.run()
