from __future__ import print_function
import sys

class BotOpts:
  """manage a dictionary of key,value options
     and allow them to be modified or queried via bot commands
  """

  def __init__(self, botio, name, opts):
    self.botio = botio
    self.name = name
    self.opts = opts
    self.notify = None

  def set_notifier(self, notify):
    self.notify = notify

  # ----- local change -----

  def get_value(self, key):
    """internal get value"""
    return self.opts[key]

  def set_value(self, key, value, do_notify=True):
    """internal set value"""
    self.opts[key] = value
    # internal notifier
    if self.notify is not None and do_notify:
      self.notify(key, value)
    # push to room
    self._reply_value(key)

  # ----- push value to change other bot's options -----

  def push_value(self, key, receivers=None):
    """current value is send via bot"""
    value = self.opts[key]
    args = [ 'push', self.name, key, str(value) ]
    self.botio.write_args(args, receivers=receivers)

  def push_all(self, receivers=None):
    """send all values to bot"""
    for key in self.opts:
      self.push_value(key, receivers=receivers)

  # ----- query other bots options -----

  def query_value(self, key, receivers=None):
    """request value via bot"""
    args = [ 'query', self.name, key ]
    self.botio.write_args(args, receivers=receivers)

  def query_all(self, receivers=None):
    self.query_value('*', receivers=receivers)

  # ----- bot answers a query -----

  def _reply_value(self, key, receivers=None):
    """answer query"""
    value = self.opts[key]
    args = [ 'value', self.name, key, str(value) ]
    self.botio.write_args(args, receivers=receivers)

  def _reply_all(self, receivers=None):
    """answer query for all"""
    for key in self.opts:
      self._reply_value(key, receivers=receivers)

  def parse_command(self, msg):
    """parse a option command. return true if command was parsed"""
    args = msg.args
    n = len(args)
    if n < 3:
      return False
    # check if its a 'query', 'push' command
    cmd = args[0]
    name = args[1]
    if name != self.name:
      return False
    if cmd == 'query' and n == 3:
      # query <name> <key>
      return self._handle_query(args[2], msg.sender)
    elif cmd == 'push' and n == 4:
      # push <name> <key> <value>
      return self._handle_push(args[2],args[3])
    else:
      return False

  def _handle_query(self, key, sender):
    if key in self.opts:
      self._reply_value(key, receivers=[sender])
      return True
    elif key == '*':
      # all entries with '*'
      self._reply_all(receivers=[sender])
      return True
    else:
      return False

  def _handle_push(self, key, value):
    if key in self.opts:
      old_value = self.opts[key]
      old_type = type(old_value)
      if old_type == int:
        try:
          value = int(value)
        except ValueError:
          return False
      elif old_type == bool:
        if value in ('true','True','1','on'):
          value = True
        elif value in ('false','False','0','off'):
          value = False
        else:
          return False
      self.set_value(key, value, True)
      return True
    else:
      return False

