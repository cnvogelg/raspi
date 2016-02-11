
import pygame
import os

# user interface class
class LCDSim:
  """a simulation of a 16x2 char LCD display done in PyGame"""

  BUTTON_SELECT           = 1
  BUTTON_RIGHT            = 2
  BUTTON_DOWN             = 4
  BUTTON_UP               = 8
  BUTTON_LEFT             = 16

  BLACK                   = (0,0,0)
  RED                     = (1,0,0)
  GREEN                   = (0,1,0)
  BLUE                    = (0,0,1)
  YELLOW                  = (1,1,0)
  TEAL                    = (1,0,1)
  VIOLET                  = (0,1,1)
  WHITE                   = (1,1,1)

  key_map = {
    pygame.K_RETURN : BUTTON_SELECT,
    pygame.K_SPACE : BUTTON_SELECT,
    pygame.K_LEFT : BUTTON_LEFT,
    pygame.K_RIGHT : BUTTON_RIGHT,
    pygame.K_UP : BUTTON_UP,
    pygame.K_DOWN : BUTTON_DOWN
  }

  fg_col_map = {
    BLACK : (50,50,50),
    RED : (255,0,0),
    GREEN : (0,255,0),
    BLUE : (0,0,255),
    YELLOW : (255,255,0),
    TEAL : (0,255,255),
    VIOLET : (255,0,255),
    WHITE : (255,255,255)
  }

  bg_col_map = {
    BLACK : (0,0,0),
    RED : (64,0,0),
    GREEN : (0,64,0),
    BLUE : (0,0,64),
    YELLOW : (64,64,0),
    TEAL : (0,64,64),
    VIOLET : (64,0,64),
    WHITE : (64,64,64)
  }

  # chars missing in font
  extra_char_codes = {
    # pi
    0xf7 : (0x0,0x0,0x1f,0xa,0xa,0xa,0x13,0x0),
    0xff : (0x1f,0x1f,0x1f,0x1f,0x1f,0x1f,0x1f,0x1f)
  }

  def __init__(self, size=(16,2), font_name=None, font_size=32, font_path="."):
    pygame.init()
    # setup font
    if font_name is None:
      font_name = "hd44780.ttf"
    font_file = os.path.join(font_path, font_name)
    self.font = pygame.font.Font(font_file, font_size)
    self.fy = font_size #self.font.get_height()
    self.fx,_ = self.font.size("W")
    self.of_x = self.fx
    self.of_y = self.fy / 2
    win_w = self.of_x * 2 + size[0] * self.fx
    win_h = self.of_y * 2 + size[1] * self.fy
    self.win_size = (win_w, win_h)
    # setup screen
    self.screen = pygame.display.set_mode(self.win_size)
    self.surface = pygame.Surface(self.screen.get_size())
    pygame.display.set_caption("LCDsim")
    # state
    self.button_state = 0
    self.width = size[0]
    self.height = size[1]
    self.cx = 0
    self.cy = 0
    self.bg_col = None
    self.fg_col = None
    # custom chars
    self.custom_chars = [None] * 8
    self.palette = None
    # extra chars
    self.extra_chars = {}
    for ec in self.extra_char_codes:
      data = self.extra_char_codes[ec]
      self.extra_chars[ec] = self._create_char_bitmap(data)
    # first redraw
    self.clear()
    self.set_color(*self.BLACK)

  def create_char(self, num, data):
    self.custom_chars[num] = self._create_char_bitmap(data)

  def _create_char_bitmap(self, data):
    s = pygame.Surface((5,8),0,8)
    if self.palette is None:
      self.palette = list(s.get_palette())
    y = 0
    for d in data:
      for x in xrange(5):
        bit = 1 << x
        pos = (4-x,y)
        if d & bit == bit:
          s.set_at(pos, 1)
        else:
          s.set_at(pos, 0)
      y += 1
    factor = self.fy / 8
    d = pygame.transform.scale(s, (5*factor,self.fy))
    return d

  def clear(self):
    self.data = []
    for l in xrange(self.height):
      ba = bytearray(self.width)
      ba[:] = " " * self.width
      self.data.append(ba)

  def set_cursor(self, cx, cy):
    if cx < self.width:
      self.cx = cx
    else:
      self.cx = self.width -1
    if cy < self.height:
      self.cy = cy
    else:
      self.cy = self.height - 1

  def message(self, txt):
    l = self.width - self.cx
    n = len(txt)
    if n > l:
      txt = txt[:l]
      n = l
    self.data[self.cy][self.cx:self.cx+n] = txt
    self._redraw()

  def set_color(self, r, g, b):
    tup = (r,g,b)
    for c in self.fg_col_map:
      if c == tup:
        self.bg_col = self.bg_col_map[c]
        self.fg_col = self.fg_col_map[c]
        self._redraw()
        return
    raise ValueError("set_color: invalid color: " + str(color))

  def _sane_line(self, txt):
    """remove custom chars"""
    line = ""
    for c in txt:
      if c < 32 or c > 127:
        line += " "
      else:
        line += chr(c)
    return line

  def _redraw(self):
    fg_col = self.fg_col
    bg_col = self.bg_col
    self.surface.fill(bg_col)
    yp = self.of_y
    for y in xrange(self.height):
      # build text line without custom chars
      data = self.data[y]
      line = self._sane_line(data)
      if not self._is_empty(line):
        text_surface = self.font.render(line, False, fg_col)
        self.surface.blit(text_surface, (self.of_x, yp))
      # render custom or extra chars
      xp = self.of_x
      for c in data:
        # custom char
        char_surf = None
        if c < 8:
          char_surf = self.custom_chars[c]
        elif c in self.extra_chars:
          char_surf = self.extra_chars[c]
        # render custom char
        if char_surf is not None:
          # adjust palette
          self.palette[0] = bg_col
          self.palette[1] = fg_col
          char_surf.set_palette(self.palette)
          # blit
          self.surface.blit(char_surf, (xp, yp))
        xp += self.fx
      # next line
      yp = yp + self.fy
    # show text
    self.screen.blit(self.surface, (0,0))
    pygame.display.flip()

  def _is_empty(self, l):
    for i in l:
      if i != ' ':
        return False
    return True

  def buttonRead(self):
    # poll PyGame
    event = pygame.event.poll()
    if event.type == pygame.QUIT:
      return None
    elif event.type == pygame.KEYDOWN:
      # key down
      key = event.key
      if key == pygame.K_ESCAPE:
        return None
      else:
        if key in self.key_map:
          button = self.key_map[key]
          self.button_state = self.button_state | button
    elif event.type == pygame.KEYUP:
      # key up
      key = event.key
      if key in self.key_map:
        button = self.key_map[key]
        self.button_state = self.button_state & ~button
    # return full state map
    return self.button_state
