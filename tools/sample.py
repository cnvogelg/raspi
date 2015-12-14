#!/usr/bin/env python

from __future__ import print_function

from bot import Bot, BotCmd, BotOptField, BotMod
from bot.event import *

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
      BotEvent("echo","hello",callee=self.event_foo_bar),
      ConnectEvent(self.on_connect),
      DisconnectEvent(self.on_disconnect),
      TickEvent(self.on_tick)
    ]

  def on_connect(self):
    self.log("on_connect")

  def on_disconnect(self):
    self.log("on_disconnect")

  def on_tick(self, ts, delta):
    self.log("tick", ts, delta)

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

  def get_tick_interval(self):
    return 1


class Echo(BotMod):
  def __init__(self):
    BotMod.__init__(self, "echo")
    self.cmds = [
      BotCmd("echo",callee=self.cmd_echo)
    ]

  def cmd_echo(self, sender):
    self.reply(["hello"])

  def get_commands(self):
    return self.cmds


bot = Bot(True)
bot.add_module(Test())
bot.add_module(Echo())
bot.run()
