import pygame

from grid import Grid

class Screen:
  def __init__(self, size, grid=None):
    self.size = size
    if grid is None:
      self.grid = Grid()
    else:
      self.grid = grid
    self.statusbar = None
    self.iconbar = None
    self.pane = None

  def set_pane(self, pane):
    self.pane = pane

  def set_statusbar(self, bar):
    self.statusbar = bar

  def set_iconbar(self, bar):
    self.iconbar = bar

  def setup(self, shiny):
    self.shiny = shiny
    self.screen = pygame.display.set_mode(self.size)
    self.rect = self.screen.get_rect()
    self._setup_grid()
    
    # setup statusbar
    if self.statusbar is not None:
      rect = pygame.Rect(0,0,self.rect.w,24)
      self.statusbar.setup(shiny, rect)

    # setup iconbar
    if self.iconbar is not None:
      y = self.grid_rect.h + self.grid_rect.y
      h = self.rect.h - y
      w = self.rect.w
      rect = pygame.Rect(0,y,w,h)
      self.iconbar.setup(shiny, rect)

    # pane setup with widgets
    if self.pane is not None:
      self.pane.setup(shiny)

  def _setup_grid(self):
    # set grid offset
    if self.statusbar is not None:
      self.grid.set_offset(0,24)
    # get max grid pos
    screen_max = (self.rect.w, self.rect.h)
    max_pos = self.grid.get_max(screen_max)
    # center grid along x
    self.grid.center(True, False, max_pos, screen_max)
    # icon bar height
    if self.iconbar is not None:
      max_pos = (max_pos[0], max_pos[1]-1)
    self.max_pos = max_pos
    # get grid rect
    mx = self.grid.map_len(self.max_pos)
    of = self.grid.get_offset()
    self.grid_rect = pygame.Rect(of[0], of[1], mx[0], mx[1])

  def handle_event(self, event):
    if self.pane is not None:
      return self.pane.handle_event(event)
    else:
      return False

  def draw(self):
    # draw grid area
    pygame.draw.rect(self.shiny.main_surface, (100,100,100), self.grid_rect)

    # status bar
    if self.statusbar is not None:
      self.statusbar.draw()

    # icon bar
    if self.iconbar is not None:
      self.iconbar.draw()

    # draw pane
    if self.pane is not None:
      self.pane.draw()
