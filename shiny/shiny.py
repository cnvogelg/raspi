import pygame

from fonts import Fonts
from grid import Grid
from colors import Colors
from event import Event

class Shiny:
  """main class for shiny UI"""

  def __init__(self, screen, fonts=None, colors=None):
    self.screen = screen
    
    if fonts is None:
      self.fonts = Fonts()
    else:
      self.fonts = fonts

    if colors is None:
      self.colors = Colors()
    else:
      self.colors = colors

  def _handle_event(self, ev, event_type):
    pos = ev.pos
    mpos = self.screen.grid.map_pos_inv(pos)
    if mpos is not None:
      sev = Event(event_type, mpos)
      return self.screen.handle_event(sev)
    else:
      return False

  def run(self, framerate=60):
    pygame.init()

    self.main_surface = pygame.display.set_mode(self.screen.size)
    self.fonts.setup()

    self.screen.setup(self)

    clock = pygame.time.Clock()
    done = False
    dirty = False
    init = True
    while not done:
      # handle events
      for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
          done = True
        elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
          done = True
        elif ev.type == pygame.MOUSEBUTTONDOWN:
          dirty = self._handle_event(ev, Event.BUTTON_DOWN)
        elif ev.type == pygame.MOUSEBUTTONUP:
          dirty = self._handle_event(ev, Event.BUTTON_UP)
        elif ev.type == pygame.MOUSEMOTION:
          dirty = self._handle_event(ev, Event.MOUSE_MOVE)

      if dirty or init:
        self.screen.draw()
        pygame.display.flip()
        dirty = False
        init = False

      clock.tick(framerate)
