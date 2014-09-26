import pygame
import widget
import textsurface

class Label(widget.Widget):
  def __init__(self, pane, rect, text):
    widget.Widget.__init__(self, pane, rect)
    self.text = text

  def set_text(self, text):
    self.text = text
    self._render()

  def setup(self, shiny):
    super(Label, self).setup(shiny)
    self.fg = shiny.colors.get_color(shiny.colors.LABEL_FG_COLOR)
    self.bg = shiny.colors.get_color(shiny.colors.LABEL_BG_COLOR)
    self.font = shiny.fonts.get_font(shiny.fonts.LABEL_FONT)
    self._render()

  def _render(self):
    self.surf = textsurface.TextSurface(self.text, self.font, self.fg, self.bg)

  def draw(self):
    pygame.draw.rect(self.shiny.main_surface, self.bg, self.rect_map)
    self.surf.renderInRect(self.shiny.main_surface, self.rect_map)
