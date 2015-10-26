
import pygame

# user interface class
class LCDSim:
  """a simulation of a 16x2 char LCD display done in PyGame"""

  BUTTON_SELECT           = 1
  BUTTON_RIGHT            = 2
  BUTTON_DOWN             = 4
  BUTTON_UP               = 8
  BUTTON_LEFT             = 16

  OFF                     = 0x00
  RED                     = 0x01
  GREEN                   = 0x02
  BLUE                    = 0x04
  YELLOW                  = RED + GREEN
  TEAL                    = GREEN + BLUE
  VIOLET                  = RED + BLUE
  WHITE                   = RED + GREEN + BLUE
  ON                      = RED + GREEN + BLUE

  key_map = {
    pygame.K_RETURN : BUTTON_SELECT,
    pygame.K_SPACE : BUTTON_SELECT,
    pygame.K_LEFT : BUTTON_LEFT,
    pygame.K_RIGHT : BUTTON_RIGHT,
    pygame.K_UP : BUTTON_UP,
    pygame.K_DOWN : BUTTON_DOWN
  }

  fg_col_map = {
    OFF : (0,0,0),
    RED : (255,0,0),
    GREEN : (0,255,0),
    BLUE : (0,0,255),
    YELLOW : (255,255,0),
    TEAL : (0,255,255),
    VIOLET : (255,0,255),
    WHITE : (255,255,255)
  }

  bg_col_map = {
    OFF : (0,0,0),
    RED : (64,0,0),
    GREEN : (0,64,0),
    BLUE : (0,0,64),
    YELLOW : (64,64,0),
    TEAL : (0,64,64),
    VIOLET : (64,0,64),
    WHITE : (64,64,64)
  }

  def __init__(self, size=(16,2), font_name=None, font_size=32):
    pygame.init()
    # setup font
    if font_name is None:
      font_name = "font/hd44780.ttf"
    self.font = pygame.font.Font(font_name, font_size)
    self.fy = self.font.get_height()
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
    self.begin(16, 2)
    self.cx = 0
    self.cy = 0
    self.bg_col = self.OFF
    self._redraw()

  def begin(self, width, height):
    self.width = width
    self.height = height
    self.clear()

  def clear(self):
    self.data = []
    for l in xrange(self.height):
      ba = bytearray(self.width)
      ba[:] = " " * self.width
      self.data.append(ba)

  def setCursor(self, cx, cy):
    self.cx = cx
    self.cy = cy

  def message(self, txt):
    l = self.width - self.cx
    n = len(txt)
    if n > l:
      txt = txt[:l]
      n = l
    self.data[self.cy][self.cx:self.cx+n] = txt
    self._redraw()

  def backlight(self, color):
    self.bg_col = color
    self._redraw()

  def _redraw(self):
    fg_col = self.fg_col_map[self.bg_col]
    bg_col = self.bg_col_map[self.bg_col]
    self.surface.fill(bg_col)
    yp = self.of_y
    for y in xrange(self.height):
      line = str(self.data[y])
      if not self._is_empty(line):
        text_surface = self.font.render(line, False, fg_col)
        self.surface.blit(text_surface, (self.of_x, yp))
      yp = yp + self.fy
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