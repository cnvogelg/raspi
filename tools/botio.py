#!/usr/bin/env python
# simple class to help reading stdin/stdio bot IO

from __future__ import print_function
import select
import sys
import os
import time
import botcfg

class BotIOMsg:
  def __init__(self, line, sender, receivers, is_internal):
    self.line = line
    self.args = None
    self.sender = sender
    self.receivers = receivers
    self.is_internal = is_internal
    self.int_cmd = None
    self.int_nick = None
    self.ts = None

  def split_args(self):
    self.args = self.line.split()

  def __str__(self):
    if self.receivers is None:
      rcv = ""
    else:
      rcv = ",".join(self.receivers)
    return "[%s;%s|%s (%s)]" % (self.sender, rcv, self.line, self.is_internal)

class BotIO:
  """small helpers to read and write commands to the stdin/stdout bot pipe"""

  def __init__(self, verbose=False):
    self._verbose = verbose
    # no bot connected? fake nick
    if os.isatty(sys.stdin.fileno()):
      self._nick = "fake"
      self._cmd_name = "fake"
      self._cfg_path = None
    else:
      self._nick = None
      # wait for init command by bot
      l = sys.stdin.readline()
      line = l.strip()
      msg = self._parse_line(line)
      if not msg or len(msg.args) != 3:
        raise ValueError("no init by bot!")
      self._nick = msg.sender
      self._cmd_name = msg.args[1]
      self._cfg_path = msg.args[2]
    # show nick
    if verbose:
      print("botio: init: nick='%s' cmd_name='%s' cfg_path='%s'" % \
        (self._nick, self._cmd_name, self._cfg_path), file=sys.stderr)
    # init roster
    self._roster = {}

  def get_nick(self):
    return self._nick

  def get_cmd_name(self):
    return self._cmd_name

  def get_cfg_path(self):
    return self._cfg_path

  def get_cfg(self):
    """return a config object that matches the one of xmppbot"""
    return botcfg.BotCfg(self._cmd_name, self._cfg_path)

  def _parse_line(self, line):
    """split line from bot into message
       return BotIOMsg or None
    """
    pos = line.find('|')
    if pos != -1:
      prefix = line[:pos]
      line = line[pos+1:]
      # prefix contains "from;to,to,to|line"
      pos = prefix.find(';')
      if pos != -1:
        sender = prefix[:pos]
        receivers = prefix[pos+1:].split(',')
        if len(receivers) == 1 and receivers[0] == '':
          receivers = None

        # a message from my nick is considered internal
        is_internal = sender == self._nick

        msg = BotIOMsg(line, sender, receivers, is_internal)
        msg.ts = time.time()
        msg.split_args()

        # parse internal message
        if is_internal:
          if not self._parse_internal(msg):
            return None

        return msg
    # something went wrong
    return None

  def _parse_internal(self, msg):
    """parse message from xmppbot"""
    args = msg.args
    if len(args) < 2:
      return False
    cmd = args[0]
    msg.int_cmd = cmd
    if cmd == 'connected':
      nick = " ".join(args[1:])
      if self._verbose:
        print("botio: connected '%s'" % nick, file=sys.stderr)
      self._roster[nick] = (True, time.time())
      msg.int_nick = nick
      return True
    elif cmd == 'disconnected':
      nick = " ".join(args[1:])
      if self._verbose:
        print("botio: disconnected '%s'" % nick, file=sys.stderr)
      self._roster[nick] = (False, time.time())
      msg.int_nick = nick
      return True
    else:
      msg.int_nick = None
      if self._verbose:
        print("botio: unknown command:", msg.line, file=sys.stderr)
      return False

  def get_roster(self):
    return self._roster

  def read_line(self, timeout=0.1, internal=False):
    """return next line from bot or None if nothing was received
       return (line, sender, [receiver, ...])
       return False if line is invalid or None on timeout
    """
    while True:
      (r,w,x) = select.select([sys.stdin],[],[], timeout)
      if sys.stdin in r:
        l = sys.stdin.readline()
        line = l.strip()
        if self._verbose:
          print("botio: got '%s'" % line, file=sys.stderr)
        msg = self._parse_line(line)
        if msg:
          # if its internal and return internal then report it
          # otherwise loop
          if internal:
            if msg.is_internal:
              return msg
          else:
            return msg
        else:
          # parse error of message
          return False
      else:
        # timeout
        return None

  def read_args(self, timeout=0.1):
    """already split line into args"""
    result = self.read_line(timeout)
    if result:
      result.split_args()
    return result

  def write_line(self, msg, receivers=None):
    """write a line"""
    if receivers is not None:
      msg = ",".join(receivers) + "|" + msg
    if self._verbose:
      print("botio: put '%s'" % msg, file=sys.stderr)
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

  def write_args(self, args, receivers=None):
    self.write_line(" ".join(args), receivers)


# ----- test -----
if __name__ == '__main__':
  def log(*args):
    t =  time.time()
    a = ["%10.3f" % t] + list(args)
    print(*a,file=sys.stderr)

  log("test: start")
  bio = BotIO()
  nick = bio.get_nick()
  cmd_name = bio.get_cmd_name()
  cfg_path = bio.get_cfg_path()
  log("test: got nick='%s' cmd_name='%s' cfg_path='%s'" % \
    (nick, cmd_name, cfg_path))
  while True:
    try:
      msg = bio.read_args(timeout=1)
      if msg:
        if msg.is_internal:
          if msg.int_cmd == 'exit':
            log("text: exit")
            break
          log("test: internal: cmd=%s nick=%s" % (msg.int_cmd, msg.int_nick))
          log("test: roster=", bio.get_roster())
        else:
          log("test: reply to: line=%s, sender=%s, receivers=%s" %
                (msg.line, msg.sender, msg.receivers))
          if msg.receivers is not None:
            log("test: do echo!")
            bio.write_line('echo ' + ' '.join(msg.args), receivers=[msg.sender])
    except KeyboardInterrupt:
      log("test: Break")
      break

