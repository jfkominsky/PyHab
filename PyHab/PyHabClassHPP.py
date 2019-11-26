import os, sys
from psychopy import visual, event, core, data, gui, monitors, tools, prefs, logging
from psychopy.constants import (STARTED, PLAYING)  # Added for new stimulus types
prefs.hardware['audioLib'] = ['sounddevice']
if os.name is 'posix':
    prefs.general['audioDevice'] = ['Built-in Output']
from psychopy import sound
import pyglet
from pyglet import input as pyglet_input
import wx, random, csv
from math import *
from datetime import *
from dateutil.relativedelta import *
from .PyHabClass import PyHab
from copy import deepcopy

class PyHabHPP(PyHab):
    """
    A head-turn preference procedure version of PyHab. Uses some of the same code, but drastically more complex, needing
    to juggle which screen things are presented on, simultaneous presentation on multiple screens, and more.
    """

    def __init__(self, settingsDict):
        PyHab.__init__(self, settingsDict)
        self.multiStim = eval(settingsDict['multiStim'])
        self.secondKey = self.key.M  # Variable that determines what the second key is. Overwrites what is set in the default init

        self.verbDatList = {'verboseOnC': [], 'verboseOnL': [], 'verboseOnR': [], 'verboseOff': []}  # a dict of the verbose data arrays
        self.verbBadList = {'verboseOnC': [], 'verboseOnL': [], 'verboseOnR': [], 'verboseOff': []}  # Corresponding for bad data

    def lookKeysPressed(self):
        """
        A simple boolean function to allow for more modularity with preferential looking
        Basically, allows you to set an arbitrary set of keys to start a trial once the attngetter has played.
        In this case, only B or M are sufficient.

        :return: True if the B, N, or M key is pressed, False otherwise.
        :rtype:
        """
        if self.keyboard[self.key.N] or self.keyboard[self.key.B] or self.keyboard[self.key.M]:
            return True
        else:
            return False
