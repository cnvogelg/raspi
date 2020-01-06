# real LCD
try:
    from .lcd import LCD16x2 as LCD
except ImportError:
    # try LCDSim
    try:
        from .lcdsim import LCDSim as LCD
    except ImportError:
        raise RuntimeError("no suitable LCD impl found!")

from .base import *
