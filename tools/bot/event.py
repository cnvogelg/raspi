from __future__ import print_function

from bot.cmd import BotCmd

class BotEvent(BotCmd):

  # special mod name
  INTERNAL = "__internal__"

  # internal names
  PEER_CONNECT = "peer_connect"
  PEER_DISCONNECT = "peer_disconnect"

  CONNECT = "connect"
  DISCONNECT = "disconnect"
  START = "start"
  STOP = "stop"
  TICK = "tick"
  UPDATE_FIELD = "update_field"

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


class PeerConnectEvent(BotEvent):
  def __init__(self, callee=None):
    BotEvent.__init__(self, BotEvent.INTERNAL, BotEvent.PEER_CONNECT, (str,), callee)


class PeerDisconnectEvent(BotEvent):
  def __init__(self, callee=None):
    BotEvent.__init__(self, BotEvent.INTERNAL, BotEvent.PEER_DISCONNECT, (str,), callee)


class ConnectEvent(BotEvent):
  def __init__(self, callee=None):
    BotEvent.__init__(self, BotEvent.INTERNAL, BotEvent.CONNECT, None, callee)


class DisconnectEvent(BotEvent):
  def __init__(self, callee=None):
    BotEvent.__init__(self, BotEvent.INTERNAL, BotEvent.DISCONNECT, None, callee)


class StartEvent(BotEvent):
  def __init__(self, callee=None):
    BotEvent.__init__(self, BotEvent.INTERNAL, BotEvent.START, None, callee)


class StopEvent(BotEvent):
  def __init__(self, callee=None):
    BotEvent.__init__(self, BotEvent.INTERNAL, BotEvent.STOP, None, callee)


class TickEvent(BotEvent):
  def __init__(self, callee=None):
    BotEvent.__init__(self, BotEvent.INTERNAL, BotEvent.TICK, None, callee)


class UpdateFieldEvent(BotEvent):
  def __init__(self, callee=None):
    BotEvent.__init__(self, BotEvent.INTERNAL, BotEvent.UPDATE_FIELD, None, callee)


# ----- test -----
if __name__ == '__main__':
  be = BotEvent("foo","bar", arg_types=(str, bool, int), callee=print)
  res = be.handle_event(["foo","bar","hello","true","42"],"me")
  print(res)
