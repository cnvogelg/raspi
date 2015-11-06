import player_dummy
import player_mpd
import player_mpv

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
  return player_mpd.PlayerMPD(**cfg)

def create_mpv_player(cfg_dict):
  valid = {
    'mpv' : str
  }
  cfg = _check_cfg(cfg_dict, valid)
  return player_mpv.PlayerMPV(**cfg)

def create_player(name, **cfg_dict):
  if name == 'dummy':
    return player_dummy.PlayerDummy()
  elif name == 'mpd':
    return create_mpd_player(cfg_dict)
  elif name == 'mpv':
    return create_mpv_player(cfg_dict)

# ----- Test -----
if __name__ == '__main__':
  p = create_player('dummy')
  p.play_chime('../sounds/prompt.wav')
  p = create_player('mpd', host='pimon')
  p.play_chime('../sounds/prompt.wav')
  p = create_player('mpv')
  p.play_chime('../sounds/prompt.wav')
