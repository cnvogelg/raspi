from __future__ import print_function

from bot import Bot, BotCmd, BotOptField, BotMod

class EchoMod(BotMod):
  def __init__(self):
    BotMod.__init__(self, "echo")
    self.cmds = [
      BotCmd("echo",callee=self.cmd_echo)
    ]

  def cmd_echo(self, sender):
    self.send_event(["hello"])

  def get_commands(self):
    return self.cmds
