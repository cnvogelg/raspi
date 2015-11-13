from __future__ import print_function

class BotOptField:
  """hold a field of the bot options"""
  def __init__(self, name, typ, value, desc=None, val_range=None):
    self.name = name
    self.typ = typ
    self.value = value
    self.range = val_range
    self.desc = desc

  @staticmethod
  def parse(args):
    if isinstance(args,str):
      args = args.split(" ")
    n = len(args)
    if n < 3:
      return None
    # name
    name = args[0]
    # typ
    typ_str = args[1]
    if typ_str == 'bool':
      typ = bool
    elif typ_str == 'int':
      typ = int
    elif typ_str == 'str':
      typ = str
    else:
      return None
    # value
    try:
      value = args[2]
      if typ == bool:
        if value == 'True':
          value = True
        elif value == 'False':
          value = False
        else:
          return None
      else:
        value = typ(value)
    except ValueError:
      return None
    # optional range [min,max]
    if n > 3:
      o = 3
      if args[o][0] == '[':
        nob = args[o][1:-1]
        el = nob.split(',')
        if len(el) != 2:
          return None
        val_range = [typ(el[0]), typ(el[1])]
        o += 1
      else:
         val_range = None
      # desc
      if n > o:
        desc = " ".join(args[o:])
      else:
        desc = None
    else:
      val_range = None
      desc = None
    return BotOptField(name, typ, value, val_range=val_range, desc=desc)

  def __str__(self):
    res = [self.name, self.typ.__name__, str(self.value)]
    if self.range is not None:
      res.append(str(self.range).replace(" ",""))
    if self.desc is not None:
      res.append(self.desc)
    return " ".join(res)

  def get(self):
    return self.value

  def set(self, value):
    # bool conversion
    if self.typ is bool:
      if value == 'True':
        value = True
      elif value == 'False':
        value = False
    # int conversion
    elif self.typ is int:
      if isinstance(value, str):
        try:
          value = int(value)
        except ValueError:
          return False
    # auto convert to type
    if not isinstance(value, self.typ):
      return False
    # check range
    if self.range is not None:
      if value < self.range[0]:
        return False
      if value > self.range[1]:
        return False
    # really changes value
    if self.value != value:
      self.value = value
      return True
    else:
      return None

# ----- Test -----
if __name__ == '__main__':
  # mini bool
  bf1 = BotOptField("bla", bool, False)
  bf1s = str(bf1)
  print("obj=",bf1)
  print("str=",bf1s)
  bf1c = BotOptField.parse(bf1s)
  print("par=",bf1c)
  bf1.set("True")
  print("true=",bf1)
  bf1.set("False")
  print("false=",bf1)
  # int
  bf2 = BotOptField("foo", int, 10, val_range=[0,100], desc="hello, world!")
  bf2s = str(bf2)
  print("obj=",bf2)
  print("str=",bf2s)
  bf2c = BotOptField.parse(bf2s)
  print("par=",bf2c)
  print(bf2.set(200))
  print(bf2.set(20))
  # string
  bf3 = BotOptField("bar", str, "val", desc="hello, world!")
  bf3s = str(bf3)
  print("obj=",bf3)
  print("str=",bf3s)
  bf3c = BotOptField.parse(bf3s)
  print("par=",bf3c)

