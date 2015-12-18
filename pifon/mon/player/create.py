import dummy
import mpd
import mpv

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

def create_mpd_player(cfg_dict):
  valid = {
    'mpc' : str,
    'host' : str
  }
  cfg = _check_cfg(cfg_dict, valid)
  return mpd.PlayerMPD(**cfg)

def create_mpv_player(cfg_dict):
  valid = {
    'mpv' : str
  }
  cfg = _check_cfg(cfg_dict, valid)
  return mpv.PlayerMPV(**cfg)

def create_player(name='dummy', **cfg_dict):
  if name == 'dummy':
    p = dummy.PlayerDummy()
  elif name == 'mpd':
    p = create_mpd_player(cfg_dict)
  elif name == 'mpv':
    p = create_mpv_player(cfg_dict)
  else:
    return None
  _setup_chimes(p, cfg_dict)
  return p

def _setup_chimes(player, cfg_dict):
  # setup chimes
  chime_start = None
  chime_stop = None
  if 'chime_start' in cfg_dict:
    chime_start = cfg_dict['chime_start']
  if 'chime_stop' in cfg_dict:
    chime_stop = cfg_dict['chime_stop']
  player.set_chimes(chime_start, chime_stop)

# ----- Test -----
if __name__ == '__main__':
  p = create_player('dummy')
  p._play_chime('../sounds/prompt.wav')
  p = create_player('mpd', host='pimon')
  p._play_chime('../sounds/prompt.wav')
  p = create_player('mpv')
  p._play_chime('../sounds/prompt.wav')
