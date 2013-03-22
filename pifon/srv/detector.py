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
    "active",
    "sustain",
    "respite"
  )
  
  def __init__(self, event_handler, opts):
    self.event_handler = event_handler
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
    
  def get_rms(self, data):
    """get root mean square of all samples"""
    n = int(len(data) / 2)
    o = 0
    sums = 0
    for i in range(n):
      v = data[o] + data[o+1] * 256
      if v > 32767:
        v = 65536 - v
      f = v / 32767.0
      sums += f * f
      o += 2
    rms = math.sqrt(sums / n)
    return rms

  def handle_buffer(self, data):
    """check incoming audio buffer and derive loudness state
       pass the state changes to the passed event handler
       the event_handler is called with .begin(), .end(), .update()
    """
    t = time.time()
    
    # determine current RMS value of audio buffer
    level = int(self.get_rms(data) * 100)
    
    # options
    update = self.opts['update'] * 100 # in ms

    # determine max current RMS level
    if level > self.cur_level:
      self.cur_level = level
    if level > self.max_level:
      self.max_level = level
      
    # process levels?
    delta = (t - self.last_update_time) * 1000
    if delta >= update:
      self.process_levels(t, self.max_level, self.cur_level)
      self.last_update_time = t
      # reset current level for next block
      self.cur_level = 0
      
  def process_levels(self, t, max_level, cur_level):
    # trace flag
    trace = self.opts['trace']

    # show level?
    show_level = trace or self.state != self.STATE_IDLE    
    if show_level:
      self.event_handler.level(max_level, cur_level)
    
    # update state with current peak
    self.state_update(t, cur_level)
  
  def state_update(self, t, peak):
    """determine new state of detector"""

    # get parameters
    level = self.opts['level']
    
    old_state = self.state
    
    # ----- IDLE -----
    if self.state == self.STATE_IDLE:
      # start attack?
      if peak >= level:
        self.attack_begin_time = t
        self.state = self.STATE_ATTACK
        # reset max level
        self.max_level = 0
    
    # ----- ATTACK -----
    elif self.state == self.STATE_ATTACK:
      # long enough?
      if peak >= level:
        attack = self.opts['attack'] * 1000 # in ms
        delta = (t - self.attack_begin_time) * 1000
        if delta >= attack:
          self.state = self.STATE_ACTIVE
      else:
        # fall back to idle
        self.state = self.STATE_IDLE
    
    # ----- ACTIVE -----
    elif self.state == self.STATE_ACTIVE:
      # sustain
      if peak < level:
        self.sustain_begin_time = t
        self.state = self.STATE_SUSTAIN
    
    # ----- SUSTAIN -----
    elif self.state == self.STATE_SUSTAIN:
      # long enough?
      if peak < level:
        sustain = self.opts['sustain'] * 1000 # in ms
        delta = (t - self.sustain_begin_time) * 1000
        if delta >= sustain:
          self.state = self.STATE_RESPITE
          self.respite_begin_time = t
      else:
        # fall back to active
        self.state = self.STATE_ACTIVE
    
    # ----- RESPITE -----
    elif self.state == self.STATE_RESPITE:
      # long enough?
      respite = self.opts['respite'] * 1000 # in ms
      delta = (t - self.respite_begin_time) * 1000
      if delta >= respite:
        # return to idle
        self.state = self.STATE_IDLE
    
    # post a state update?
    if old_state != self.state:
      self.event_handler.state(self.state_names[self.state])
