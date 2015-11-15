from slots import Slots

class UICtl:
  def __init__(self, ui):
    self.ui = ui
    n = ui.get_max_audio_slots()
    self.audio_slots = Slots(n)
    self.num_audio_slot = 0

  def handle_events(self, ts):
    """handle UI events and state machine.
       return False to quit"""
    # check buttons
    but = self.ui.read_buttons()
    if but is not None:
      if 'q' in but:
        return False
    # handle ui tick
    self.ui.tick(ts)
    return True

  # ----- audio callbacks -----

  def _update_audio_slots(self):
    # report a new slot number to ui
    n = self.audio_slots.get_last_used_slot() + 1
    if n != self.num_audio_slot:
      self.num_audio_slot = n
      self.ui.set_num_audio_slots(n)

  def audio_add_instance(self, i):
    # try to allocate a new slot for the instance
    slot = self.audio_slots.add(i)
    if slot is not None:
      # report the instance to the ui
      self._update_audio_slots()
      self.ui.attach_audio_slot(slot, i)

  def audio_del_instance(self, i):
    slot = self.audio_slots.remove(i)
    if slot is not None:
      # a slot was assigned
      self.ui.detach_audio_slot(slot, i)
      # is an instance still wating for a slot?
      new_i = self.audio_slots.get_unassigned_obj()
      if new_i is not None:
        # assign old instance a slot
        self.audio_add_instance(new_i)
      else:
        # try to remap old slots to be more compact
        remap = self.audio_slots.remap_slots()
        if remap is not None:
          for inst in remap:
            old_pos, new_pos = remap[inst]
            self.ui.remap_audio_slot(old_pos, new_pos, inst)
        self._update_audio_slots()

  def audio_update_level(self, i):
    pass

  def audio_update_state(self, i):
    pass

  def audio_ping(self, i, valid):
    pass

  def audio_update_option(self, i, field):
    pass

  def audio_update_all_options(self, i, fields):
    pass
