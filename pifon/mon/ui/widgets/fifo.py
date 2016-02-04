from widget import Widget

class Fifo(Widget):

  def __init__(self, pos, width):
    Widget.__init__(self, pos, width)
    self.width = width
    self.text = " " * width

  def add(self, char):
    self.text = self.text[1:] + char
    self.set_dirty()

  def clear(self):
    self.text = " " * self.width
    self.set_dirty()

  def get_text(self):
    return self.text


# test
if __name__ == '__main__':
  f = Fifo((0,0),4)
  for i in range(10):
    print("'%s'" % f.get_text())
    f.add(chr(64+i))
