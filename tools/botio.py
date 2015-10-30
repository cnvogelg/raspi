#!/usr/bin/env python
# simple class to help reading stdin/stdio bot IO

from __future__ import print_function
import select
import sys
import os

class BotIOMsg:
  def __init__(self, line, sender, receivers):
    self.line = line
    self.args = None
    self.sender = sender
    self.receivers = receivers

  def split_args(self):
    self.args = self.line.split()

class BotIO:
  """small helpers to read and write commands to the stdin/stdout bot pipe"""

  def __init__(self, verbose=False):
    self._verbose = verbose
    # no bot connected? fake nick
    if os.isatty(sys.stdin.fileno()):
      self._nick = "fake"
    else:
      # wait for init command by bot
      l = sys.stdin.readline()
      line = l.strip()
      msg = self._parse_line(line)
      if not msg:
        raise ValueError("no init by bot!")
      self._nick = msg.sender
    # show nick
    if verbose:
      print("init: nick='%s'" % self._nick, file=sys.stderr)

  def get_nick(self):
    return self._nick

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
        return BotIOMsg(line, sender, receivers)
    # something went wrong
    return None

  def read_line(self, timeout=0.1):
    """return next line from bot or None if nothing was received
       return (line, sender, [receiver, ...])
       return False if line is invalid or None on timeout
    """
    (r,w,x) = select.select([sys.stdin],[],[], timeout)
    if sys.stdin in r:
      l = sys.stdin.readline()
      line = l.strip()
      if self._verbose:
        print("botio: got '%s'" % line, file=sys.stderr)
      msg = self._parse_line(line)
      if msg:
        return msg
      else:
        return False
    else:
      # timout
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
  print("BotIO test: echo!",file=sys.stderr)
  bio = BotIO(verbose=True)
  nick = bio.get_nick()
  print("got nick: '%s'" % nick, file=sys.stderr)
  while True:
    msg = bio.read_args(timeout=1)
    if msg:
      print("echo_test got: line=%s, sender=%s, receivers=%s" %
            (msg.line, msg.sender, msg.receivers),file=sys.stderr)
      if msg.sender == nick:
        print("-> internal msg!",file=sys.stderr)
      else:
        bio.write_line('echo ' + ' '.join(msg.args), receivers=[msg.sender])
