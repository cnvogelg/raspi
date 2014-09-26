class Colors:
  BUTTON_FG_COLOR = 0
  BUTTON_BG_COLOR = 1
  BUTTON_BD_COLOR = 2
  BUTTON_FG_ACTIVE_COLOR = 3
  BUTTON_BG_ACTIVE_COLOR = 4
  BUTTON_BD_ACTIVE_COLOR = 5

  LABEL_FG_COLOR = 10
  LABEL_BG_COLOR = 11

  def __init__(self):
    self.color_map = {
      self.BUTTON_FG_COLOR : (0x16, 0x7F, 0xFC),
      self.BUTTON_BG_COLOR : (0xf8, 0xf8, 0xf8),
      self.BUTTON_BD_COLOR : (0xd8, 0xd8, 0xd8),
      self.BUTTON_FG_ACTIVE_COLOR: (0x50, 0x90, 0xff),
      self.BUTTON_BG_ACTIVE_COLOR: (0xff, 0xff, 0xff),
      self.BUTTON_BD_ACTIVE_COLOR: (0xdf, 0xdf, 0xdf),

      self.LABEL_FG_COLOR : (0, 0, 0),
      self.LABEL_BG_COLOR : (0xf8, 0xf8, 0xf8)
    }

  def get_color(self, i):
    return self.color_map[i]
