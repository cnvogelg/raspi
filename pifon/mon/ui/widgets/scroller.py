class Scroller(object):

  IDLE = 31

  def __init__(self, length):
    self.buffer = bytearray(length)
    self.queue = []
    self.current = None
    # set all to idle
    for i in range(length):
      self.buffer[i] = self.IDLE

  def is_idle(self):
    for b in self.buffer:
      if b != self.IDLE:
        return False
    return True

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

  def tick(self):
    idle = self.is_idle()
    c = self._get_next_char()
    if c is not None:
      self._scroll(c)
      return True
    elif not idle:
      self._scroll(self.IDLE)
      return True
    else:
      return False

  def _scroll(self, new):
    for i in range(len(self.buffer)-1):
      self.buffer[i] = self.buffer[i+1]
    self.buffer[-1] = new

  def _get_next_char(self):
    """return the next char that scrolls in or None if nothing to do"""
    # fill current message?
    if self.current is None:
      if len(self.queue) > 0:
        self.current = self.queue.pop(0)
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
  s = Scroller(8)
  print(s.is_idle())
  print("'%s'" % s.get_text())
  if s.tick():
    print("'%s'" % s.get_text())
  else:
    print("IDLE")
  s.add_message("hello")
  for i in range(15):
    if s.tick():
      print("'%s'" % s.get_text())
    else:
      print("IDLE")
