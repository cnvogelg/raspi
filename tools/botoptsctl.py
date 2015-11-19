#!/usr/bin/env python
from __future__ import print_function
import sys
from botoptfield import BotOptField

class BotOptsCtl:
  """a bot options client"""

  def __init__(self, botio, receiver):
    self.botio = botio
    self.opts = {}
    self.notify = None
    self.notify_all = None
    self.receiver = receiver
    self.got_all = False

  def set_notifier(self, notify, notify_all):
    """set notifier callback. calls notifier(field)"""
    self.notify = notify
    self.notify_all = notify_all

  # ----- local change -----

  def get_value(self, name):
    """get a cached value"""
    if name in opts:
      return self.opts[name].get()
    else:
      return None

  def set_value(self, name, value, do_notify=True):
    """set value in server"""
    if name not in self.opts:
      return False
    # simply send a 'set' command and wait for reply
    args = ['set', name, value]
    self.botio.write_args(args, receivers=[self.receiver])
    return True

  def get_all_values(self):
    return self.opts

  def has_all_values(self):
    return self.got_all

  # ----- query values -----

  def _send(self, *args):
    self.botio.write_args(args, receivers=[self.receiver])

  def query_value(self, key):
    """current value is send via bot"""
    self._send('query', key)

  def query_all(self):
    """send all values to bot"""
    self._send('query_all')

  def flush_all(self):
    """remove all locally stored options"""
    self.opts = {}
    self.got_all = False
    if self.notify_all is not None:
      self.notify_all(self.opts.values())

  def load(self):
    """load the options from config file"""
    self._send('load')

  def save(self):
    """save options to config file"""
    self._send('save')

  def reset_all(self):
    """reset all options to default values"""
    self._send('reset_all')

  def reset(self, key):
    """reset a field to default values"""
    self._send('reset', key)

  # ----- parse bot command -----

  def handle_command(self, msg):
    """parse a option command. return true if command was parsed"""
    # handle internal
    if msg.is_internal:
      # initial query
      if msg.int_nick == self.receiver:
        if msg.int_cmd == 'connected':
          self.query_all()
          return True
        elif msg.int_cmd == 'disconnected':
          self.flush_all()
          return True
      # ignore internal commands
      return False
    # only check for my server
    if msg.sender != self.receiver:
      return False
    # check args
    args = msg.args
    n = len(args)
    if n < 1:
      self._error("no_cmd?")
      return False
    cmd = args[0]
    # 'value'
    if cmd == 'value' and n > 1:
      return self._handle_value(args[1:])
    # 'end_values'
    elif cmd == 'end_values':
      return self._handle_end_values()
    # ignore errors
    elif cmd in ('error', 'status'):
      pass
    # unknown command
    else:
      self._error("cmd? " + cmd)
      return False

  def _handle_value(self, items):
    # try to parse field
    field = BotOptField.parse(items)
    if field is None:
      self._error("field? " + " ".join(items))
      return False
    else:
      self.opts[field.name] = field
      if self.notify is not None:
        self.notify(field)
      return True

  def _handle_end_values(self):
    self.got_all = True
    if self.notify_all is not None:
      self.notify_all(self.opts.values())
    return True

  def _error(self, txt):
    self.botio.write_line("error " + txt)


# ----- Test -----
if __name__ == '__main__':
  import botio
  import time
  from botoptfield import BotOptField

  def log(*args):
    t =  time.time()
    a = ["%10.3f  ctl  " % t] + list(args)
    print(*a,file=sys.stderr)

  def notifier(field):
    log("update: field:", field)

  def notify_all(fields):
    log("update_all:", fields)

  log("start")
  bio = botio.BotIO(verbose=False)
  nick = bio.get_nick()
  pos = nick.find('@')
  host = nick[pos+1:]
  srv = "botopts@" + host
  botopts = BotOptsCtl(bio, srv)
  botopts.set_notifier(notifier, notify_all)
  log("got nick: '%s' -> srv: '%s'" % (nick, srv))
  while True:
    try:
      msg = bio.read_args(timeout=1)
      if msg:
        botopts.handle_command(msg)
    except KeyboardInterrupt:
      log("Break")
      break

