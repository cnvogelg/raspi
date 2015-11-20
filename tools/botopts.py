#!/usr/bin/env python
from __future__ import print_function
import sys

class BotOpts:
  """serve a set of bot options"""

  def __init__(self, botio, opts, cfg=None, cfg_name=None):
    self.botio = botio
    self.opts = {}
    self.def_values = {}
    for o in opts:
      self.opts[o.name] = o
      self.def_values[o.name] = o.value
    self.notify = None
    # set config
    self.cfg = cfg
    if cfg_name is None:
      self.cfg_name = "bot_opts"
    else:
      self.cfg_name = cfg_name
    # load options from config if available
    if cfg is not None:
      cfg.load()
      vals = self.get_values()
      new_vals = cfg.get_section(self.cfg_name, vals)
      for key in new_vals:
        self.set_value(key, new_vals[key])

  def set_notifier(self, notify):
    """set notifier callback. calls notifier(field)"""
    self.notify = notify

  # ----- local change -----

  def get_value(self, name):
    """internal get value"""
    return self.opts[name].get()

  def set_value(self, name, value, do_notify=True):
    """internal set value"""
    if name not in self.opts:
      return False
    field = self.opts[name]
    ok = field.set(value)
    if ok == True:
      # internal notifier
      if self.notify is not None and do_notify:
        self.notify(field)
      # push to room
      self.push_value(name)
      return True
    # ignore same value
    elif ok is None:
      self._status("same " + name)
      return True
    else:
      return False

  def get_values(self):
    """return a dict with name : values"""
    res = {}
    for name in self.opts:
      field = self.opts[name]
      res[name] = field.value
    return res

  # ----- load/save/reset -----

  def load(self):
    """load option values from config file"""
    if self.cfg is not None:
      path = self.cfg.load()
      if path is None:
        self._error("load? not_found")
        return False
      self._status("loaded "+path)
      new_vals = self.cfg.get_section(self.cfg_name, self.get_values())
      for key in new_vals:
        if not self.set_value(key, new_vals[key]):
          self._error("load? set_value")
          return False
      return True
    else:
      self._error("load? no_cfg")
      return False

  def save(self):
    """save option values to config file"""
    if self.cfg is not None:
      self.cfg.set_section(self.cfg_name, self.get_values())
      path = self.cfg.save()
      if path is None:
        self._error("save? not_found")
        return False
      else:
        self._status("saved "+path)
        return True
    else:
      self._error("save? no_cfg")
      return False

  def reset(self, key):
    """reset a key"""
    if key in self.def_values:
      return self.set_value(key, self.def_values[key])
    else:
      return False

  def reset_all(self):
    """reset all values"""
    for key in self.def_values:
      if not self.set_value(key, self.def_values[key]):
        return False
    return True

  # ----- push value to change other bot's options -----

  def push_value(self, key, receivers=None):
    """current value is send via bot"""
    value = self.opts[key]
    line = "value " + str(value)
    self.botio.write_line(line, receivers=receivers)

  def push_all(self, receivers=None):
    """send all values to bot"""
    for key in self.opts:
      self.push_value(key, receivers=receivers)
    self.botio.write_line("end_values", receivers=receivers)

  # ----- parse bot command -----

  def handle_command(self, msg, ignore_other=True):
    """parse a option command. return true if command was parsed"""
    # ignore internal commands
    if msg.int_cmd is not None:
      return False
    args = msg.args
    n = len(args)
    if n < 1:
      self._error("no_cmd?")
      return False
    # check if its a 'query', 'push' command
    cmd = args[0]
    if cmd == 'query_all':
      self.push_all( receivers=[msg.sender])
    elif cmd == 'query' and n == 2:
      # query <name>
      key = args[1]
      if key not in self.opts:
        self._error("key? " + key)
        return False
      return self._handle_query(key, msg.sender)
    elif cmd == 'set' and n == 3:
      # set <name> ...
      key = args[1]
      if key not in self.opts:
        self._error("key? " + key)
        return False
      if not self.set_value(key, args[2]):
        self._error("set? " + key + " " + args[2])
        return False
      else:
        return True
    elif cmd == 'load':
      return self.load()
    elif cmd == 'save':
      return self.save()
    elif cmd == 'reset' and n == 2:
      key = args[1]
      if key not in self.opts:
        self._error("key? " + key)
        return False
      return self.reset(key)
    elif cmd == 'reset_all':
      return self.reset_all()
    elif cmd in ('error', 'status'):
      # ignore errors
      pass
    elif not ignore_other:
      self._error("cmd? " + cmd)
      return False

  def _handle_query(self, key, sender):
    if key in self.opts:
      self.push_value(key, receivers=[sender])
      return True
    else:
      self._error("query? " + key)
      return False

  def _error(self, txt):
    self.botio.write_line("error " + txt)

  def _status(self, txt):
    self.botio.write_line("status " + txt)

# ----- Test -----
if __name__ == '__main__':
  import botio
  import time
  from botoptfield import BotOptField

  def log(*args):
    t =  time.time()
    a = ["%10.3f  srv  " % t] + list(args)
    print(*a,file=sys.stderr)

  def notifier(field):
    log("update: field:", field)

  log("start")
  bio = botio.BotIO(verbose=False)
  nick = bio.get_nick()
  opts = [
    BotOptField("abool",bool,True,desc="a boolean"),
    BotOptField("anint",int,42, val_range=[1,100], desc="an integer"),
    BotOptField("astr",str,"hoo!", desc="a string")
  ]
  botopts = BotOpts(bio, opts, cfg=bio.get_cfg())
  botopts.set_notifier(notifier)
  log("got nick: '%s'" % nick)
  while True:
    try:
      msg = bio.read_args(timeout=1)
      if msg:
        if msg.is_internal:
          pass
        else:
          botopts.handle_command(msg)
    except KeyboardInterrupt:
      log("Break")
      break

