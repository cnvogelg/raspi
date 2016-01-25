from __future__ import print_function
import sys

import lcd
import ui.widgets



class UI:

  FLAG_CLEAR = 1
  FLAG_CLOCK = 2
  FLAG_SCROLLER = 4
  FLAG_AUDIO = 8
  FLAG_PLAYER = 16

  def __init__(self, cfg):
    self.cfg = cfg
    self.lcd = self._setup_lcd()
    self.clock = ui.widgets.Clock()
    # audio
    self.audio_map = {}
    self.audio_list = []
    self.audio_fill = " " * 16
    self.hb_chars = "?!" + self.lcd.heart_a_char + self.lcd.heart_b_char
    self.play_chars = self.lcd.play_char + self.lcd.bell_char + " "
    # player
    self.player_map = {}
    self.player_list = []
    self.player_fill = " " * 7
    self.player_chars = self.lcd.play_char + self.lcd.stop_char
    self.mode_chars = self.lcd.note_char + self.lcd.hourglass_char + \
      self.lcd.speaker_char + " "
    # welcome
    self.scroller = ui.widgets.Scroller(16)
    self.scroller.add_message("Welcome to pifon2!")
    # flag
    self.redraw_flag = 0
    self.show_scroller = False

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
      self.show_scroller = True
    else:
      # disable scroller and force redraw of clock and player
      if self.show_scroller:
        self.redraw_flag |= self.FLAG_CLOCK | self.FLAG_PLAYER
        self.show_scroller = False

  def _redraw(self):
    f = self.redraw_flag

    # clear lcd screen?
    if f & self.FLAG_CLEAR == self.FLAG_CLEAR:
      self.lcd.clear()

    # no scroller?
    if self.show_scroller:
      # update scroller?
      if f & self.FLAG_SCROLLER == self.FLAG_SCROLLER:
        txt = self.scroller.get_text()
        self.lcd.text(0,0,txt)
    else:
      # update clock?
      if f & self.FLAG_CLOCK == self.FLAG_CLOCK:
        txt = self.clock.get_text()
        self.lcd.text(0,0,txt)
      # update player
      if f & self.FLAG_PLAYER == self.FLAG_PLAYER:
        txt = " " + self._get_player_text()
        self.lcd.text(8,0,txt)

    # update audio
    if f & self.FLAG_AUDIO == self.FLAG_AUDIO:
      txt = self._get_audio_text()
      self.lcd.text(0,1,txt)

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
    aw = ui.widgets.AudioShow(a,
      hb_chars=self.hb_chars, play_chars=self.play_chars)
    self.audio_map[a] = aw
    self.audio_list.append(a)
    self.redraw_flag |= self.FLAG_AUDIO

  def audio_del(self, a):
    self._p("audio_del", a)
    if a in self.audio_map:
      del self.audio_map[a]
      self.audio_list.remove(a)
      self.redraw_flag |= self.FLAG_AUDIO

  def audio_update(self, a, flags):
    self._p("audio_update", a)
    if a in self.audio_map:
      aw = self.audio_map[a]
      aw.update()
      self.redraw_flag |= self.FLAG_AUDIO

  def _get_audio_text(self):
    res = []
    for a in self.audio_list:
      aw = self.audio_map[a]
      res.append(aw.get_text())
    txt = " ".join(res) + self.audio_fill
    txt = txt[0:len(self.audio_fill)]
    return txt

  # player calls

  def _index_mapper(self, a):
    n = len(self.audio_list)
    for i in range(n):
      if self.audio_list[i] == a:
        return str(i)
    return " "

  def player_add(self, p):
    self._p("player_add", p)
    pw = ui.widgets.PlayerShow(p, self._index_mapper,
      play_chars=self.player_chars, mode_chars=self.mode_chars)
    self.player_map[p] = pw
    self.player_list.append(p)
    self.redraw_flag |= self.FLAG_PLAYER

  def player_del(self, p):
    self._p("player_del", p)
    if p in self.player_map:
      del self.player_map[p]
      self.player_list.remove(p)
      self.redraw_flag |= self.FLAG_PLAYER

  def player_update(self, p, flags):
    self._p("player_update", p, flags)
    if p in self.player_map:
      pw = self.player_map[p]
      pw.update()
      self.redraw_flag |= self.FLAG_PLAYER

  def _get_player_text(self):
    res = []
    for p in self.player_list:
      pw = self.player_map[p]
      res.append(pw.get_text())
    txt = " ".join(res) + self.player_fill
    txt = txt[0:len(self.player_fill)]
    return txt
