import pygame

class Iconbar:
  def __init__(self):
    pass

  def setup(self, shiny, rect):
    self.shiny = shiny
    self.rect = rect

  def draw(self):
    pygame.draw.rect(self.shiny.main_surface, (0,128,64), self.rect)
