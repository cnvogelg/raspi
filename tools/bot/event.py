from __future__ import print_function

from bot.cmd import BotCmd

class BotEvent(BotCmd):
  def __init__(self, mod_name, name, arg_types=None, callee=None):
    BotCmd.__init__(self, name, arg_types, callee)
    self.mod_name = mod_name

  def handle_event(self, args, sender):
    if len(args) < 2:
      return "no event"
    # check module name
    mod_name = args[0]
    if mod_name != self.mod_name:
      return False
    # remainder of args
    args = args[1:]
    return self.handle_cmd(args, sender)


# ----- test -----
if __name__ == '__main__':
  be = BotEvent("foo","bar", arg_types=(str, bool, int), callee=print)
  res = be.handle_event(["foo","bar","hello","true","42"],"me")
  print(res)
