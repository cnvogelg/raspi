import time
import math

class Detector:
  # states of detector
  STATE_IDLE = 0
  STATE_ATTACK = 1
  STATE_ACTIVE = 2
  STATE_SUSTAIN = 3
  STATE_RESPITE = 4

  state_names = (
    "idle",
    "attack",
    "busy",
    "sustain",
    "respite"
  )

  def __init__(self, opts):
    self.event_handler = None
    self.opts = opts
    # state
    self.last_update_time = 0
    self.respite_begin_time = 0
    self.attack_begin_time = None
    self.sustain_begin_time = 0
    self.in_respite = False
    self.cur_level = 0
    self.max_level = 0
    self.state = self.STATE_IDLE
    self.active = False

  def set_event_handler(self, ev):
    self.event_handler = ev

  def get_state_name(self):
    return self.state_names[self.state]

  def is_active(self):
    return self.active

  def handle_rms(self, level):
    """check incoming audio buffer and derive loudness state
       pass the state changes to the passed event handler
       the event_handler is called with .begin(), .end(), .update()
    """
    t = time.time()

    # options
    update = self.opts.get_value('update') * 100 # in ms

    # determine max current RMS level
    if level > self.cur_level:
      self.cur_level = level
    if level > self.max_level:
      self.max_level = level

    # process levels?
    delta = (t - self.last_update_time) * 1000
    if delta >= update:
      res = self.process_levels(t, self.max_level, self.cur_level)
      self.last_update_time = t
      # reset current level for next block
      self.cur_level = 0
      return res
    else:
      return (None, None)

  def process_levels(self, t, max_level, cur_level):
    # trace flag
    trace = self.opts.get_value('trace')

    # show level?
    show_level = trace or self.state != self.STATE_IDLE
    if show_level and self.event_handler is not None:
      if self.attack_begin_time is not None:
        duration = t - self.attack_begin_time
      else:
        duration = 0
      self.event_handler.level(max_level, cur_level, int(duration))

    # update state with current peak
    return self.state_update(t, cur_level)

  def state_update(self, t, peak):
    """determine new state of detector"""

    # get parameters
    alevel = self.opts.get_value('alevel')
    slevel = self.opts.get_value('slevel')

    old_state = self.state
    old_active = self.active

    # ----- IDLE -----
    if self.state == self.STATE_IDLE:
      # start attack?
      if peak >= alevel:
        self.attack_begin_time = t
        self.state = self.STATE_ATTACK

    # ----- ATTACK -----
    elif self.state == self.STATE_ATTACK:
      # long enough?
      if peak >= alevel:
        attack = self.opts.get_value('attack') * 1000 # in ms
        delta = (t - self.attack_begin_time) * 1000
        if delta >= attack:
          self.state = self.STATE_ACTIVE
          self.active = True
      else:
        # fall back to idle
        self.state = self.STATE_IDLE

    # ----- ACTIVE -----
    elif self.state == self.STATE_ACTIVE:
      # sustain
      if peak < slevel:
        self.sustain_begin_time = t
        self.state = self.STATE_SUSTAIN

    # ----- SUSTAIN -----
    elif self.state == self.STATE_SUSTAIN:
      # long enough?
      if peak < slevel:
        sustain = self.opts.get_value('sustain') * 1000 # in ms
        delta = (t - self.sustain_begin_time) * 1000
        if delta >= sustain:
          self.state = self.STATE_RESPITE
          self.active = False
          self.respite_begin_time = t
      else:
        # fall back to active
        self.state = self.STATE_ACTIVE

    # ----- RESPITE -----
    elif self.state == self.STATE_RESPITE:
      # long enough?
      respite = self.opts.get_value('respite') * 1000 # in ms
      delta = (t - self.respite_begin_time) * 1000
      if delta >= respite:
        # return to idle
        self.state = self.STATE_IDLE
        # reset max level
        self.max_level = 0

    # post a state update?
    up_state = None
    if old_state != self.state:
      self.post_state()
      up_state = self.state
    up_active = None
    if old_active != self.active:
      self.post_active()
      up_active = self.active
    return (up_state, up_active)

  def post_state(self):
    if self.event_handler is not None:
      self.event_handler.state(self.state_names[self.state])

  def post_active(self):
    if self.event_handler is not None:
      self.event_handler.active(self.active)
