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

    def abortTrial(self, onArray, offArray, trial, ttype, onArrayL, onArrayR, stimName = '', habTrialNo = 0):
        """
        Aborts a trial in progress, saves any data recorded thus far to the bad-data structures

        :param onArray: Gaze-on Center events
        :type onArray: list of dicts {trial, trialType, startTime, endTime, duration}
        :param offArray: Gaze-off events
        :type offArray: list of dicts {trial, trialType, startTime, endTime, duration}
        :param trial: Trial number
        :type trial: int
        :param ttype: Trial type
        :type ttype: string
        :param onArrayL: Gaze-on Left events
        :type onArrayL: list of dicts {trial, trialType, startTime, endTime, duration}
        :param onArrayR: Gaze-on Right events
        :type onArrayR: list of dicts {trial, trialType, startTime, endTime, duration}
        :param stimName: If presenting stimuli, name of the stim file
        :type stimName: string
        :return:
        :rtype:
        """
        sumOn = 0
        sumOff = 0
        sumOnL = 0
        sumOnR = 0
        if habTrialNo <= 0:
            habTrialNo = ''
        for i in range(0, len(onArray)):
            sumOn = sumOn + onArray[i]['duration']
        for j in range(0, len(offArray)):
            sumOff = sumOff + offArray[j]['duration']
        for k in range(0, len(onArrayL)):
            sumOnL = sumOnL + onArrayL[k]['duration']
        for m in range(0, len(onArrayR)):
            sumOnR = sumOnR + onArrayR[m]['duration']

        # needs to be .extend or you get weird array-within-array-within-array issues that become problematic later
        self.verbBadList['verboseOn'].extend(onArray)
        self.verbBadList['verboseOnL'].extend(onArrayL)
        self.verbBadList['verboseOnR'].extend(onArrayR)
        self.verbBadList['verboseOff'].extend(offArray)
        tempData = {'sNum': self.sNum, 'sID': self.sID, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex, 'cond': self.cond,
                    'condLabel': self.condLabel,
                    'trial': trial, 'GNG': 0, 'trialType': ttype, 'stimName': stimName, 'habCrit': self.habCrit, 'habTrialNo': habTrialNo,
                    'sumOnC': sumOn, 'numOnC': len(onArray),
                    'sumOnL': sumOnL, 'numOnL': len(onArrayL),
                    'sumOnR': sumOnR, 'numOnR': len(onArrayR), 'sumOff': sumOff, 'numOff': len(offArray)}
        self.badTrials.append(tempData)

    def dataRec(self, onArray, offArray, trial, type, onArrayL, onArrayR, stimName = '', habTrialNo = 0):
        """
        Records the data for a trial that ended normally.

        :param onArray: Gaze-on Left events
        :type onArray: list of dicts {trial, trialType, startTime, endTime, duration}
        :param offArray: Gaze-off events
        :type offArray: list of dicts {trial, trialType, startTime, endTime, duration}
        :param trial: Trial number
        :type trial: int
        :param ttype: Trial type
        :type ttype: string
        :param onArrayL: Gaze-on Right events
        :type onArrayL: list of dicts {trial, trialType, startTime, endTime, duration}
        :param onArrayR: Gaze-on Right events
        :type onArrayR: list of dicts {trial, trialType, startTime, endTime, duration}
        :param stimName: If presenting stimuli, name of the stim file
        :type stimName: string
        :return:
        :rtype:
        """
        sumOn = 0
        sumOff = 0
        sumOnL = 0
        sumOnR = 0
        if habTrialNo <= 0:
            habTrialNo = ''
        #loop through each array adding up gaze duration (on and off).
        for i in range(0,len(onArray)):
            sumOn = sumOn + onArray[i]['duration']
        for j in range(0,len(offArray)):
            sumOff = sumOff + offArray[j]['duration']
        for k in range(0,len(onArrayL)):
            sumOnL = sumOnL + onArrayL[k]['duration']
        for m in range(0, len(onArrayR)):
            sumOnR = sumOnR + onArrayR[m]['duration']
        #add to verbose master gaze array
        self.verbDatList['verboseOn'].extend(onArray)
        self.verbDatList['verboseOff'].extend(offArray)
        self.verbDatList['verboseOn2'].extend(onArray2)
        tempData={'sNum':self.sNum, 'sID': self.sID, 'months':self.ageMo, 'days':self.ageDay, 'sex':self.sex, 'cond':self.cond,'condLabel':self.condLabel,
                                'trial':trial, 'GNG':1, 'trialType':type, 'stimName':stimName, 'habCrit':self.habCrit, 'habTrialNo': habTrialNo,
                                'sumOnL':sumOn, 'numOnL':len(onArray),
                                'sumOnL':sumOnL,'numOnL':len(onArrayL),
                                'sumOnR':sumOnR,'numOnR':len(onArrayR),'sumOff':sumOff, 'numOff':len(offArray)}
        self.dataMatrix.append(tempData)

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

    def setupWindow(self):
        """
        An HPP-specific version of the function that sets up the windows and loads everything. With four windows to set
        up it's a real doozy, and has the added problem of needing to assign things properly to each window for stim
        presentation.


        :return:
        :rtype:
        """
        if self.stimPres:
            # Stimulus presentation window
            self.win = visual.Window((self.screenWidth['C'], self.screenHeight['C']), fullscr=False, screen=self.screenIndex['C'], allowGUI=False,
                                     units='pix', color=self.screenColor['C'])
            self.winL = visual.Window((self.screenWidth['L'], self.screenHeight['L']), fullscr=False, screen=self.screenIndex['L'], allowGUI=False,
                                     units='pix', color=self.screenColor['L'])
            self.winR = visual.Window((self.screenWidth['R'], self.screenHeight['R']), fullscr=False, screen=self.screenIndex['R'], allowGUI=False,
                                     units='pix', color=self.screenColor['R'])
            self.dummyThing = visual.Circle(self.win, size=1, color=self.win.color)  # This is for fixing a display glitch in PsychoPy3 involving multiple windows of different sizes.
        # Coder window
        self.win2 = visual.Window((400, 400), fullscr=False, screen=self.expScreenIndex, allowGUI=True, units='pix', waitBlanking=False,
                                  rgb=[-1, -1, -1])
        if self.stimPres:
            tempText = visual.TextStim(self.win2, text="Loading Stimuli", pos=[0, 0], color='white', bold=True, height=40)
            tempText.draw()
            self.win2.flip()
            # Step 1: Load and present "startImage"
            if self.startImage is not '':  #TODO: For now start/end is restricted to center screen.
                self.dummyThing.draw()
                tempStim = self.stimList[self.startImage]
                tempStimObj = visual.ImageStim(self.win, tempStim['stimLoc'], size=[self.movieWidth['C'], self.movieHeight['C']])
                tempStimObj.draw()
                self.win.flip() # This should now be on the screen until the first attngetter
            self.stimDict = {x: [] for x in self.stimNames.keys()}  # This holds all the loaded movies.
            self.counters = {x: 0 for x in self.stimNames.keys()}  # list of counters, one per index of the dict, so it knows which movie to play
            tempCtr = {x: 0 for x in self.stimNames.keys()}
            for i in self.actualTrialOrder:
                # Adjust for hab sub-trials. Looks for a very specific set of traits, which could occur, but...shouldn't.
                if '.' in i:
                    tempI = i
                    while '.' in tempI:
                        tempI = tempI[tempI.index('.')+1:]
                    i = tempI
                x = tempCtr[i]  # Changed so hab trials get the same treatment as everything else.
                # TODO The counter system will need to treat each pair in a multi-presentation trial as one item.
                # TODO: This will require making an HPP-specific DoExperiment. Ultimately we're going to have to redo most of PyHabClass for HPP unless we find a way to factorize it more.
                # TODO: REdosetup also doesn't carry over, nor jump and insert. Nothing that references stimNames will be able to stay the same.
                if i in self.multiStim:
                    # We need to count two to three movies for every instance of the counter.
                    lenC = len(self.stimNames[i]['C'])
                    lenL = len(self.stimNames[i]['L'])
                    lenR = len(self.stimNames[i]['R'])

                else:
                    # TODO: For non multi-stim trials, we have effectively no way of controlling order reasonably. We need a separate data structure just for order of movies in HPP...hell.
                    if x < len(self.stimNames[i]):
                        # TODO: x is an iterator for an instance of a trial. The stimNames length condition no longer works exactly...
                        tempStim = self.stimList[self.stimNames[i][x]]
                        #TODO: Here's where we have to start getting real clever about it. StimNames is going to be more complex.
                        if tempStim['stimType'] == 'Movie':
                            tempStimObj = visual.MovieStim3(self.win, tempStim['stimLoc'],
                                                          size=[self.movieWidth['C'], self.movieHeight['C']], flipHoriz=False,
                                                          flipVert=False, loop=False)
                        elif tempStim['stimType'] == 'Image':
                            tempStimObj = visual.ImageStim(self.win, tempStim['stimLoc'],
                                                           size=[self.movieWidth['C'], self.movieHeight['C']])
                        elif tempStim['stimType'] == 'Audio':
                            tempStimObj = sound.Sound(tempStim['stimLoc'])
                        else: # The eternal problem of audio/image pair. Just creates an object that's a dict of audio and image.
                            audioObj = sound.Sound(tempStim['audioLoc'])
                            imageObj = visual.ImageStim(self.win, tempStim['imageLoc'],
                                                           size=[self.movieWidth['C'], self.movieHeight['C']])
                            tempStimObj = {'Audio': audioObj, 'Image': imageObj}
                        tempAdd = {'stimType':tempStim['stimType'], 'stim':tempStimObj}
                        self.stimDict[i].append(tempAdd)
                    tempCtr[i] += 1

            if len(list(self.playAttnGetter.keys())) > 0:
                for i in list(self.attnGetterList.keys()):
                    if self.attnGetterList[i]['stimType'] == 'Audio':
                        self.attnGetterList[i]['file'] = sound.Sound(self.attnGetterList[i]['stimLoc'])
                    else:
                        self.attnGetterList[i]['file'] = visual.MovieStim3(self.win, self.attnGetterList[i]['stimLoc'],
                                                                           size=[self.movieWidth['C'], self.movieHeight['C']],
                                                                           flipHoriz=False, flipVert=False, loop=False)
                        if self.attnGetterList[i]['stimType'] == 'Movie + Audio':
                            self.attnGetterList[i]['audioFile'] = sound.Sound(self.attnGetterList[i]['audioLoc'])
            if self.endImage is not '': # Load image for end of experiment, if needed.
                tempStim = self.stimList[self.endImage]
                self.endImageObject = visual.ImageStim(self.win, tempStim['stimLoc'], size=[self.movieWidth['C'], self.movieHeight['C']])
            else:
                self.endImageObject = None
        self.keyboard = self.key.KeyStateHandler()
        self.win2.winHandle.push_handlers(self.keyboard)
        if self.stimPres:
            self.win.winHandle.push_handlers(self.keyboard)
            self.baseSize = 40 # Base size of all attention-getters, in pixels
            self.attnGetterSquare = visual.Rect(self.win, height=self.baseSize, width=self.baseSize, pos=[self.testOffset + 0, 0], fillColor='black')
            self.attnGetterCross = visual.ShapeStim(self.win, vertices='cross', size=self.baseSize, pos=[self.testOffset + 0, 0], fillColor='black')

            numVertices = 10
            starRad = self.baseSize #This creates a large but static rotating star. It does not loom.
            starVerts = []
            for x in range(0,numVertices):
                if x % 2 == 1:
                    tempRad = starRad*.55  # How much to draw in between the "points"
                else:
                    tempRad = starRad
                tempVert = [tempRad*sin((2*pi)/numVertices * x), tempRad*cos((2*pi)/numVertices * x)]
                starVerts.append(tempVert)

            self.attnGetterStar = visual.ShapeStim(self.win, vertices=starVerts, pos=[self.testOffset + 0, 0], fillColor='black')

        self.statusSquareA = visual.Rect(self.win2, height=80, width=80,
                                         pos=[self.statusOffset - 60, self.statusOffsetY + 0],
                                         fillColor='black')  # These two appear on the status screen window.
        self.statusSquareB = visual.Rect(self.win2, height=80, width=80,
                                         pos=[self.statusOffset + 60, self.statusOffsetY + 0], fillColor='black')
        self.statusTextA = visual.TextStim(self.win2, text="", pos=[self.statusOffset - 60, self.statusOffsetY + 0],
                                           color='white', bold=True, height=30)
        self.statusTextB = visual.TextStim(self.win2, text="", pos=[self.statusOffset + 60, self.statusOffsetY + 0],
                                           color='white', bold=True, height=30)
        self.trialText = visual.TextStim(self.win2, text="Trial no: ", pos=[-100, 150], color='white')
        self.readyText = visual.TextStim(self.win2, text="Trial not active", pos=[-25, 100], color='white')
        self.doExperiment()  # Get this show on the road!