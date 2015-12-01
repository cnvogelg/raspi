#!/usr/bin/env python

from __future__ import print_function

class BotMod:
  """base class for bot modules"""
  def __init__(self, name):
    self.name = name
    self.reply = None

  def get_name(self):
    return self.name

  def set_reply(self, r):
    self.reply = r

  def get_commands(self):
    return None


# ----- test -----
if __name__ == '__main__':
  from bot import Bot
  from botcmd import BotCmd

  class Test(BotMod):
    def __init__(self):
      BotMod.__init__(self, "test")
      self.cmds = [
        BotCmd("hello",callee=self.cmd_hello)
      ]

    def cmd_hello(self, sender):
      self.reply(["answer"], to=[sender])

    def get_commands(self):
      return self.cmds

  bot = Bot(True)
  bot.add_module(Test())
  bot.run()
