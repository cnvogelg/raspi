from __future__ import print_function
import sys

import lcd
import ui.widgets

class UI:

  def __init__(self, cfg):
    self.cfg = cfg
    self.lcd = self._setup_lcd()
    self.widgets = []
    # clock
    self.clock = ui.widgets.Clock((0,0))
    self.widgets.append(self.clock)
    # scroller
    self.scroller = ui.widgets.Scroller((0,0),16)
    self.scroller.add_message("pifon2")
    self.scroller.show(False)
    self.widgets.append(self.scroller)
    # audio - reserve two instances
    a0 = ui.widgets.AudioShow((0,1), 0, self.lcd.bar_chars)
    a1 = ui.widgets.AudioShow((5,1), 1, self.lcd.bar_chars)
    a2 = ui.widgets.AudioShow((10,1), 1, self.lcd.bar_chars)
    self.widgets += [a0,a1,a2]
    self.audio_list = [a0,a1,a2]
    self.audio_map = {}
    # player
    self.player = None
    self.player_show = ui.widgets.PlayerShow((15,1), self._index_mapper)
    self.widgets.append(self.player_show)

  def _setup_lcd(self):
    def_cfg = {
      'sim' : True,
      'font_path' : 'font'
    }
    lcd_cfg = self.cfg.get_section('ui_lcd', def_cfg)
    font_path = lcd_cfg['font_path']
    sim = lcd_cfg['sim']
    return  lcd.LCD16x2(font_path=font_path, sim=sim)

  def _p(self, *args, **kwargs):
    a = ["**UI**"] + list(args)
    print(*a,file=sys.stderr,**kwargs)

  def get_tick_interval(self):
    return 0.25

  def on_tick(self, ts, delta):
    """tick timer for ui. called every 0.25s"""
    if not self._handle_buttons():
      return False
    # tick update all widgets
    self._tick_widgets(ts, delta)
    # what to show in first line?
    if self.scroller.is_busy():
      # show scroller if its busy
      self.scroller.show(True)
      self.clock.show(False)
    else:
      # if nothing todo then show clock
      self.scroller.show(False)
      self.clock.show(True)
    # perform redraw
    self._redraw_widgets()

  def on_start(self, nick):
    self.nick = nick
    self.scroller.add_message(nick)

  def on_connect(self):
    self.scroller.add_message("Connected!")

  def on_disconnect(self):
    self.scroller.add_message("Disconnected:(")

  def on_peer_connect(self, peer):
    self.scroller.add_message("'%s' connected." % peer)

  def on_peer_disconnect(self, peer):
    self.scroller.add_message("'%s' disconnected." % peer)

  def _tick_widgets(self, ts, delta):
    for w in self.widgets:
      w.tick(ts, delta)

  def _clear_screen(self):
    self.lcd.clear()

  def _draw_func(self, pos, txt):
    self.lcd.text(pos[0], pos[1], txt)

  def _redraw_widgets(self, force=False):
    for w in self.widgets:
      w.redraw(self._draw_func)

  def _handle_buttons(self):
    b = self._read_buttons()
    if b is not None:
      self._p("buttons:", b)
      # quit bot?
      if 'q' in b:
        return False
    return True

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
    # find free slot
    for ai in self.audio_list:
      if ai.get_audio() is None:
        ai.set_audio(a)
        idx = ai.idx
        self.audio_map[a] = ai
        self.scroller.add_message("add %d:%s" % (idx, a.name))
        return
    # no slot free
    self.scroller.add_message("skip: " + a.name)

  def audio_del(self, a):
    self._p("audio_del", a)
    if a in self.audio_map:
      ai = self.audio_map[a]
      idx = ai.idx
      del self.audio_map[a]
      ai.set_audio(None)
      self.scroller.add_message("rem %d:%s" % (idx, a.name))
      return
    # no slot assigned
    self.scroller.add_message("lost: " + a.name)

  def audio_update(self, a, flags):
    self._p("audio_update", a)
    if a in self.audio_map:
      ai = self.audio_map[a]
      ai.update()

  # player calls

  def _index_mapper(self, ai):
    """map an audio info to a list index"""
    for a in self.audio_list:
      if a.get_audio() == ai:
        return str(a.idx)
    return None

  def _is_my_player(self, name):
    """check if given player is my associated player"""
    return name == self.nick

  def player_add(self, p):
    self._p("player_add", p)
    if self._is_my_player(p.name):
      self.player = p
      self.player_show.set_player(p)

  def player_del(self, p):
    self._p("player_del", p)
    if p == self.player:
      self.player = None
      self.player_show.set_player(None)

  def player_update(self, p, flags):
    self._p("player_update", p, flags)
    if p == self.player:
      self.player_show.update()
