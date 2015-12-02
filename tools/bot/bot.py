#!/usr/bin/env python

from __future__ import print_function
import time
import sys

from io import BotIO
from cmd import BotCmd
from opts import BotOpts

class Bot:
  """main class for a bot instance"""
  def __init__(self, verbose=False):
    self.modules = []
    self.bio = None
    self.nick = None
    self.cmd_name = None
    self.cfg_path = None
    self.verbose = verbose
    self.opts = {}

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
    for m in self.modules:
      name = m.get_name()
      self._log("bot: module",name,"found")
      # set reply function for module
      def reply(args, to=None):
        a = [name] + list(args)
        self.bio.write_args(a, receivers=to)
      m.set_reply(reply)
      # set log function
      def log(*args):
        a = [name + ":"] + list(args)
        self._log(*a)
      m.set_log(log)
      # has options?
      opts = m.get_opts()
      if opts is not None:
        cfg_name = m.get_opts_name()
        bo = BotOpts(reply, opts, cfg=self.bio.get_cfg(), cfg_name=cfg_name)
        self.opts[m] = bo
        bo.set_notifier(m.on_update_opt_field)
        self._log("bot: module",name,"opts:", bo.get_values())

  def _setup_cmds(self):
    self.cmds = [
      BotCmd("lsmod",callee=self._cmd_lsmod)
    ]

  def _cmd_lsmod(self, sender):
    self._log("cmd: lsmod")
    for a in self.modules:
      self._reply(["module", a.get_name()], to=[sender])

  def _main_loop(self):
    while True:
      try:
        msg = self.bio.read_args(timeout=1)
        if msg:
          if msg.is_internal:
            if msg.int_cmd == 'exit':
              self._log("bot: exit")
              break
            self._handle_internal_msg(msg)
          else:
            self._handle_msg(msg)
      except KeyboardInterrupt:
        self._log("bot: Break")
        break

  def _reply(self, args, to=None):
    self.bio.write_args(args, receivers=to)

  def _error(self, msg, to):
    self._reply(["error", msg], [to])

  def _handle_internal_msg(self, msg):
    """handle internal message"""
    pass

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
    if mod in self.opts:
      bo = self.opts[mod]
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

