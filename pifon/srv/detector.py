import time
import math

class Detector:
  def __init__(self, event_handler, opts):
    self.event_handler = event_handler
    self.opts = opts
    # state
    self.is_active = False
    self.sustain_begin_time = 0
    self.last_event_time = 0
    self.respite_begin_time = 0
    self.attack_begin_time = None
    self.in_respite = False
    self.max_peak = 0
    self.trace_min = 32768
    self.trace_max = 0
    self.trace_time = 0
    
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
    peak = int(self.get_rms(data) * 100)
    
    # options
    update = self.opts['update'] * 100 # in ms
    attack = self.opts['attack'] * 1000 # in ms
    sustain = self.opts['sustain'] * 1000 # in ms
    respite = self.opts['respite'] * 1000 # in ms
    level = self.opts['level']
    trace = self.opts['trace']
    
    # report a trace of the peak level if desired
    if peak < self.trace_min:
      self.trace_min = peak
    if peak > self.trace_max:
      self.trace_max = peak
    if trace:
      delta = (t - self.trace_time) * 1000
      if delta > update:
        self.event_handler.trace(self.trace_min, self.trace_max)
        self.trace_min = 32768
        self.trace_max = 0
        self.trace_time = t
    
    # ----- in active phase -----
    if self.is_active:
      do_update = True
      
      # check for quiet
      if peak < level:
        # first silence phase
        if self.sustain_begin_time == None:
          self.sustain_begin_time = t         
          self.event_handler.state('sustain_begin',peak)
        else:
          # still silent
          delta = (t - self.sustain_begin_time) * 1000
          if delta >= sustain:
            # silence was long enough -> leave loudness
            self.is_active = False
            self.attack_begin_time = None
            self.event_handler.state('end',peak)
            do_update = False
            if respite > 0:
              # begin respite phase
              self.respite_begin_time = t
              self.in_respite = True
              self.event_handler.state('respite_begin',peak)
      else:
        # still loud -> reset quiet interval
        if self.sustain_begin_time != None:
          self.sustain_begin_time = None
          self.event_handler.state('sustain_lost',peak)

      # update peak during active phase?
      if do_update:
        if peak > self.max_peak:
          self.max_peak = peak
        # long enough for update
        delta = (t - self.last_event_time) * 1000
        if delta >= update:
          self.event_handler.update(self.max_peak)
          self.last_event_time = t
          self.max_peak = 0

    # ----- in passive phase -----
    else:
      # in respite phase?
      if self.in_respite:
        delta = (t - self.respite_begin_time) * 1000
        if delta > respite:
          self.event_handler.state('respite_over',peak)
          self.in_respite = False
      else:
        # check four loud
        if peak > level:
          # begin of attack
          if self.attack_begin_time == None:
            self.attack_begin_time = t
            self.event_handler.state('attack_begin',peak)
          # check if attack period passed
          delta = (t - self.attack_begin_time)
          if delta >= attack:
            # begin active phase
            self.is_active = True
            self.sustain_begin_time = None
            self.last_event_time = t
            self.event_handler.state('begin',peak)
            self.max_peak = 0
        # not loud
        else:
          if self.attack_begin_time != None:
            self.attack_begin_time = None
            self.event_handler.state('attack_lost',peak)
