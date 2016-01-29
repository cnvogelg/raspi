from widget import Widget

class Scroller(Widget):

  IDLE = 31

  def __init__(self, pos, length, prefix=None):
    Widget.__init__(self, pos, length)
    self.buffer = bytearray(length)
    self.queue = []
    self.current = None
    if prefix is None:
      self.prefix = chr(0x7e) + " "
    else:
      self.prefix = prefix
    # set all to idle
    for i in range(length):
      self.buffer[i] = self.IDLE

  def is_busy(self):
    if len(self.queue) > 0:
      return True
    for b in self.buffer:
      if b != self.IDLE:
        return True
    return False

  def add_message(self, msg):
    self.queue.append(msg)

  def get_text(self):
    r = []
    for b in self.buffer:
      if b == self.IDLE:
        r.append(" ")
      else:
        r.append(chr(b))
    return "".join(r)

  def tick(self, ts, delta):
    busy = self.is_busy()
    c = self._get_next_char()
    if c is not None:
      self._scroll(c)
      self.set_dirty()
    elif busy:
      self._scroll(self.IDLE)
      self.set_dirty()

  def _scroll(self, new):
    for i in range(len(self.buffer)-1):
      self.buffer[i] = self.buffer[i+1]
    self.buffer[-1] = new

  def _get_next_char(self):
    """return the next char that scrolls in or None if nothing to do"""
    # fill current message?
    if self.current is None:
      if len(self.queue) > 0:
        self.current = self.prefix + self.queue.pop(0)
      else:
        return None
    # current scroll
    if len(self.current) == 0:
      self.current = None
      return self.IDLE
    new = self.current[0]
    self.current = self.current[1:]
    return ord(new)


# test
if __name__ == '__main__':
  s = Scroller((0,0),8)
  print(s.is_idle())
  print("'%s'" % s.get_text())
  if s.tick():
    print("'%s'" % s.get_text())
  else:
    print("IDLE")
  s.add_message("hello")
  for i in range(15):
    s.tick()
    if s.is_dirty:
      print("'%s'" % s.get_text())
    else:
      print("IDLE")
