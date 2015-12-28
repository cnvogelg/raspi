from __future__ import print_function

import sys
from bot.cmd import BotCmd

class BotEvent(BotCmd):

  # special mod name
  INTERNAL = "__internal__"

  # internal names
  PEER_CONNECT = "peer_connect"
  PEER_DISCONNECT = "peer_disconnect"
  PEER_MOD_LIST = "peer_mod_list"

  CONNECT = "connect"
  DISCONNECT = "disconnect"
  START = "start"
  STOP = "stop"
  TICK = "tick"
  UPDATE_FIELD = "update_field"
  MOD_LIST = "mod_list"

  def __init__(self, mod_name, name, arg_types=None, callee=None):
    BotCmd.__init__(self, name, arg_types, callee)
    self.mod_name = mod_name

  def handle_event(self, args, sender):
    if len(args) < 2:
      return False
    # check module name
    mod_name = args[0]
    if mod_name != self.mod_name:
      return False
    # remainder of args
    args = args[1:]
    return self.handle_cmd(args, sender)


class InternalEvent(BotEvent):
  def __init__(self, name, callee=None):
    BotEvent.__init__(self, BotEvent.INTERNAL, name, callee=callee)


class PeerConnectEvent(InternalEvent):
  def __init__(self, callee=None):
    InternalEvent.__init__(self, BotEvent.PEER_CONNECT, callee)


class PeerDisconnectEvent(InternalEvent):
  def __init__(self, callee=None):
    InternalEvent.__init__(self, BotEvent.PEER_DISCONNECT, callee)


class PeerModListEvent(InternalEvent):
  def __init__(self, callee=None):
    InternalEvent.__init__(self, BotEvent.PEER_MOD_LIST, callee)


class ConnectEvent(InternalEvent):
  def __init__(self, callee=None):
    InternalEvent.__init__(self, BotEvent.CONNECT, callee)


class DisconnectEvent(InternalEvent):
  def __init__(self, callee=None):
    InternalEvent.__init__(self, BotEvent.DISCONNECT, callee)


class ModListEvent(InternalEvent):
  def __init__(self, callee=None):
    InternalEvent.__init__(self, BotEvent.MOD_LIST, callee)


class StartEvent(InternalEvent):
  def __init__(self, callee=None):
    InternalEvent.__init__(self, BotEvent.START, callee)


class StopEvent(InternalEvent):
  def __init__(self, callee=None):
    InternalEvent.__init__(self, BotEvent.STOP, callee)


class TickEvent(InternalEvent):
  def __init__(self, callee=None):
    InternalEvent.__init__(self, BotEvent.TICK, callee)


class UpdateFieldEvent(InternalEvent):
  def __init__(self, callee=None):
    InternalEvent.__init__(self, BotEvent.UPDATE_FIELD, callee)


# ----- test -----
if __name__ == '__main__':
  be = BotEvent("foo","bar", arg_types=(str, bool, int), callee=print)
  res = be.handle_event(["foo","bar","hello","true","42"],"me")
  print(res)
