
class LCD16x2:
  """a wrapper class to control either an Adafruit HW display via I2C
     or run a LCD simulator via pygame"""

  BUTTON_SELECT           = 1
  BUTTON_RIGHT            = 2
  BUTTON_DOWN             = 4
  BUTTON_UP               = 8
  BUTTON_LEFT             = 16

  ALL_BUTTONS = (BUTTON_SELECT, BUTTON_RIGHT, BUTTON_DOWN, BUTTON_UP, BUTTON_LEFT)

  OFF                     = (0,0,0)
  RED                     = (1,0,0)
  GREEN                   = (0,1,0)
  BLUE                    = (0,0,1)
  YELLOW                  = (1,1,0)
  TEAL                    = (0,1,1)
  VIOLET                  = (1,0,1)
  WHITE                   = (1,1,1)
  ON                      = (1,1,1)

  pi_char = chr(0xf7)

  # custom chars
  play_char = chr(0)
  bell_char = chr(1)

  # bar chars from 0 to 8
  bar_chars = (chr(32),chr(1),chr(2),chr(3),chr(4),chr(5),chr(6),chr(7),chr(0xff))

  # custom chars (5x8 pixels)
  # (source http://www.quinapalus.com/hd44780udg.html)
  custom_chars = (
    # 0: play
    ( 0x0,0x8,0xc,0xe,0xc,0x8,0x0,0x0 ),
    # 1: 1 px bar
    ( 0,0,0,0,0,0,0,0x1f ),
    # 2: 2 px bar
    ( 0,0,0,0,0,0,0x1f,0x1f ),
    # 3: 3 px bar
    ( 0,0,0,0,0,0x1f,0x1f,0x1f ),
    # 4: 4 px bar
    ( 0,0,0,0,0x1f,0x1f,0x1f,0x1f ),
    # 5: 5 px bar
    ( 0,0,0,0x1f,0x1f,0x1f,0x1f,0x1f ),
    # 6: 6 px bar
    ( 0,0,0x1f,0x1f,0x1f,0x1f,0x1f,0x1f ),
    # 7: 7 px bar
    ( 0,0x1f,0x1f,0x1f,0x1f,0x1f,0x1f,0x1f )
  )

  def __init__(self, sim=False, font_path="."):
    if sim:
      from lcdsim import LCDSim as LCD
      self._lcd = LCD(font_path=font_path)
      self._sim = True
    else:
      import Adafruit_CharLCD as LCD
      self._lcd = LCD.Adafruit_CharLCDPlate()
      self._sim = False
    # load custom chars
    num = 0
    for data in self.custom_chars:
      self._lcd.create_char(num, list(data))
      num += 1
    # button map
    if not self._sim:
      self._button_map = {
        self.BUTTON_SELECT : LCD.SELECT,
        self.BUTTON_LEFT : LCD.LEFT,
        self.BUTTON_RIGHT : LCD.RIGHT,
        self.BUTTON_UP : LCD.UP,
        self.BUTTON_DOWN : LCD.DOWN
      }

  def off(self):
    self.backlight(self.OFF)

  def clear(self):
    self._lcd.clear()

  def text(self, cx, cy, txt):
    self._lcd.set_cursor(cx, cy)
    self._lcd.message(txt)

  def backlight(self, color):
    self._lcd.set_color(*color)

  def buttonRead(self):
    if self._sim:
      return 0
    else:
      result = 0
      for button in self.ALL_BUTTONS:
        if self._lcd.is_pressed(self._button_map[button]):
          result |= button
      return result


def autodetect_sim():
  """check if we can use the sim or the real thing
     return True for sim, False for real, None if neither is possible
  """
  # real one needs smbus
  try:
    import smbus
    return False
  except ImportError:
    pass
  # sim needs pygame
  try:
    import pygame
    return True
  except ImportError:
    return None


# ----- test -----
if __name__ == '__main__':
  import time
  sim = autodetect_sim()
  if sim is None:
    print("Neither sim nor real LCD available!")
  lcd = LCD16x2(sim=sim, font_path="../../font")
  lcd.clear()
  lcd.text(0,0,lcd.pi_char + "hello, world!")
  off = 7
  for c in lcd.bar_chars:
    lcd.text(off,1,c)
    off += 1
  on = True
  col_map = (lcd.RED, lcd.GREEN, lcd.BLUE, lcd.WHITE)
  col = 0
  try:
    while True:
      but = lcd.buttonRead()
      if but is None or but == 0xc:
        break
      if but == 1:
        if not on:
          on = True
      if on:
        col = (col + 1) % 4
        lcd.text(4,1,"%d" % col)
        lcd.backlight(col_map[col])
        on = False
      lcd.text(0,1,"%02x" % but)
      time.sleep(0.25)
  except KeyboardInterrupt:
    pass
  finally:
    lcd.off()
    print("bye")
