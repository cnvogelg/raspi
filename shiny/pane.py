import control

class Pane:
  def __init__(self, title):
    self.title = title
    self.widgets = []
    self.controls = []

  def add_widget(self, w):
    self.widgets.append(w)
    if isinstance(w, control.Control):
      self.controls.append(w)

  def setup(self, shiny):
    self.shiny = shiny
    for w in self.widgets:
      w.setup(shiny)

  def handle_event(self, event):
    for w in self.controls:
      rect = w.rect
      if event.is_in_rect(rect):
        return w.handle_event(event)
    return False

  def draw(self):
    for w in self.widgets:
      w.draw()
