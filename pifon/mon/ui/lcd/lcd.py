
class LCD16x2:
  """a wrapper class to control either an Adafruit HW display via I2C
     or run a LCD simulator via pygame"""

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
    else:
      from adafruit.Adafruit_CharLCDPlate import Adafruit_CharLCDPlate as LCD
      self._lcd = LCD()
    self._lcd.begin(16,2)
    # load custom chars
    num = 0
    for data in self.custom_chars:
      self._lcd.createChar(num, list(data))
      num += 1

  def off(self):
    self.backlight(0)

  def clear(self):
    self._lcd.clear()

  def text(self, cx, cy, txt):
    self._lcd.setCursor(cx, cy)
    self._lcd.message(txt)

  def backlight(self, color):
    self._lcd.backlight(color)

  def buttonRead(self):
    return self._lcd.buttonRead()


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
  col = 6
  try:
    while True:
      but = lcd.buttonRead()
      if but is None or but == 0xc:
        break
      if but == 1:
        if not on:
          on = True
      if on:
        col = (col + 1) % 8
        lcd.text(4,1,"%d" % col)
        lcd.backlight(col)
        on = False
      lcd.text(0,1,"%02x" % but)
      time.sleep(0.25)
  except KeyboardInterrupt:
    pass
  finally:
    lcd.off()
    print("bye")
