#!/usr/bin/env python2.7

import os
import sys
import inspect

# add .. to module path
my_dir = os.path.split(inspect.getfile( inspect.currentframe() ))[0]
tools_dir = os.path.realpath(os.path.abspath(os.path.join(my_dir,"..")))
if tools_dir not in sys.path:
  sys.path.insert(0, tools_dir)

import shiny

# size of touch screen
screen_size = (1024, 600)
screen = shiny.Screen(screen_size)

def handler(button):
  print button

# setup jog pane
jog_pane = shiny.Pane("Jogger")
lx = shiny.Label(jog_pane, (2,0,4,1), "000.0000")
ly = shiny.Label(jog_pane, (2,1,4,1), "000.0000")
lz = shiny.Label(jog_pane, (2,2,4,1), "000.0000")
bxp = shiny.Button(jog_pane, (0,0,2,1), "X+", handler)
bxn = shiny.Button(jog_pane, (6,0,2,1), "X-", handler)
byp = shiny.Button(jog_pane, (0,1,2,1), "Y+", handler)
byn = shiny.Button(jog_pane, (6,1,2,1), "Y-", handler)
bzp = shiny.Button(jog_pane, (0,2,2,1), "Z+", handler)
bzn = shiny.Button(jog_pane, (6,2,2,1), "Z-", handler)

# status bar
statusbar = shiny.Statusbar("Jogger")
screen.set_statusbar(statusbar)

# icon bar
iconbar = shiny.Iconbar()
screen.set_iconbar(iconbar)

# set first pane
screen.set_pane(jog_pane)

main = shiny.Shiny(screen)
main.run()
