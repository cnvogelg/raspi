#!/usr/bin/env python

import bot
import sys

# add arguments as paths
for arg in sys.argv[1:]:
  sys.path.append(arg)

# launch bot
b = bot.Bot(True)
b.run()
