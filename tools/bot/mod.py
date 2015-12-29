#!/usr/bin/env python

from __future__ import print_function

class BotMod(object):
  """base class for bot modules"""
  def __init__(self, name):
    self.name = name
    self.reply = None
    self.log = None
    self.cfg = None
    self.botopts = None
    self.last_tick = 0
    self.nick = None
    self.bot = None

  def get_name(self):
    """return name of bot"""
    return self.name

  def setup(self, reply, log, cfg, botopts=None):
    """bot sets up the module and reports environment"""
    self.reply = reply
    self.log = log
    self.cfg = cfg
    self.botopts = botopts

  def get_version(self):
    """return a version string"""
    return "1.0"

  def get_commands(self):
    """return bot command array"""
    return None

  def get_opts_name(self):
    """return config section name of bot"""
    return self.name

  def get_opts(self):
    """return bot options array"""
    return None

  def get_events(self):
    """return the list of events"""
    return None

  def get_tick_interval(self):
    """return the interval in s the tick will be triggered. Use 0 for no tick"""
    return 0


# ----- test -----
if __name__ == '__main__':
  from bot import Bot
  from cmd import BotCmd
  from optfield import BotOptField
  from event import BotEvent

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
      self.events = [
        BotEvent("foo","bar",callee=self.event_foo_bar)
      ]

    def cmd_hello(self, sender):
      self.reply(["answer"], to=[sender])

    def event_foo_bar(self, sender):
      self.reply(['yuck!'])

    def get_commands(self):
      return self.cmds

    def get_opts(self):
      return self.opts

    def get_events(self):
      return self.events

  bot = Bot(True)
  bot.add_module(Test())
  bot.run()
