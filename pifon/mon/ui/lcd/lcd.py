
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

  def __init__(self, sim=False, font_path="."):
    if sim:
      from lcdsim import LCDSim as LCD
      self._lcd = LCD(font_path=font_path)
    else:
      from adafruit.Adafruit_CharLCDPlate import Adafruit_CharLCDPlate as LCD
      self._lcd = LCD()
    self._lcd.begin(16,2)

  def clear(self):
    self._lcd.clear()

  def setCursor(self, cx, cy):
    self._lcd.setCursor(cx, cy)

  def message(self, txt):
    self._lcd.message(txt)

  def backlight(self, color):
    self._lcd.backlight(color)

  def buttonRead(self):
    return self._lcd.buttonRead()

# ----- test -----
if __name__ == '__main__':
  import time
  lcd = LCD16x2(sim=True, font_path="../../font")
  lcd.clear()
  lcd.setCursor(0,0)
  lcd.message("hello, world!")
  while True:
    but = lcd.buttonRead()
    if but & lcd.BUTTON_SELECT != 0:
      break
    lcd.setCursor(0,1)
    lcd.message("%02x" % but)
    time.sleep(0.25)

