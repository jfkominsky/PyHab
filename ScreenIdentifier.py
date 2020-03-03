from psychopy import visual, event, core, gui, monitors, tools, sound,__version__
from psychopy.app import coder
import wx, random, csv, shutil, os, sys, threading, itertools
from math import *
from copy import deepcopy
import pyglet

"""
A simple tool for identifying which screen has which screen index
"""

defDisp = pyglet.window.get_platform().get_default_display()
allScrs = defDisp.get_screens()

screenList = list(range(0, len(allScrs)))
winList = []

for i in range(0, len(screenList)):
    tmpWin = visual.Window(size=(400,300), pos=(0,0),units='norm',screen=screenList[i])
    tmpTxt = visual.TextStim(tmpWin, text=str(screenList[i]), pos=(0,0))
    tmpTxt.draw()
    tmpWin.flip()
    winList.append(tmpWin)

event.waitKeys()
for j in range(0, len(winList)):
    winList[j].close()