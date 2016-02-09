from __future__ import print_function

from bot import Bot, BotCmd, BotOptField, BotMod
from bot.event import *

class TestMod(BotMod):
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
      BotEvent("echo","hello",callee=self.event_echo_hello),
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
    self.send_event(["answer"], to=[sender])

  def event_echo_hello(self, sender):
    self.send_event(['yuck!'])

  def get_commands(self):
    return self.cmds

  def get_opts(self):
    return self.opts

  def get_events(self):
    return self.events

  def get_tick_interval(self):
    return 1
