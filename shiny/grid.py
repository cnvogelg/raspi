import pygame
import math

class Grid:
  def __init__(self, gy=48, gx=48):
    self.gy = gy
    self.gx = gx
    self.ox = 0
    self.oy = 0

  def set_offset(self, x, y):
    self.ox = x
    self.oy = y

  def get_offset(self):
    return (self.ox, self.oy)

  def map_x(self, x):
    return self.ox + int(x * self.gx)

  def map_y(self, y):
    return self.oy + int(y * self.gy)

  def map_pos(self, pos):
    return self.ox + int(pos[0] * self.gx), self.oy + int(pos[1] * self.gy)

  def map_len(self, len):
    return int(len[0] * self.gx), int(len[1] * self.gy)

  def map_pos_inv(self, ipos):
    x = ipos[0]
    y = ipos[1]
    if x < self.ox or y < self.oy:
      return None
    else:
      x -= self.ox
      y -= self.oy
      return (x / self.gx, y / self.gy)

  def map_rect(self, r):
    x = int(r[0] * self.gx) + self.ox
    y = int(r[1] * self.gy) + self.oy
    w = int(r[2] * self.gx)
    h = int(r[3] * self.gy)
    return pygame.Rect(x, y, w, h)

  def get_max(self, screen_max):
    x = (screen_max[0] - self.ox) / self.gx
    y = (screen_max[1] - self.oy) / self.gy
    return (x, y)

  def center(self, in_x, in_y, cells, screen):
    if in_x:
      dx = screen[0] - cells[0] * self.gx
      self.ox = dx / 2
    if in_y:
      dy = screen[1] - cells[1] * self.gy
      self.oy = dy / 2 
