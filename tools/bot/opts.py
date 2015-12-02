#!/usr/bin/env python
from __future__ import print_function
import sys

from cmd import BotCmd

class BotOpts:
  """serve a set of bot options"""

  def __init__(self, reply, opts, cfg=None, cfg_name=None):
    self.reply = reply
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
        self.set_value(key, new_vals[key], do_reply=False)
    # setup commands
    self._setup_cmds()

  def set_notifier(self, notify):
    """set notifier callback. calls notifier(field)"""
    self.notify = notify

  # ----- local change -----

  def get_value(self, name):
    """internal get value"""
    return self.opts[name].get()

  def set_value(self, name, value, do_notify=True, do_reply=False):
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
      if do_reply:
        self.push_value(name)
      return True
    # ignore same value
    elif ok is None:
      if do_reply:
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
    self.reply([line], to=receivers)

  def push_all(self, receivers=None):
    """send all values to bot"""
    for key in self.opts:
      self.push_value(key, receivers=receivers)
    self.reply(["end_values"], to=receivers)

  # ----- parse bot command -----

  def _setup_cmds(self):
    self.cmds = [
      BotCmd("query_all",callee=self._cmd_query_all),
      BotCmd("query",arg_types=(str,),callee=self._cmd_query),
      BotCmd("set",arg_types=(str,str),callee=self._cmd_set),
      BotCmd("load",callee=self._cmd_load),
      BotCmd("save",callee=self._cmd_save),
      BotCmd("reset_all",callee=self._cmd_reset_all),
      BotCmd("reset",arg_types=(str,),callee=self._cmd_reset)
    ]

  def _cmd_query_all(self, sender):
    self.push_all(receivers=[sender])

  def _cmd_query(self, sender, args):
    key = args[0]
    if key not in self.opts:
      self._error("key? " + key, sender)
    elif key in self.opts:
      self.push_value(key, receivers=[sender])
    else:
      self._error("query? " + key, sender)

  def _cmd_set(self, sender, args):
    key = args[0]
    val = args[1]
    if key not in self.opts:
      self._error("key? " + key, sender)
    elif not self.set_value(key, val):
      self._error("set? " + key + " " + args[2], sender)

  def _cmd_load(self, sender):
    self.load()

  def _cmd_save(self, sender):
    self.save()

  def _cmd_reset_all(self, sender):
    self.reset_all()

  def _cmd_reset(self, sender, args):
    key = args[0]
    if key not in self.opts:
      self._error("key? " + key, sender)
    else:
      self.reset(key)

  def handle_command(self, args, sender, ignore_other=True):
    """parse a option command. return true if command was parsed"""
    cmd_name = args[0]
    for cmd in self.cmds:
      if cmd_name == cmd.get_name():
        res = cmd.handle_cmd(args, sender)
        if type(res) is str:
          self._error(cmd_name + ": " + res, to)
          return False
        else:
          return True
    return None

  def _error(self, txt, to=None):
    self.reply(["error " + txt], to=to)

  def _status(self, txt, to=None):
    self.reply(["status " + txt], to=to)

# ----- Test -----
if __name__ == '__main__':
  import io
  import time
  from optfield import BotOptField

  def log(*args):
    t =  time.time()
    a = ["%10.3f  srv  " % t] + list(args)
    print(*a,file=sys.stderr)

  def notifier(field):
    log("update: field:", field)

  log("start")
  bio = io.BotIO(verbose=False)
  nick = bio.get_nick()
  opts = [
    BotOptField("abool",bool,True,desc="a boolean"),
    BotOptField("anint",int,42, val_range=[1,100], desc="an integer"),
    BotOptField("astr",str,"hoo!", desc="a string")
  ]

  def reply(args, to):
    bio.write_args(args, to)

  botopts = BotOpts(reply, opts, cfg=bio.get_cfg())
  botopts.set_notifier(notifier)
  log("got nick: '%s'" % nick)
  while True:
    try:
      msg = bio.read_args(timeout=1)
      if msg:
        if msg.is_internal:
          pass
        else:
          botopts.handle_command(msg.args, msg.sender)
    except KeyboardInterrupt:
      log("Break")
      break

