from __future__ import print_function
import sys

import lcd
import ui.widgets

class UI:

  FLAG_CLEAR = 1
  FLAG_CLOCK = 2
  FLAG_SCROLLER = 4

  def __init__(self, font_path=".", sim=False):
    self.lcd = lcd.LCD16x2(font_path=font_path, sim=sim)
    self.clock = ui.widgets.Clock()
    self.scroller = ui.widgets.Scroller(8)
    self.redraw_flag = 0
    self.scroller.add_message("Welcome to pifon!")

  def _p(self, *args, **kwargs):
    a = ["**UI**"] + list(args)
    print(*a,file=sys.stderr,**kwargs)

  def get_tick_interval(self):
    return 0.25

  def on_tick(self, ts, delta):
    """tick timer for ui. called every 0.25s"""
    b = self._read_buttons()
    if b is not None:
      self._p("buttons:", b)
      # quit bot?
      if 'q' in b:
        return False
    # update widgets
    self._update_widgets()
    # redraw?
    if self.redraw_flag:
      self._redraw()

  def _update_widgets(self):
    # clock needs redraw?
    if self.clock.tick():
      self.redraw_flag |= self.FLAG_CLOCK
    # scroller needs redraw?
    if self.scroller.tick():
      self.redraw_flag |= self.FLAG_SCROLLER

  def _redraw(self):
    f = self.redraw_flag
    # clear lcd screen?
    if f & self.FLAG_CLEAR == self.FLAG_CLEAR:
      self.lcd.clear()
    # update clock?
    if f & self.FLAG_CLOCK == self.FLAG_CLOCK:
      txt = self.clock.get_text()
      self.lcd.text(0,0,txt)
    # update scroller?
    if f & self.FLAG_SCROLLER == self.FLAG_SCROLLER:
      txt = self.scroller.get_text()
      self.lcd.text(8,0,txt)
    # done
    self.redraw_flag = 0

  def _read_buttons(self):
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

  # audio calls

  def audio_add(self, a):
    self._p("audio_add", a)

  def audio_del(self, a):
    self._p("audio_del", a)

  def audio_update(self, a, flags):
    self._p("audio_update", a, flags)

  # player calls

  def player_add(self, p):
    self._p("player_add", p)

  def player_del(self, p):
    self._p("player_del", p)

  def player_update(self, p, flags):
    self._p("player_update", p, flags)
