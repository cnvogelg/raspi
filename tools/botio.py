#!/usr/bin/env python
# simple class to help reading stdin/stdio bot IO

from __future__ import print_function
import select
import sys

class BotIO:
  """small helpers to read and write commands to the stdin/stdout bot pipe"""
  
  def __init__(self, nick):
    self.nick = nick
  
  def read_line(self, timeout=0.1, broadcast=True):
    """return next line from bot or None if nothing was received"""
    (r,w,x) = select.select([sys.stdin],[],[], timeout)
    if sys.stdin in r:
      l = sys.stdin.readline()
      line = l.strip()
      pos = line.find(':')
      if pos != -1:
        prefix = line[:pos]
        line = line[pos+1:]
        if prefix == self.nick:
          return line
        else:
          return None
      else:
        if broadcast:
          return line
        else:
          return None
    else:
      return None
  
  def read_args(self, timeout=0.1, broadcast=True):
    """already split line into args"""
    line = self.read_line(timeout, broadcast)
    if line == None:
      return None
    else:
      args = line.split()
      if len(args) > 0:
        return args
      else:
        return None
  
  def write_line(self, msg):
    """write a line"""
    sys.stdout.write(msg+"\n")
    sys.stdout.flush()
    
  def write_args(self, args):
    self.write_line(" ".join(args))

# ----- test -----
if __name__ == '__main__':
  print("BotIO test: echo!",file=sys.stderr)
  bio = BotIO('echo_test')
  while True:
    args = bio.read_args(timeout=1,broadcast=False)
    if args != None:
      # do not recurse :)
      if args[0] != 'echo':
        bio.write_line('echo ' + ' '.join(args))
