class Widget(object):
  """base class for all UI elements"""

  def __init__(self, pane, rect):
    self.rect = rect
    self.pane = pane
    pane.add_widget(self)

  def setup(self, shiny):
    self.shiny = shiny
    # map rect of widget
    self.rect_map = shiny.screen.grid.map_rect(self.rect)
