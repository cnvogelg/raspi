from __future__ import print_function

class BotCmd:
  """a bot command"""
  def __init__(self, name, arg_types=None, callee=None):
    self.name = name
    self.arg_types = arg_types
    self.callee = callee

  def get_name(self):
    return self.name

  def handle_cmd(self, args, sender):
    """check if an argument list matches the command"""
    n = len(args)
    # command given?
    if n == 0:
      return "No command given"
    # check name
    cmd = args[0]
    if cmd != self.name:
      return False
    # no arguments
    if self.arg_types is None:
      if n != 1:
        return "Extra args given"
      self.callee(sender)
      return True
    # check args
    else:
      if n != len(self.arg_types) + 1:
        return "Wrong number of args"
      params = []
      off = 1
      for t in self.arg_types:
        res = self._parse_arg(t, args[off])
        if res is None:
          return "Wrong argument @" + off
        off += 1
        params.append(res)
      self.callee(sender, params)
      return True

  def _parse_arg(self, t, a):
    if t is str:
      return a
    elif t is bool:
      al = a.lower()
      if al in ('true', '1', 'on'):
        return True
      elif al in ('false', '0', 'off'):
        return False
      else:
        return None
    elif t is int:
      try:
        return int(a)
      except ValueError:
        return None
    else:
      return None


# ----- test -----
if __name__ == '__main__':
  bc = BotCmd("bla", arg_types=(str, bool, int), callee=print)
  res = bc.handle_cmd(["bla","hello","true","42"],"me")
  print(res)
