
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
  stop_char = chr(1)
  heart_a_char = chr(2)
  heart_b_char = chr(3)
  speaker_char = chr(4)
  note_char = chr(5)
  hourglass_char = chr(6)
  bell_char = chr(7)

  all_chars = chr(0)+chr(1)+chr(2)+chr(3)+chr(4)+chr(5)+chr(6)+chr(7)

  # custom chars (5x8 pixels)
  # (source http://www.quinapalus.com/hd44780udg.html)
  custom_chars = (
    # 0: play
    ( 0x0,0x8,0xc,0xe,0xc,0x8,0x0,0x0 ),
    # 1: stop
    ( 0x0,0x1f,0x1f,0x1f,0x1f,0x1f,0x0,0x0 ),
    # 2: hearbeat A
    ( 0x0,0x0,0xa,0x15,0x11,0xa,0x4,0x0 ),
    # 3: hearbeat B
    ( 0x0,0x0,0xa,0x1f,0x1f,0xe,0x4,0x0 ),
    # 4: speaker
    ( 0x1,0x3,0xf,0xf,0xf,0x3,0x1,0x0 ),
    # 5: note
    ( 0x2,0x3,0x2,0x2,0xe,0x1e,0xc,0x0 ),
    # 6: hourglass
    ( 0x1f,0x11,0xa,0x4,0xa,0x11,0x1f,0x0 ),
    # 7: bell
    ( 0x4,0xe,0xe,0xe,0x1f,0x0,0x4,0x0 )
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
      self._lcd.createChar(num, data)
      num += 1

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
  lcd.text(7,1,lcd.all_chars)
  while True:
    but = lcd.buttonRead()
    if but is None:
      break
    lcd.text(0,1,"%02x" % but)
    time.sleep(0.25)

