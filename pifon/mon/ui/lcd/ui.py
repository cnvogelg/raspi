from __future__ import print_function
import sys

import lcd

class UI:
  def __init__(self, font_path=".", sim=False):
    self.lcd = lcd.LCD16x2(font_path=font_path, sim=sim)

  def tick(self, ts):
    """tick timer for ui. called every 0.1s"""
    pass

  def read_buttons(self):
    """return either string with pressed buttons or None if no button
       is pressed"""
    but = self.lcd.buttonRead()
    if but == 0:
      return None
    if but is None:
      return "q"
    res = ""
    if but & self.lcd.BUTTON_SELECT == self.lcd.BUTTON_SELECT:
      res += "s"
    if but & self.lcd.BUTTON_RIGHT == self.lcd.BUTTON_RIGHT:
      res += "r"
    if but & self.lcd.BUTTON_LEFT == self.lcd.BUTTON_LEFT:
      res += "l"
    if but & self.lcd.BUTTON_UP == self.lcd.BUTTON_UP:
      res += "u"
    if but & self.lcd.BUTTON_DOWN == self.lcd.BUTTON_DOWN:
      res += "d"
    return res

  # ----- audio slots -----

  def get_max_audio_slots(self):
    """return to max number of simulatinous servers"""
    return 4

  def set_num_audio_slots(self, num):
    """report the current number of used audio slots"""
    print("set_num_audio_slots", num, file=sys.stderr)

  def attach_audio_slot(self, pos, instance):
    print("attach_audio_slot:", pos, instance, file=sys.stderr)

  def remap_audio_slot(self, old_pos, new_pos, instance):
    print("remap_audio_slot:", old_pos, new_pos, instance, file=sys.stderr)

  def detach_audio_slot(self, pos, instance):
    print("detach_audio_slot:", pos, instance, file=sys.stderr)
