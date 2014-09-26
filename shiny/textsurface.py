import pygame

class TextSurface:
  """keep a cached surface of a given text and additional layout info"""

  def __init__(self, text, font, color, bg_color=None):
    self.text = text
    self.font = font
    self.color = color
    # render text to surface
    self.surf = self.font.render(self.text, True, color, bg_color)
    r = self.surf.get_rect()
    self.h = r.h
    self.w = r.w

  ALIGN_CENTER=0
  ALIGN_MIN=1
  ALIGN_MAX=2

  def renderInRect(self, dst, rect, x_align=ALIGN_CENTER, y_align=ALIGN_CENTER):
    if rect.w < self.w:
      # crop x
      dx = self.w - rect.w
      if x_align == self.ALIGN_CENTER:
        ax = dx // 2
      elif x_align == self.ALIGN_MIN:
        ax = 0
      else:
        ax = dx 
      px = rect.x
    else:
      # no crop x
      cx = 0
      ax = 0
      dx = rect.w - self.w
      if x_align == self.ALIGN_CENTER:
        px = rect.x + dx // 2
      elif x_align == self.ALIGN_MIN:
        px = rect.x
      else:
        px = rect.x + dx

    if rect.h < self.h:
      # crop y
      dy = self.h - rect.h
      if y_align == self.ALIGN_CENTER:
        ay = dy // 2
      elif y_align == self.ALIGN_MIN:
        ay = 0
      else:
        ay = dy
      py = rect.y
    else:
      # no crop y
      cy = 0
      ay = 0
      dy = rect.h - self.h
      if y_align == self.ALIGN_CENTER:
        py = rect.y + dy // 2
      elif y_align == self.ALIGN_MIN:
        py = rect.y
      else:
        py = rect.y + dy

    # clip and blit 
    area = pygame.Rect(ax, ay, self.w, self.h)
    dst.blit(self.surf, (px, py), area)
