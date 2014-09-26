import pygame
import os
import sys
import inspect

class Fonts:
  BUTTON_FONT = 0
  LABEL_FONT = 1
  STATUS_FONT = 2

  def __init__(self):
    my_dir = os.path.split(inspect.getfile( inspect.currentframe() ))[0]
    self.dir = os.path.realpath(os.path.abspath(os.path.join(my_dir,"fonts")))
    self.font_desc = {
      self.BUTTON_FONT : ("Roboto/Roboto-Medium.ttf", 36),
      self.LABEL_FONT : ("Roboto/Roboto-Light.ttf", 36),
      self.STATUS_FONT : ("Roboto/Roboto-Regular.ttf", 18)
    }

  def setup(self):
    self.fonts = {}
    # create fonts
    for i in self.font_desc:
      (name, size) = self.font_desc[i]
      path = os.path.join(self.dir, name)
      self.fonts[i] = pygame.font.Font(path, size)

  def get_font(self, i):
    return self.fonts[i]
