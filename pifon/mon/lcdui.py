#!/usr/bin/env python
# using an LCD with the pifon
#
# I use an Adafruit LCD Plate for the Raspi here
# http://learn.adafruit.com/adafruit-16x2-character-lcd-plus-keypad-for-raspberry-pi 
#

import time
from contrib.Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from ui import UI

# user interface class
class LCDUI(UI):
  def __init__(self):
    # setup display
    self.lcd = Adafruit_CharLCDPlate()
    self.lcd.begin(16, 2)
    self.lcd.clear()
    # init state
    self.last_mask = 0
    self.num_buttons = 5
    self.last_repeat = []
    self.first_flag = []
    self.start_time = 0.5
    self.repeat_time = 0.2
    self.clear_line = " " * 16
    self.last_value_len = 0
    self.last_status_len = 0
    self.last_msg_len = 0
    self.last_back = self.BACK_OFF
    for i in xrange(self.num_buttons):
      self.last_repeat.append([0])
      self.first_flag.append(True)
    # map buttons
    self.map = {
      self.lcd.BUTTON_SELECT : self.EVENT_PICK,
      self.lcd.BUTTON_RIGHT  : self.EVENT_INC,
      self.lcd.BUTTON_LEFT   : self.EVENT_DEC,
      self.lcd.BUTTON_DOWN   : self.EVENT_NEXT,
      self.lcd.BUTTON_UP     : self.EVENT_PREV
    }
    # map background
    self.map_back = {
      self.BACK_OFF : self.lcd.OFF,
      self.BACK_WHITE : self.lcd.WHITE,
      self.BACK_RED : self.lcd.RED,
      self.BACK_GREEN : self.lcd.GREEN,
      self.BACK_BLUE : self.lcd.BLUE,
      self.BACK_YELLOW : self.lcd.YELLOW,
      self.BACK_TEAL : self.lcd.TEAL,
      self.BACK_VIOLET : self.lcd.VIOLET
    }

  def shutdown(self):
    self.lcd.clear()
    self.lcd.noDisplay()
    self.lcd.backlight(self.lcd.OFF)

  def update_background(self, back):
    """update background"""
    if back != self.last_back:
      self.last_back = back
      mapped_back = self.map_back[back]
      self.lcd.backlight(mapped_back)
      
  def show_menu(self, title):
    """start showing a menu"""
    # limit to 8 chars
    t = (title + " " * 8)[:8]
    t += " " * 8
    self.last_value_len = 0
    self.lcd.setCursor(0,1)
    self.lcd.message(t)
  
  def hide_menu(self):
    self.show_menu("")
  
  def _update_value(self, value, last_len, size, pad_right=False):
    """update value and return (txt, pos, new_last_len)"""
    t = str(value)
    n = len(t)
    # limit to n chars
    if n > size:
      t = t[:size]
      n = size
    # overwrite last value
    if n < last_len: 
      d = last_len - n
      if pad_right:
        t = t + (" " * d)
      else:
        t = (" " * d) + t
    pos = size - len(t)
    return (t, pos, n)
  
  def update_menu_value(self, value):
    """update a value change in the menu"""
    (txt, pos, self.last_value_len) = self._update_value(value, self.last_value_len, 4)
    self.lcd.setCursor(pos + 12,1)
    self.lcd.message(txt)

  def update_title(self, title):
    """update the title message"""
    self.lcd.setCursor(0,0)
    self.lcd.message(title)

  def update_status(self, status):
    """update the status bar"""
    (txt, pos, self.last_status_len) = self._update_value(status, self.last_status_len, 10)
    self.lcd.setCursor(pos + 6,0)
    self.lcd.message(txt)
  
  def show_message(self, msg):
    """if no menu is shown then you can show a message"""
    self.last_msg_len = 16
    self.update_message(msg)
  
  def update_message(self, msg):
    (txt, pos, self.last_msg_len) = self._update_value(msg, self.last_msg_len, 16, True)
    self.lcd.setCursor(0,1)
    self.lcd.message(txt)    
  
  def hide_message(self):
    """if a message is shown then hide it"""
    self.update_message("")
  
  def get_next_event(self):
    """return the next button event or 0 if no event occurred"""
    # check for new press
    mask = self.lcd.buttonRead()
    changes = (self.last_mask ^ mask) & mask
    self.last_mask = mask
    # any button newly pressed
    ts = time.time()
    result = 0
    if changes != 0:
      for i in xrange(self.num_buttons):
        if changes & (1<<i) != 0:
          # store begin of press
          self.last_repeat[i] = ts
          self.first_flag[i] = True
      result = mask
    elif mask != 0:
      # check for auto-repeat
      for i in xrange(self.num_buttons):
        if mask & (1<<i) != 0:
          delta = ts - self.last_repeat[i]
          flag = self.first_flag[i]
          # first repeat
          if flag:
            if delta > self.start_time:
              result |= 1<<i
              self.last_repeat[i] = ts
              self.first_flag[i] = False
          # continious repeat
          else:
            if delta > self.repeat_time:
              result |= 1<<i
              self.last_repeat[i] = ts
    if result == 0:
      return 0
    else:
      # map button
      mapped_result = 0
      for e in self.map:
        if result & e == e:
          mapped_result |= self.map[e]
      return mapped_result

# ----- test -----
if __name__ == '__main__':
  print("LCDUI test")
  ui = LCDUI()
  val = 0
  val2 = 0
  in_menu = False
  ui.show_message("<select> = menu")
  while True:
    ev = ui.get_next_event()
    if ev & ui.EVENT_PICK:
      if in_menu:
        ui.hide_menu()
        ui.show_message("<select> = menu")
        in_menu = False
      else:
        ui.hide_message()
        ui.show_menu("test")
        ui.update_menu_value(val)
        in_menu = True
    if ev & ui.EVENT_INC:
      if in_menu:
        val += 1
        ui.update_menu_value(val)
    elif ev & ui.EVENT_DEC:
      if in_menu:
        val -= 1
        ui.update_menu_value(val)
    if ev & ui.EVENT_NEXT:
      val2 += 1
      ui.update_status(val2)
    time.sleep(0.1)
  