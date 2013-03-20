from __future__ import print_function
import sys

class BotOpts:
  """manage a dictionary of key,value options
     and allow them to be modified via bot commands
  """
  
  def __init__(self, botio, name, opts, broadcast=False):
    self.botio = botio
    self.name = name
    self.opts = opts
    self.broadcast = broadcast
    self.notify = None
    
  def set_notifier(self, notify):
    self.notify = notify
  
  def get_value(self, key):
    return self.opts[key]
    
  def set_value(self, key, value, from_bot=False):
    self.opts[key] = value
    # broadcase value
    if self.broadcast:
      self.send_value(key)
    # notify about value change
    if from_bot and self.notify != None:
      self.notify(key, value)
    
  def send_value(self, key):
    """current value is send via bot"""
    value = self.opts[key]  
    args = [ 'set', self.name, key, str(value) ]
    self.botio.write_args(args)

  def send_all(self):
    for key in self.opts:
      self.send_value(key)

  def query_value(self, key):
    """request value via bot"""
    args = [ 'get', self.name, key ]
    self.botio.write_args(args)
  
  def query_all(self):
    self.query_value('*')
  
  def parse_command(self, args):
    """parse a option command. return true if command was parsed"""
    n = len(args)
    if n < 3:
      return False
    # check if its a 'set', 'get' command
    cmd = args[0]
    name = args[1]
    if name != self.name:
      return False
    if cmd == 'get' and n == 3:
      # get <name> <key> 
      return self.handle_get(args[2])
    elif cmd == 'set' and n == 4:
      # set <name> <key> <value>
      return self.handle_set(args[2],args[3])
    else:
      return False
  
  def handle_get(self, key):
    if key in self.opts:
      self.send_value(key)
      return True
    elif key == '*':
      # all entries with '*'
      for key in self.opts:
        self.send_value(key)
    else:
      return False
  
  def handle_set(self, key, value):
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
      
