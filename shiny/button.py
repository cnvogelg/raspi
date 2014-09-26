import pygame
import control
import textsurface
import event

class Button(control.Control):
  def __init__(self, pane, rect, text, handler=None):
    control.Control.__init__(self, pane, rect)
    self.text = text
    self.active = False
    self.handler = handler

  def __str__(self):
    return "[Button:%s]" % (self.text)

  def setup(self, shiny):
    super(Button, self).setup(shiny)
    # get font
    font = shiny.fonts.get_font(shiny.fonts.BUTTON_FONT)
    # get colors
    self.fg = shiny.colors.get_color(shiny.colors.BUTTON_FG_COLOR)
    self.bg = shiny.colors.get_color(shiny.colors.BUTTON_BG_COLOR)
    self.bd = shiny.colors.get_color(shiny.colors.BUTTON_BD_COLOR)
    self.fga = shiny.colors.get_color(shiny.colors.BUTTON_FG_ACTIVE_COLOR)
    self.bga = shiny.colors.get_color(shiny.colors.BUTTON_BG_ACTIVE_COLOR)
    self.bda = shiny.colors.get_color(shiny.colors.BUTTON_BD_ACTIVE_COLOR)
    # render text surfaces
    self.surf = textsurface.TextSurface(self.text, font, self.fg, self.bg)
    self.surfa = textsurface.TextSurface(self.text, font, self.fga, self.bga)
    # map button
    r = self.rect_map
    self.trect_map = pygame.Rect(r[0]+1, r[1]+1, r[2]-2, r[3]-2)

  def draw(self):
    if self.active:
      bg = self.bga
      bd = self.bda
      s = self.surfa
    else:
      bg = self.bg
      bd = self.bd
      s = self.surf
    # draw background, border, and blit text
    pygame.draw.rect(self.shiny.main_surface, bg, self.rect_map)
    pygame.draw.rect(self.shiny.main_surface, bd, self.rect_map, 1)
    s.renderInRect(self.shiny.main_surface, self.trect_map)

  def handle_event(self, ev):
    if ev.type == event.Event.BUTTON_DOWN:
      if not self.active:
        self.active = True
        if self.handler is not None:
          self.handler(self)
        return True
    elif ev.type == event.Event.BUTTON_UP:
      if self.active:
        self.active = False
        return True
    return False
