from __future__ import print_function

class Slots:
  """manage a set of objects in a limited slot array"""
  def __init__(self, num):
    self.slots = [None] * num
    self.slot_map = {}
    self.used = 0
    self.num = num

  def __str__(self):
    return "[%d/%d,%s,%s]" % (self.used, self.num, repr(self.slots), repr(self.slot_map))

  def add(self, obj):
    """add new object and return slot index or None if slot array is full"""
    if self.used < self.num:
      # find free slot
      pos = 0
      for i in self.slots:
        if i is None:
          break
        pos += 1
      self.used += 1
      self.slot_map[obj] = pos
      self.slots[pos] = obj
      return pos
    else:
      # has no free slot
      self.slot_map[obj] = None
      return None

  def remove(self, obj):
    """remove object from slot array. return slot pos if any"""
    if obj in self.slot_map:
      pos = self.slot_map[obj]
      del self.slot_map[obj]
      if pos is not None:
        self.slots[pos] = None
        self.used -= 1
      return pos
    else:
      return None

  def get_unassigned_obj(self):
    """return an object that is currently not assigned"""
    for k in self.slot_map:
      pos = self.slot_map[k]
      if pos is None:
        return k
    return None

  def get_num_used(self):
    """return the number of slots"""
    return self.used

  def get_last_used_slot(self):
    """return number of last used slot or -1 if no slot is set"""
    if self.used == 0:
      return -1
    for a in reversed(xrange(self.num)):
      if self.slots[a] is not None:
        return a
    return -1

  def get_slot(self, pos):
    """return a slot object"""
    return self.slots[pos]

  def get_slot_array(self):
    """return a copy of the slot array"""
    return self.slots[:]

  def remap_slots(self):
    """remap slots and remove holes if any. return True if remap was done"""
    # nothing to remap
    if self.used == self.num:
      return False
    todo = 0
    result = {}
    while todo < self.used:
      # need to fill an entry?
      if self.slots[todo] is None:
        # search backwards
        for a in reversed(xrange(self.num)):
          a_obj = self.slots[a]
          if a_obj is not None:
            self.slots[todo] = a_obj
            self.slot_map[a_obj] = todo
            self.slots[a] = None
            # store mapping of object in result
            result[a_obj] = (a, todo)
            break
      todo += 1
    if len(result) == 0:
      return None
    else:
      return result

# ----- Test -----
if __name__ == '__main__':
  s = Slots(3)
  print(s, s.get_last_used_slot())
  s.add("a")
  print(s, s.get_last_used_slot())
  s.add("b")
  print(s)
  s.add("c")
  print(s)
  s.add("d")
  print(s)
  s.remove("b")
  print(s)
  obj = s.get_unassigned_obj()
  s.add(obj)
  print(s)
  s.remove("d")
  print(s)
  res = s.remap_slots()
  print(res)
  print(s)
