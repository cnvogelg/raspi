#!/usr/bin/env python

from __future__ import print_function

class BotMod:
  """base class for bot modules"""
  def __init__(self, name):
    self.name = name
    self.reply = None
    self.log = None
    self.last_tick = 0

  def get_name(self):
    """return name of bot"""
    return self.name

  def set_reply(self, r):
    """bot sets reply callable on init"""
    self.reply = r

  def set_log(self, l):
    """bot sets the log function on init"""
    self.log = l

  def get_commands(self):
    """return bot command array"""
    return None

  def get_opts_name(self):
    """return config section name of bot"""
    return self.name

  def get_opts(self):
    """return bot options array"""
    return None

  def get_tick_interval(self):
    """return the interval in s the tick will be triggered. Use 0 for no tick"""
    return 0

  # ----- events -----

  def on_start(self):
    self.log("start")

  def on_stop(self):
    self.log("stop")

  def on_update_opt_field(self, field):
    """callback whenever a field changes"""
    self.log("update_opt_field:", field)

  def on_tick(self, ts, delta):
    self.log("tick", ts, delta)

  def on_connected(self):
    self.log("connected")

  def on_disconnected(self):
    self.log("disconnected")

  def on_peer_connected(self, nick):
    self.log("peer connected", nick)

  def on_peer_disconnected(self, nick):
    self.log("peer disconnected", nick)


# ----- test -----
if __name__ == '__main__':
  from bot import Bot
  from cmd import BotCmd
  from optfield import BotOptField

  class Test(BotMod):
    def __init__(self):
      BotMod.__init__(self, "test")
      self.cmds = [
        BotCmd("hello",callee=self.cmd_hello)
      ]
      self.opts = [
        BotOptField("abool",bool,True,desc="a boolean"),
        BotOptField("anint",int,42, val_range=[1,100], desc="an integer"),
        BotOptField("astr",str,"hoo!", desc="a string")
      ]

    def cmd_hello(self, sender):
      self.reply(["answer"], to=[sender])

    def get_commands(self):
      return self.cmds

    def get_opts(self):
      return self.opts

  bot = Bot(True)
  bot.add_module(Test())
  bot.run()
