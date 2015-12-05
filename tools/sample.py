#!/usr/bin/env python

from __future__ import print_function

from bot import Bot, BotCmd, BotOptField, BotMod

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

  def get_tick_interval(self):
    return 1

bot = Bot(True)
bot.add_module(Test())
bot.run()
