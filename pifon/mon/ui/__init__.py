import lcd
from ctl import UICtl

def _check_cfg(cfg_dict, valid):
  res = {}
  if cfg_dict is None:
    return res
  for v in cfg_dict:
    if v in valid:
      try:
        res[v] = valid[v](cfg_dict[v])
      except ValueError:
        pass
    else:
      raise ValueError("invalid option key: "+v)
  return res

def create_lcd_ui(**kw_args):
  valid = {
    'font_path' : str,
    'sim' : bool
  }
  cfg = _check_cfg(cfg_dict, valid)
  return lcd.UI(**cfg)

def create_ui(name, **kw_args):
  if name == 'lcd':
    return lcd.UI(**kw_args)
  else:
    return None

# ----- Test -----
if __name__ == '__main__':
  ui = create_ui('lcd', font_path='font', sim=True)
  while True:
    but = ui.read_buttons()
    if but is not None:
      if "q" in but:
        break
      print(but)
