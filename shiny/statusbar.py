import pygame

class Statusbar:
  def __init__(self, title):
    self.title = title

  def setup(self, shiny, rect):
    self.shiny = shiny
    self.rect = rect

  def draw(self):
    pygame.draw.rect(self.shiny.main_surface, (0,128,0), self.rect)
