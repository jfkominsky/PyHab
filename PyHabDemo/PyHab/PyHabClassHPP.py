import os, sys
from psychopy import visual, event, core, data, gui, monitors, tools, prefs, logging, __version__
from psychopy.constants import (STARTED, PLAYING)  # Added for new stimulus types
if eval(__version__[0:4]) < 2023: # PTB has proven itself unreliable on too many systems, but sounddevice isn't included in 2023.
    prefs.hardware['audioLib'] = ['sounddevice'] # change to 'PTB' if you get audio errors
else:
    prefs.hardware['audioLib'] = ['PTB']
if os.name == 'posix':
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

    def __init__(self, settingsDict, testMode=False):
        PyHab.__init__(self, settingsDict, testMode)
        self.centerKey = self.key.B
        self.secondKey = self.key.V  # Variable that determines what the second key is. Overwrites what is set in the default init
        self.rightKey = self.key.N
        self.leftKey = self.secondKey  # This is a sort of belts-and-suspenders solution in case there are stray secondKey references.


        self.verbDatList = {'verboseOnC': [], 'verboseOnL': [], 'verboseOnR': [], 'verboseOff': []}  # a dict of the verbose data arrays
        self.verbBadList = {'verboseOnC': [], 'verboseOnL': [], 'verboseOnR': [], 'verboseOff': []}  # Corresponding for bad data

    def abortTrial(self, onArray, offArray, trial, ttype, onArrayL, onArrayR, stimName = '', habTrialNo = 0, habCrit = 0.0):
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
        :param habTrialNo: Tracking if this is a habituation trial and if so what number
        :type habTrialNo: int
        :param habCrit: Habituation criterion, if it's been set
        :type habCrit: float
        :return:
        :rtype:
        """
        sumOn = 0
        sumOff = 0
        sumOnL = 0
        sumOnR = 0
        firstLookC = 0
        firstLookL = 0
        firstLookR = 0
        if habTrialNo <= 0:
            habTrialNo = ''
        if len(onArray) > 0:
            firstLookC = onArray[0]['duration']
        if len(onArrayL) > 0:
            firstLookL = onArrayL[0]['duration']
        if len(onArrayR) > 0:
            firstLookR = onArrayR[0]['duration']
        for i in range(0, len(onArray)):
            sumOn = sumOn + onArray[i]['duration']
        for j in range(0, len(offArray)):
            sumOff = sumOff + offArray[j]['duration']
        for k in range(0, len(onArrayL)):
            sumOnL = sumOnL + onArrayL[k]['duration']
        for m in range(0, len(onArrayR)):
            sumOnR = sumOnR + onArrayR[m]['duration']

        # needs to be .extend or you get weird array-within-array-within-array issues that become problematic later
        self.verbBadList['verboseOnC'].extend(onArray)
        self.verbBadList['verboseOnL'].extend(onArrayL)
        self.verbBadList['verboseOnR'].extend(onArrayR)
        self.verbBadList['verboseOff'].extend(offArray)
        totalduration = sumOn + sumOnL + sumOnR + sumOff
        lastOn = 0
        for i in [onArray, onArrayL, onArrayR]:
            if len(i) > 0:
                if i[-1]['endTime'] > lastOn:
                    lastOn = i[-1]['endTime']
        if len(offArray) > 0:
            if offArray[-1]['endTime'] > lastOn:
                totalduration = totalduration - offArray[-1]['duration']
        tempData = {'sNum': self.sNum, 'sID': self.sID, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex, 'cond': self.cond,
                    'condLabel': self.condLabel,
                    'trial': trial, 'GNG': 0, 'trialType': ttype, 'stimName': stimName, 'habCrit': habCrit, 'habTrialNo': habTrialNo,
                    'sumOnC': sumOn, 'numOnC': len(onArray),
                    'sumOnL': sumOnL, 'numOnL': len(onArrayL),
                    'sumOnR': sumOnR, 'numOnR': len(onArrayR), 'sumOff': sumOff, 'numOff': len(offArray),
                    'trialDuration': totalduration, 'firstLookC':firstLookC, 'firstLookL':firstLookL, 'firstLookR':firstLookR}
        self.badTrials.append(tempData)

    def dataRec(self, onArray, offArray, trial, type, onArrayL, onArrayR, stimName = '', habTrialNo = 0, habCrit = 0.0):
        """
        Records the data for a trial that ended normally.

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
        :param habTrialNo: Tracking if this is a habituation trial and if so what number
        :type habTrialNo: int
        :param habCrit: Habituation criterion, if it's been set
        :type habCrit: float
        :return:
        :rtype:
        """
        sumOn = 0
        sumOff = 0
        sumOnL = 0
        sumOnR = 0
        firstLookC = 0
        firstLookL = 0
        firstLookR = 0
        if habTrialNo <= 0:
            habTrialNo = ''
        if len(onArray) > 0:
            firstLookC = onArray[0]['duration']
        if len(onArrayL) > 0:
            firstLookL = onArrayL[0]['duration']
        if len(onArrayR) > 0:
            firstLookR = onArrayR[0]['duration']
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
        self.verbDatList['verboseOnC'].extend(onArray)
        self.verbDatList['verboseOnL'].extend(onArrayL)
        self.verbDatList['verboseOnR'].extend(onArrayR)
        self.verbDatList['verboseOff'].extend(offArray)
        totalduration = sumOn + sumOnL + sumOnR + sumOff
        lastOn = 0
        for i in [onArray, onArrayL, onArrayR]:
            if len(i) > 0:
                if i[-1]['endTime'] > lastOn:
                    lastOn = i[-1]['endTime']
        if len(offArray) > 0:
            if offArray[-1]['endTime'] > lastOn:
                totalduration = totalduration - offArray[-1]['duration']

        tempData={'sNum':self.sNum, 'sID': self.sID, 'months':self.ageMo, 'days':self.ageDay, 'sex':self.sex, 'cond':self.cond,'condLabel':self.condLabel,
                                'trial':trial, 'GNG':1, 'trialType':type, 'stimName':stimName, 'habCrit':habCrit, 'habTrialNo': habTrialNo,
                                'sumOnC':sumOn, 'numOnC':len(onArray),
                                'sumOnL':sumOnL,'numOnL':len(onArrayL),
                                'sumOnR':sumOnR,'numOnR':len(onArrayR),'sumOff':sumOff, 'numOff':len(offArray),
                                'trialDuration': totalduration, 'firstLookC':firstLookC, 'firstLookL':firstLookL, 'firstLookR':firstLookR}
        self.dataMatrix.append(tempData)

    def lookKeysPressed(self):
        """
        A simple boolean function to allow for more modularity with preferential looking
        Basically, allows you to set an arbitrary set of keys to start a trial once the attngetter has played.
        In this case, any of V, B, or N are sufficient.

        :return: True if the V, B, or N key is pressed, False otherwise.
        :rtype:
        """
        if self.keyboard[self.key.V] or self.keyboard[self.key.B] or self.keyboard[self.key.N]:
            return True
        else:
            return False

    def lookScreenKeyPressed(self, screen=['C']):
        """
        A function that primarily exists for HPP, because of the need to distinguish between any key
        being pressed and the key corresponding to the HPP screen in question being pressed

        :param screen: List of screens for next stim.
        :type screen: list of strings
        :return: for non-HPP versions, the value of lookKeysPressed.
        :rtype: bool
        """

        if 'C' in screen and self.keyboard[self.key.B]:
            return True
        elif 'L' in screen and self.keyboard[self.key.V]:
            return True
        elif 'R' in screen and self.keyboard[self.key.N]:
            return True
        else:
            return False

    def dispCoderWindow(self, trialType = -1):
        """
        Because there are three looking keys, the experimenter window has three boxes. Also things work differently with
        there being no 'secondkey' really.
        :param trialType:
        :type trialType:
        :return:
        :rtype:
        """
        if trialType == -1:
            self.statusSquareA.fillColor = 'black'
            self.statusTextA.text = ''
        elif self.blindPres < 2:
            if trialType == 0:
                self.statusSquareA.fillColor = 'blue'
                self.statusTextA.text = "RDY"
            elif self.keyboard[self.centerKey]:
                self.statusSquareA.fillColor = 'green'
                self.statusTextA.text = "ON"
            else:
                self.statusSquareA.fillColor = 'red'
                self.statusTextA.text = "OFF"
        else:
            self.statusSquareA.fillColor = 'blue'
            self.statusTextA.text = ""

        self.statusSquareA.draw()
        self.statusTextA.draw()
        #Again for second coder box.
        if trialType == -1:
            self.statusSquareB.fillColor = 'black'
            self.statusTextB.text = ''
        elif self.blindPres < 2:
            if trialType == 0:
                self.statusSquareB.fillColor = 'blue'
                self.statusTextB.text = "RDY"
            elif self.keyboard[self.rightKey]:
                self.statusSquareB.fillColor = 'green'
                self.statusTextB.text = "ON"
            else:
                self.statusSquareB.fillColor = 'red'
                self.statusTextB.text = "OFF"
        else:
            self.statusSquareB.fillColor = 'blue'
            self.statusTextB.text = ""
        self.statusSquareB.draw()
        self.statusTextB.draw()
        # and the third!
        if trialType == -1:
            self.statusSquareL.fillColor = 'black'
            self.statusTextL.text = ''
        elif self.blindPres < 2:
            if trialType == 0:
                self.statusSquareL.fillColor = 'blue'
                self.statusTextL.text = "RDY"
            elif self.keyboard[self.leftKey]:
                self.statusSquareL.fillColor = 'green'
                self.statusTextL.text = "ON"
            else:
                self.statusSquareL.fillColor = 'red'
                self.statusTextL.text = "OFF"
        else:
            self.statusSquareL.fillColor = 'blue'
            self.statusTextL.text = ""
        self.statusSquareL.draw()
        self.statusTextL.draw()
        if self.blindPres < 2:
            self.trialText.draw()
            if self.blindPres < 1:
                self.readyText.draw()
        self.win2.flip()  # flips the status screen without delaying the stimulus onset.

    def dispTrial(self, trialType, dispMovie = False, trialNum=-1):
        """
        An HPP-specific version of dispTrial that can display on multiple things, read the new stimDict, etc.

        :param trialType: The trial type of the current trial being displayed
        :type trialType: str
        :param dispMovie: Now a dictionary C/L/R each index of which contains what this function expects in the base class
        :type dispMovie: bool or dict
        :param trialNum: Trial number for movie playback timing. -1 for attention-getter and other cases where it is irrelevant
        :type trialNum: int
        :return: 1 or 0. 1 = end of movie for trials that end on that. TODO: for HPP currently returns 1 if EVERYTHING IN IT is done.
        :rtype: int
        """
        self.dispCoderWindow(trialType)
        
        # That's the easy part. Now for the fun bit.
        if self.stimPres:
            screens = []
            for i,j in dispMovie.items():
                if j != 0:
                    screens.append(i)
            t = []
            for k in screens:
                if dispMovie[k]['stimType'] == 'Movie':
                    t.append(self.dispMovieStim(trialType, dispMovie[k]['stim'], dispMovie[k]['firstFrame'], trialNum=trialNum, screen=k))
                elif dispMovie[k]['stimType'] == 'Image':
                    t.append(self.dispImageStim(dispMovie[k]['stim'], screen=k))
                elif dispMovie[k]['stimType'] == 'Audio' and trialType != 0:  # No still-frame equivalent
                    t.append(self.dispAudioStim(trialType, dispMovie[k]['stim']))
                elif dispMovie[k]['stimType'] == 'Image with audio':  # Audio and image together
                    if trialType != 0:  # No still-frame equivalent
                        t.append(self.dispAudioStim(trialType, dispMovie[k]['stim']['Audio']))
                    else:
                        t.append(0)
                    p = self.dispImageStim(dispMovie[k]['stim']['Image'], screen=k)
                else:
                    t.append(0)
            if sum(t) >= len(t):
                return 1
            else:
                return 0
        else:
            return 0


    def printCurrentData(self):
        """
        Prints current data to output window, HPP variant. Only called when stimulus presentation is off.

        :return:
        :rtype:
        """

        print("hab crit, on-timeC, numOnC, on-timeL, numOnL, onTimeR, numOnR, offTime, numOff, trialDuration")
        print("-------------------------------------------------------------------------------------------")
        for i in range(0, len(self.dataMatrix)):
            dataList = [self.dataMatrix[i]['habCrit'], round(self.dataMatrix[i]['sumOnC'],1),
                        self.dataMatrix[i]['numOnC'], round(self.dataMatrix[i]['sumOnL'],1),
                        self.dataMatrix[i]['numOnL'], round(self.dataMatrix[i]['sumOnR'],1),
                        self.dataMatrix[i]['numOnR'], round(self.dataMatrix[i]['sumOff'],1),
                        self.dataMatrix[i]['numOff'], self.dataMatrix[i]['trialDuration']]
            print(dataList)

    def doTrial(self, number, ttype, disMovie):
        """
        Control function for individual trials, to be called by doExperiment
        Returns a status value (int) that tells doExperiment what to do next
        HPP experiments works very differently from everything else, and this is where the bulk of that is happening.

        TODO: Add MinDur

        :param number: Trial number
        :type number: int
        :param ttype: Trial type
        :type ttype: string
        :param disMovie: A dictionary with three indexes, one per screen. Any screen with stimuli on it will have a dictionary {stimType:,stim:}
        :type disMovie: dict
        :return: int, 0 = proceed to next trial, 1 = hab crit met, 2 = end experiment, 3 = trial aborted
        :rtype:
        """

        self.trialText.text = "Trial no. " + str(number)
        habTrial = False  # Just for tracking if this is part of a habituation, whether or not it is included in the hab calc
        habBlock = ''
        localType = deepcopy(ttype)
        while '.' in localType:
            localType = localType[localType.index('.') + 1:]
        if '*' in ttype:  # Hab block trial
            # Hab trials have this * marker, but also the hab block will always be the top-level block, i.e., before the first .
            # Even if it's a one-trial block this will be true.
            # datatype should be the full block-trial name minus *^
            dataType = ttype.translate({94: None, 42: None})
            habBlock = ttype[:ttype.index('*')]
            # Now we need to trim out the hab number. Assume maxHab < 100
            for b, c in self.habCount.items():
                if habBlock[0:len(b)] == b and habBlock[len(b):] == str(c + 1):
                    habBlock = habBlock[0:len(b)]
            habTrial = True
        else:
            dataType = ttype
        self.frameCount = {k: 0 for k, v in self.frameCount.items()}
        self.pauseCount = {k: 0 for k, v in self.pauseCount.items()}
        stimScreens = []  # Records the screens on which simuli appear.
        # If we're dealing with a movie or movies, seek to 0.
        for i, j in disMovie.items():
            if j not in [0, '0']:
                # Check which screen have stimuli for this trial
                stimScreens.append(i)
            if j not in [0, '0'] and self.stimPres:
                if j['stimType'] == 'Movie':
                    j['stim'].seek(0.0)
                    j['stim'].pause()
            elif self.stimPres:
                # This is for an edge case where you autoadvance from one trial into a trial that presents on different
                # screens, to blank those screens, because by default autoadvance stops PyHab from wiping a screen.
                if i == 'C':
                    self.win.flip()
                elif i == 'L':
                    self.winL.flip()
                elif i == 'R':
                    self.winR.flip()
        startTrial = core.getTime()
        onArrayC = []
        offArray = []
        onArrayL = []
        onArrayR = []
        numOnC = 0
        numOff = 0
        sumOnC = 0
        sumOnL = 0
        sumOnR = 0
        numOnL = 0
        numOnR = 0
        maxDurAdd = 0
        abort = False
        runTrial = True
        endFlag = False
        gazeOnC = False
        gazeOnL = False
        gazeOnR = False
        endNow = False

        self.trialTiming.append({'trialNum': number, 'trialType': dataType, 'event': 'startTrial',
                                 'time': (startTrial - self.absoluteStart)})

        def onDuration(adds=0, subs=0):  # A function for the duration switch, while leaving sumOn intact
            if localType in self.durationCriterion:
                return core.getTime() - startTrial - subs
            elif localType in self.hppStimScrOnly:
                # Only report duration for screens w/stimuli.
                runTotal = 0
                if 'C' in stimScreens:
                    runTotal = runTotal + sumOnC
                if 'L' in stimScreens:
                    runTotal = runTotal + sumOnL
                if 'R' in stimScreens:
                    runTotal = runTotal + sumOnR
                return runTotal + adds
            else:
                return sumOnC + sumOnL + sumOnR + adds

        if localType in self.onTimeDeadline.keys():
            deadlineChecked = False
        else:
            deadlineChecked = True
        self.readyText.text = "Trial running"
        if self.keyboard[self.centerKey]:
            gazeOnC = True
            startOnC = 0
            numOnC = 1
        elif self.keyboard[self.leftKey]:
            gazeOnL = True
            startOnL = 0
            numOnL = 1
        elif self.keyboard[self.rightKey]:
            gazeOnR = True
            startOnR = 0
            numOnR = 1
        else:
            startOff = 0
            dataStartOff = 0  # Separates 'off' for the data file and 'off' for deciding end of trial, for hppStimScrOnly situation
            numOff = 1
        while runTrial:
            if self.keyboard[self.key.R]: #'abort trial' is pressed
                abort = True
                runTrial = False
                endTrial = core.getTime() - startTrial
                # determine if they were looking or not at end of trial and update appropriate array
                if gazeOnC or gazeOnL or gazeOnR:
                    if gazeOnC:
                        onDurC = endTrial - startOnC
                        # Current format: Trial number, type, start of event, end of event, duration of event.
                        tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnC, 'endTime': endTrial,
                                         'duration': onDurC}
                        onArrayC.append(tempGazeArray)
                    if gazeOnL:
                        onDurL = endTrial - startOnL
                        tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnL, 'endTime': endTrial,
                                         'duration': onDurL}
                        onArrayL.append(tempGazeArray)
                    if gazeOnR:
                        onDurR = endTrial - startOnR
                        tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnR, 'endTime': endTrial,
                                         'duration': onDurR}
                        onArrayR.append(tempGazeArray)
                else:
                    offDur = endTrial - startOff
                    tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOff, 'endTime': endTrial,
                                     'duration': offDur}
                    offArray.append(tempGazeArray)
            elif core.getTime() - startTrial >= .5 and self.keyboard[self.key.S] and ttype != 'Hab' and '^' not in ttype:
                # End trial and go forward manually. Disabled for hab trials and meta-trials.
                # Disabled for the first half-second to stop you from skipping through multiple auto-advancing trials
                if localType in self.movieEnd or localType in self.minDur.keys():
                    endFlag = True
                else:
                    runTrial = False
                    endTrial = core.getTime() - startTrial
                    if not self.stimPres:
                        self.endTrialSound.play()
                        self.endTrialSound = sound.Sound('A', octave=4, sampleRate=48000, secs=0.2, stereo=True)
                    if gazeOnC or gazeOnL or gazeOnR:
                        if gazeOnC:
                            onDurC = endTrial - startOnC
                            # Current format: Trial number, type, start of event, end of event, duration of event.
                            tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnC,
                                             'endTime': endTrial,
                                             'duration': onDurC}
                            onArrayC.append(tempGazeArray)
                        if gazeOnL:
                            onDurL = endTrial - startOnL
                            tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnL,
                                             'endTime': endTrial,
                                             'duration': onDurL}
                            onArrayL.append(tempGazeArray)
                        if gazeOnR:
                            onDurR = endTrial - startOnR
                            tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnR,
                                             'endTime': endTrial,
                                             'duration': onDurR}
                            onArrayR.append(tempGazeArray)
                    else:
                        offDur = endTrial - startOff
                        tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOff,
                                         'endTime': endTrial,
                                         'duration': offDur}
                        offArray.append(tempGazeArray)
            elif self.keyboard[self.key.Y]:  # the 'end the study' button, for fuss-outs
                runTrial = False
                endTrial = core.getTime() - startTrial
                # determine if they were looking or not at end of trial and update appropriate array
                if gazeOnC or gazeOnL or gazeOnR:
                    if gazeOnC:
                        onDurC = endTrial - startOnC
                        # Current format: Trial number, type, start of event, end of event, duration of event.
                        tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnC,
                                         'endTime': endTrial,
                                         'duration': onDurC}
                        onArrayC.append(tempGazeArray)
                    if gazeOnL:
                        onDurL = endTrial - startOnL
                        tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnL,
                                         'endTime': endTrial,
                                         'duration': onDurL}
                        onArrayL.append(tempGazeArray)
                    if gazeOnR:
                        onDurR = endTrial - startOnR
                        tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnR,
                                         'endTime': endTrial,
                                         'duration': onDurR}
                        onArrayR.append(tempGazeArray)
                else:
                    offDur = endTrial - startOff
                    tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOff,
                                     'endTime': endTrial,
                                     'duration': offDur}
                    offArray.append(tempGazeArray)
                if len(onArrayC) == 0:
                    onArrayC.append({'trial':0, 'trialType':0, 'startTime':0, 'endTime':0, 'duration':0})
                if len(onArrayL) == 0:
                    onArrayL.append({'trial':0, 'trialType':0, 'startTime':0, 'endTime':0, 'duration':0})
                if len(onArrayR) == 0:
                    onArrayR.append({'trial':0, 'trialType':0, 'startTime':0, 'endTime':0, 'duration':0})
                if len(offArray) == 0:
                    offArray.append({'trial':0, 'trialType':0, 'startTime':0, 'endTime':0, 'duration':0})  # keeps it from crashing while trying to write data.
                ttype = 4  # to force an immediate quit.
                # Now for the non-abort states.
            elif core.getTime() - startTrial >= self.maxDur[localType] + maxDurAdd and not endFlag:  # reached max trial duration
                if localType in self.movieEnd or localType in self.minDur.keys():
                    endFlag = True
                else:
                    runTrial = False
                    endTrial = core.getTime() - startTrial
                    if not self.stimPres:
                        self.endTrialSound.play()
                        self.endTrialSound = sound.Sound('A', octave=4, sampleRate=48000, secs=0.2, stereo=True)
                    if gazeOnC or gazeOnL or gazeOnR:
                        if gazeOnC:
                            onDurC = endTrial - startOnC
                            # Current format: Trial number, type, start of event, end of event, duration of event.
                            tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnC,
                                             'endTime': endTrial,
                                             'duration': onDurC}
                            onArrayC.append(tempGazeArray)
                        if gazeOnL:
                            onDurL = endTrial - startOnL
                            tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnL,
                                             'endTime': endTrial,
                                             'duration': onDurL}
                            onArrayL.append(tempGazeArray)
                        if gazeOnR:
                            onDurR = endTrial - startOnR
                            tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnR,
                                             'endTime': endTrial,
                                             'duration': onDurR}
                            onArrayR.append(tempGazeArray)
                    else:
                        offDur = endTrial - startOff
                        tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOff,
                                         'endTime': endTrial,
                                         'duration': offDur}
                        offArray.append(tempGazeArray)
            elif not gazeOnC and not gazeOnL and not gazeOnR:  # This should happen rarely, but if it does...
                # In hppStimScreenOnly situations, startOff is defined differently, allowing both 'true' off and stim
                # screen off to work together.
                # dataStartOff exists to make sure the data file is still fully accurate to what actually happened.
                nowOff = core.getTime() - startTrial
                endCondMet = False
                if self.playThrough[localType] in [0,4]:  # Standard gaze-on then gaze-off
                    if onDuration(subs=nowOff-startOff) >= self.minOn[localType] and nowOff - startOff >= self.maxOff[localType] and not endFlag:
                        endCondMet = True
                    elif localType in self.autoRedo and deadlineChecked and nowOff - startOff >= self.maxOff[localType] and not endFlag:
                        endCondMet = True
                        endNow = True
                elif self.playThrough[localType] == 3:  # Either/or
                    if nowOff - startOff >= self.maxOff[localType] and not endFlag:
                        endCondMet = True
                        if localType in self.autoRedo and sumOnC + sumOnL + sumOnR < self.minOn[localType]:
                            endNow = True
                elif localType in self.autoRedo and sumOnC + sumOnL + sumOnR < self.minOn[localType]: # Only applies to on-time-only cases with auto-redo
                    if nowOff - startOff >= self.maxOff[localType] and not endFlag:
                        endCondMet = True
                        endNow = True

                if localType in self.autoRedo and nowOff >= self.onTimeDeadline[localType] and not deadlineChecked:
                    # NB: nowOff in this context is just duration of the trial, period.
                    deadlineChecked = True
                    if sumOnC + sumOnL + sumOnR < self.minOn[localType]:  # this specifically uses sumOn, always.
                        endCondMet = True
                        endNow = True

                if endCondMet:
                    # if they have previously looked for at least minOn seconds and now looked away for maxOff continuous sec
                    if (localType in self.movieEnd or localType in self.minDur.keys()) and not endNow:
                        endFlag = True
                    else:
                        runTrial = False
                        endTrial = core.getTime() - startTrial
                        if not self.stimPres:
                            self.endTrialSound.play()
                            self.endTrialSound = sound.Sound('A', octave=4, sampleRate=48000, secs=0.2, stereo=True)
                        endOff = nowOff
                        offDur = nowOff - dataStartOff
                        tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOff,
                                         'endTime': endOff,
                                         'duration': offDur}
                        offArray.append(tempGazeArray)
                elif self.keyboard[self.centerKey]: # if they have started looking since looking away
                    gazeOnC = True
                    numOnC = numOnC + 1
                    startOnC = core.getTime() - startTrial
                    endOff = core.getTime() - startTrial
                    # by definition, if this is tripped there will be a preceding 'off' section if this is tripped because gazeOn is set at start
                    offDur = endOff - dataStartOff
                    tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOff, 'endTime': endOff,
                                     'duration': offDur}
                    offArray.append(tempGazeArray)
                    if localType in self.dynamicPause and self.stimPres:
                        # Let's get fancy: This now only starts playing the thing on the screen they're looking at!
                        if disMovie['C'] != 0:
                            if disMovie['C']['stimType'] in ['Movie', 'Audio'] and not disMovie['C']['stim'].isPlaying:
                                disMovie['C']['stim'].play()
                            elif disMovie['C']['stimType'] == ['Image with audio'] and not disMovie['C']['stim']['Audio'].isPlaying:
                                disMovie['C']['stim']['Audio'].play()
                elif self.keyboard[self.leftKey]:
                    gazeOnL = True
                    numOnL = numOnL + 1
                    startOnL = core.getTime() - startTrial
                    endOff = core.getTime() - startTrial
                    # by definition, if this is tripped there will be a preceding 'off' section if this is tripped because gazeOn is set at start
                    offDur = endOff - dataStartOff
                    tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOff, 'endTime': endOff,
                                     'duration': offDur}
                    offArray.append(tempGazeArray)
                    if localType in self.dynamicPause and self.stimPres:
                        # Let's get fancy: This now only starts playing the thing on the screen they're looking at!
                        if disMovie['L'] != 0:
                            if disMovie['L']['stimType'] in ['Movie', 'Audio'] and not disMovie['L']['stim'].isPlaying:
                                disMovie['L']['stim'].play()
                            elif disMovie['L']['stimType'] == ['Image with audio'] and not disMovie['L']['stim']['Audio'].isPlaying:
                                disMovie['L']['stim']['Audio'].play()
                elif self.keyboard[self.rightKey]:
                    gazeOnR = True
                    numOnR = numOnR + 1
                    startOnR = core.getTime() - startTrial
                    endOff = core.getTime() - startTrial
                    # by definition, if this is tripped there will be a preceding 'off' section if this is tripped because gazeOn is set at start
                    offDur = endOff - dataStartOff
                    tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOff, 'endTime': endOff,
                                     'duration': offDur}
                    offArray.append(tempGazeArray)
                    if localType in self.dynamicPause and self.stimPres:
                        # Let's get fancy: This now only starts playing the thing on the screen they're looking at!
                        if disMovie['R'] != 0:
                            if disMovie['R']['stimType'] in ['Movie', 'Audio'] and not disMovie['R']['stim'].isPlaying:
                                disMovie['R']['stim'].play()
                            elif disMovie['R']['stimType'] == ['Image with audio'] and not disMovie['R']['stim']['Audio'].isPlaying:
                                disMovie['R']['stim']['Audio'].play()
                else:
                    if localType in self.midAG and self.stimPres:
                        if nowOff - startOff >= self.midAG[localType]['trigger']:
                            # TODO: Do something here to deal with recording data about mid-trial AG behavior?
                            if localType not in self.dynamicPause: # Need to pause it anyways to play the AG so they don't overlap
                                for i,j in disMovie.items():
                                    if j != 0:
                                        if j['stimType'] in ['Movie', 'Audio'] and j['stim'].isPlaying:
                                            j['stim'].pause()
                                        elif j['stimType'] == ['Image with audio'] and j['stim']['Audio'].isPlaying:
                                            j['stim']['Audio'].pause()
                            startAG = core.getTime()
                            tempTiming = {'trialNum': number, 'trialType': dataType, 'event': 'startAttnGetter',
                                          'time': (core.getTime() - self.absoluteStart)}
                            self.trialTiming.append(tempTiming)
                            self.attnGetter(localType, self.midAG[localType]['cutoff'], self.midAG[localType]['onmin'])
                            durAG = core.getTime() - startAG
                            tempTiming = {'trialNum': number, 'trialType': dataType, 'event': 'endAttnGetter',
                                          'time': (core.getTime() - self.absoluteStart)}
                            self.trialTiming.append(tempTiming)
                            maxDurAdd = maxDurAdd + durAG  # Increase max length of trial by duration that AG played.
                            if localType not in self.dynamicPause:
                                for i,j in disMovie.items():
                                    if j != 0:
                                        if j['stimType'] in ['Movie', 'Audio'] and not j['stim'].isPlaying:
                                            j['stim'].play()
                                        elif j['stimType'] == ['Image with audio'] and not j['stim']['Audio'].isPlaying:
                                            j['stim']['Audio'].play()
            elif gazeOnC or gazeOnL or gazeOnR:
                nowOn = core.getTime() - startTrial
                # HPP naturally makes this much more complex.
                if gazeOnC:
                    tempOn = startOnC
                elif gazeOnL:
                    tempOn = startOnL
                elif gazeOnR:
                    tempOn = startOnR

                # Modify addition for hppStimScrOnly
                tmpAdd = nowOn - tempOn
                if localType in self.hppStimScrOnly:
                    # Zero out tmpAdd if it's not the right screen, otherwise use as intended.
                    if gazeOnC and 'C' not in stimScreens:
                        tmpAdd = 0
                    if gazeOnL and 'L' not in stimScreens:
                        tmpAdd = 0
                    if gazeOnR and 'R' not in stimScreens:
                        tmpAdd = 0

                if self.playThrough[localType] in [1,3] and onDuration(adds=tmpAdd) >= self.minOn[localType] and not endFlag:
                    # If the "on-only" condition has been met
                    if (localType in self.movieEnd or localType in self.minDur.keys()) and not endNow:
                        endFlag = True
                    else:
                        runTrial = False
                        endTrial = core.getTime() - startTrial
                        if not self.stimPres:
                            self.endTrialSound.play()
                            self.endTrialSound = sound.Sound('A', octave=4, sampleRate=48000, secs=0.2, stereo=True)
                        if gazeOnC:
                            onDur = endTrial - startOnC
                            tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnC,
                                             'endTime': endTrial, 'duration': onDur}
                            onArrayC.append(tempGazeArray)
                        if gazeOnL:
                            onDur = endTrial - startOnL
                            tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnL,
                                             'endTime': endTrial, 'duration': onDur}
                            onArrayL.append(tempGazeArray)
                        if gazeOnR:
                            onDur = endTrial - startOnR
                            tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnR,
                                             'endTime': endTrial, 'duration': onDur}
                            onArrayR.append(tempGazeArray)
                elif self.playThrough[localType] == 4 and onDuration(adds=tmpAdd) >= self.maxOn[localType] and not endFlag:
                    # If the "maxOn" condition has been met
                    if (localType in self.movieEnd or localType in self.minDur.keys()) and not endNow:
                        endFlag = True
                    else:
                        runTrial = False
                        endTrial = core.getTime() - startTrial
                        if not self.stimPres:
                            self.endTrialSound.play()
                            self.endTrialSound = sound.Sound('A', octave=4, sampleRate=48000, secs=0.2, stereo=True)
                        if gazeOnC:
                            onDur = endTrial - startOnC
                            tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnC,
                                             'endTime': endTrial, 'duration': onDur}
                            onArrayC.append(tempGazeArray)
                        if gazeOnL:
                            onDur = endTrial - startOnL
                            tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnL,
                                             'endTime': endTrial, 'duration': onDur}
                            onArrayL.append(tempGazeArray)
                        if gazeOnR:
                            onDur = endTrial - startOnR
                            tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnR,
                                             'endTime': endTrial, 'duration': onDur}
                            onArrayR.append(tempGazeArray)

                if localType in self.hppStimScrOnly and runTrial and not endFlag:
                    # Specific circumstances around hppStimScreenOnly, allowing it to end trials with 'gaze-off'
                    # todo: Need to integrate mid-trial attention-getter behavior as well
                    stimScreenOff = False
                    if gazeOnC and 'C' not in stimScreens:
                        stimScreenOff = True
                    if gazeOnL and 'L' not in stimScreens:
                        stimScreenOff = True
                    if gazeOnR and 'R' not in stimScreens:
                        stimScreenOff = True

                    if stimScreenOff:
                        # essentially the 'off-time' comparison from the normal off-time condition
                        nowOff = core.getTime() - startTrial
                        endCondMet = False
                        if self.playThrough[localType] == 0:  # Standard gaze-on then gaze-off
                            if onDuration(subs=nowOff - startOff) >= self.minOn[localType] and nowOff - startOff >= self.maxOff[localType] and not endFlag:
                                endCondMet = True
                            elif localType in self.autoRedo and deadlineChecked and nowOff - startOff >= self.maxOff[localType] and not endFlag:
                                endCondMet = True
                                endNow = True
                        elif self.playThrough[localType] == 3:  # Either/or
                            if nowOff - startOff >= self.maxOff[localType] and not endFlag:
                                endCondMet = True
                                if localType in self.autoRedo and onDuration(subs=nowOff - startOff) < self.minOn[localType]:
                                    endNow = True
                        elif localType in self.autoRedo and onDuration(subs=nowOff - startOff) < self.minOn[localType]:
                            if nowOff - startOff >= self.maxOff[localType] and not endFlag:
                                endCondMet = True
                                endNow = True

                        if endCondMet:
                            # if they have previously looked for at least minOn seconds and now looked away for maxOff continuous sec
                            if (localType in self.movieEnd or localType in self.minDur.keys()) and not endNow:
                                endFlag = True
                            else:
                                runTrial = False
                                endTrial = core.getTime() - startTrial
                                if not self.stimPres:
                                    self.endTrialSound.play()
                                    self.endTrialSound = sound.Sound('A', octave=4, sampleRate=48000, secs=0.2, stereo=True)
                                if gazeOnC:
                                    onDur = endTrial - startOnC
                                    tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnC,
                                                     'endTime': endTrial, 'duration': onDur}
                                    onArrayC.append(tempGazeArray)
                                if gazeOnL:
                                    onDur = endTrial - startOnL
                                    tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnL,
                                                     'endTime': endTrial, 'duration': onDur}
                                    onArrayL.append(tempGazeArray)
                                if gazeOnR:
                                    onDur = endTrial - startOnR
                                    tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnR,
                                                     'endTime': endTrial, 'duration': onDur}
                                    onArrayR.append(tempGazeArray)
                        elif localType in self.midAG and self.stimPres:
                            if nowOff - startOff >= self.midAG[localType]['trigger']:
                                # TODO: Do something here to deal with recording data about mid-trial AG behavior?
                                if localType not in self.dynamicPause:  # Need to pause it anyways to play the AG so they don't overlap
                                    for i, j in disMovie.items():
                                        if j != 0:
                                            if j['stimType'] in ['Movie', 'Audio'] and j['stim'].isPlaying:
                                                j['stim'].pause()
                                            elif j['stimType'] == ['Image with audio'] and j['stim']['Audio'].isPlaying:
                                                j['stim']['Audio'].pause()
                                startAG = core.getTime()
                                self.attnGetter(localType, self.midAG[localType]['cutoff'],
                                                self.midAG[localType]['onmin'])
                                durAG = core.getTime() - startAG
                                maxDurAdd = maxDurAdd + durAG  # Increase max length of trial by duration that AG played.
                                if localType not in self.dynamicPause:
                                    for i, j in disMovie.items():
                                        if j != 0:
                                            if j['stimType'] in ['Movie', 'Audio'] and not j['stim'].isPlaying:
                                                j['stim'].play()
                                            elif j['stimType'] == ['Image with audio'] and not j['stim'][
                                                'Audio'].isPlaying:
                                                j['stim']['Audio'].play()


                if gazeOnC and not self.keyboard[self.centerKey]:
                    gazeOnC = False
                    endOn = core.getTime() - startTrial
                    onDur = endOn - startOnC
                    tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnC, 'endTime': endOn,
                                     'duration': onDur}
                    onArrayC.append(tempGazeArray)
                    sumOnC = sumOnC + onDur
                    if localType in self.dynamicPause and self.stimPres:
                        if disMovie['C'] != 0:
                            if disMovie['C']['stimType'] in ['Movie','Audio'] and disMovie['C']['stim'].isPlaying:
                                disMovie['C']['stim'].pause()
                            elif disMovie['C']['stimType'] == ['Image with audio'] and disMovie['C']['stim']['Audio'].isPlaying:
                                disMovie['C']['stim']['Audio'].pause()
                    if self.keyboard[self.leftKey]:
                        gazeOnL = True
                        numOnL = numOnL + 1
                        startOnL = core.getTime() - startTrial
                        if localType in self.hppStimScrOnly:
                            # If L is not a stim screen but C, the previous on, was
                            if 'L' not in stimScreens and 'C' in stimScreens:
                                startOff = core.getTime() - startTrial
                    elif self.keyboard[self.rightKey]:
                        gazeOnR = True
                        numOnR = numOnR + 1
                        startOnR = core.getTime() - startTrial
                        if localType in self.hppStimScrOnly:
                            # If R is not a stim screen but C, the previous on, was
                            if 'R' not in stimScreens and 'C' in stimScreens:
                                startOff = core.getTime() - startTrial
                    else:
                        numOff = numOff + 1
                        startOff = core.getTime() - startTrial
                        dataStartOff = core.getTime() - startTrial
                if gazeOnL and not self.keyboard[self.leftKey]:
                    gazeOnL = False
                    endOn = core.getTime() - startTrial
                    onDur = endOn - startOnL
                    tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnL, 'endTime': endOn,
                                     'duration': onDur}
                    onArrayL.append(tempGazeArray)
                    sumOnL = sumOnL + onDur
                    if localType in self.dynamicPause and self.stimPres:
                        if disMovie['L'] != 0:
                            if disMovie['L']['stimType'] in ['Movie','Audio'] and disMovie['L']['stim'].isPlaying:
                                disMovie['L']['stim'].pause()
                            elif disMovie['L']['stimType'] == ['Image with audio'] and disMovie['L']['stim']['Audio'].isPlaying:
                                disMovie['L']['stim']['Audio'].pause()
                    if self.keyboard[self.centerKey]:
                        gazeOnC = True
                        numOnC = numOnC + 1
                        startOnC = core.getTime() - startTrial
                        if localType in self.hppStimScrOnly:
                            # If C is not a stim screen but L, the previous on, was
                            if 'C' not in stimScreens and 'L' in stimScreens:
                                startOff = core.getTime() - startTrial
                    elif self.keyboard[self.rightKey]:
                        gazeOnR = True
                        numOnR = numOnR + 1
                        startOnR = core.getTime() - startTrial
                        if localType in self.hppStimScrOnly:
                            # If R is not a stim screen but L, the previous on, was
                            if 'R' not in stimScreens and 'L' in stimScreens:
                                startOff = core.getTime() - startTrial
                    else:
                        numOff = numOff + 1
                        startOff = core.getTime() - startTrial
                        dataStartOff = core.getTime() - startTrial
                if gazeOnR and not self.keyboard[self.rightKey]:
                    gazeOnR = False
                    endOn = core.getTime() - startTrial
                    onDur = endOn - startOnR
                    tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnR, 'endTime': endOn,
                                     'duration': onDur}
                    onArrayR.append(tempGazeArray)
                    sumOnR = sumOnR + onDur
                    if localType in self.dynamicPause and self.stimPres:
                        if disMovie['R'] != 0:
                            if disMovie['R']['stimType'] in ['Movie','Audio'] and disMovie['R']['stim'].isPlaying:
                                disMovie['R']['stim'].pause()
                            elif disMovie['R']['stimType'] == ['Image with audio'] and disMovie['R']['stim']['Audio'].isPlaying:
                                disMovie['R']['stim']['Audio'].pause()
                    if self.keyboard[self.centerKey]:
                        gazeOnC = True
                        numOnC = numOnC + 1
                        startOnC = core.getTime() - startTrial
                        if localType in self.hppStimScrOnly:
                            # If C is not a stim screen but R, the previous on, was
                            if 'C' not in stimScreens and 'R' in stimScreens:
                                startOff = core.getTime() - startTrial
                    elif self.keyboard[self.leftKey]:
                        gazeOnL = True
                        numOnL = numOnL + 1
                        startOnL = core.getTime() - startTrial
                        if localType in self.hppStimScrOnly:
                            # If L is not a stim screen but R, the previous on, was
                            if 'L' not in stimScreens and 'R' in stimScreens:
                                startOff = core.getTime() - startTrial
                    else:
                        numOff = numOff + 1
                        startOff = core.getTime() - startTrial
                        dataStartOff = core.getTime() - startTrial
            movieStatus = self.dispTrial(localType, disMovie)
            if endFlag:
                if localType in self.movieEnd and movieStatus >= 1:
                    runTrial = False
                    endTrial = core.getTime() - startTrial
                    if not self.stimPres:
                        self.endTrialSound.play()
                        self.endTrialSound = sound.Sound('A', octave=4, sampleRate=48000, secs=0.2, stereo=True)
                    if gazeOnC:
                        onDur = endTrial - startOnC
                        tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnC,
                                         'endTime': endTrial, 'duration': onDur}
                        onArrayC.append(tempGazeArray)
                    if gazeOnL:
                        onDur = endTrial - startOnL
                        tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnL,
                                         'endTime': endTrial, 'duration': onDur}
                        onArrayL.append(tempGazeArray)
                    if gazeOnR:
                        onDur = endTrial - startOnR
                        tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnR,
                                         'endTime': endTrial, 'duration': onDur}
                        onArrayR.append(tempGazeArray)
                    else:
                        offDur = endTrial - startOff
                        tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOff,
                                         'endTime': endTrial, 'duration': offDur}
                        offArray.append(tempGazeArray)
                elif localType in self.minDur.keys():
                    if self.minDur[localType] <= core.getTime() - startTrial:
                        runTrial = False
                        endTrial = core.getTime() - startTrial
                        if not self.stimPres:
                            self.endTrialSound.play()
                            self.endTrialSound = sound.Sound('A', octave=4, sampleRate=48000, secs=0.2, stereo=True)
                        if gazeOnC:
                            onDur = endTrial - startOnC
                            tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnC,
                                             'endTime': endTrial, 'duration': onDur}
                            onArrayC.append(tempGazeArray)
                        if gazeOnL:
                            onDur = endTrial - startOnL
                            tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnL,
                                             'endTime': endTrial, 'duration': onDur}
                            onArrayL.append(tempGazeArray)
                        if gazeOnR:
                            onDur = endTrial - startOnR
                            tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOnR,
                                             'endTime': endTrial, 'duration': onDur}
                            onArrayR.append(tempGazeArray)
                        else:
                            offDur = endTrial - startOff
                            tempGazeArray = {'trial': number, 'trialType': dataType, 'startTime': startOff,
                                             'endTime': endTrial, 'duration': offDur}
                            offArray.append(tempGazeArray)
        self.trialTiming.append({'trialNum': number, 'trialType': dataType, 'event': 'endTrial',
                                 'time': (core.getTime() - self.absoluteStart)})
        if habTrial:
            habDataRec = self.habCount[habBlock] + 1
            habCrit = self.habCrit[habBlock]
        else:
            habDataRec = 0
            habCrit = -1
        if self.stimPres:
            # Reset everything, stop playing sounds and movies.
            for i, j in disMovie.items():
                if j != 0:
                    if j['stimType'] == 'Movie':
                        j['stim'].seek(0.0)  # this is the reset, we hope.
                        j['stim'].pause()
                    elif j['stimType'] == 'Audio':
                        j['stim'].stop()
                    elif j['stimType'] == 'Image with audio':
                        j['stim']['Audio'].stop()
        self.statusSquareA.fillColor = 'black'
        self.statusSquareB.fillColor = 'black'
        self.statusSquareL.fillColor = 'black'
        self.statusTextA.text = ""
        self.statusTextB.text = ""
        self.statusTextL.text = ""
        self.statusSquareA.draw()
        self.statusSquareB.draw()
        self.statusSquareL.draw()
        if self.blindPres < 2:
            self.trialText.draw()
            if self.blindPres < 1:
                self.readyText.draw()
        self.win2.flip()

        if self.stimPres and number < len(self.actualTrialOrder):
            tmpNxt = deepcopy(self.actualTrialOrder[number])
            while '.' in tmpNxt:
                tmpNxt = tmpNxt[tmpNxt.index('.') + 1:]
            # Unlike other modes, if there's an attngetter it blanks ALL the screens for that too.
            if tmpNxt not in self.autoAdvance or tmpNxt in self.playAttnGetter:
                self.dummyThing.draw()
                self.win.flip()  # blanks the screen outright between trials if NOT auto-advancing into the next trial
                self.winL.flip()
                self.winR.flip()
        finalSumOn = 0
        # Check if this is an auto-redo situation
        if localType not in self.durationCriterion:
            if localType not in self.hppStimScrOnly:
                for o in range(0, len(onArrayC)):
                    finalSumOn = finalSumOn + onArrayC[o]['duration']
                for p in range(0, len(onArrayL)):
                    finalSumOn = finalSumOn + onArrayL[p]['duration']
                for q in range(0, len(onArrayR)):
                    finalSumOn = finalSumOn + onArrayR[q]['duration']
            else:  # If hppStimScreenOnly is used, only pay attention to those screens.
                if 'C' in stimScreens:
                    for o in range(0, len(onArrayC)):
                        finalSumOn = finalSumOn + onArrayC[o]['duration']
                if 'L' in stimScreens:
                    for p in range(0, len(onArrayL)):
                        finalSumOn = finalSumOn + onArrayL[p]['duration']
                if 'R' in stimScreens:
                    for q in range(0, len(onArrayR)):
                        finalSumOn = finalSumOn + onArrayR[q]['duration']
        else:
            finalSumOn = core.getTime() - startTrial  # Checks total duration, ignores last-look issue.
        if localType in self.autoRedo and finalSumOn < self.minOn[localType] and ttype != 4:
            # Determine if total on-time is less that minOn, if so, flag trial as bad and repeat it
            abort = True
        if abort:  # if the abort button was pressed
            if self.stimPres:
                for i, j in disMovie.items():
                    if j != 0:
                        if j['stimType'] == 'Movie':
                            j['stim'].seek(0.0)  # this is the reset, we hope.
                            j['stim'].pause()
            self.abortTrial(onArrayC, offArray, number, dataType, onArrayL, onArrayR, self.stimName, habDataRec, habCrit)
            return 3
        else:
            self.dataRec(onArrayC, offArray, number, dataType, onArrayL, onArrayR, self.stimName, habDataRec, habCrit)
        if habTrial:
            if self.habMetWhen[habBlock] == -1 and not abort:  # if still during habituation
                if localType in self.blockList[habBlock]['calcHabOver']:
                    tempSum = 0
                    # This if for habituation by total trial duration, ignores hppStimScrOnly
                    if self.blockList[habBlock]['habByDuration']:
                        for c in range(0, len(onArrayC)):
                            tempSum += onArrayC[c]['duration']
                        for d in range(0, len(onArrayL)):
                            tempSum += onArrayL[d]['duration']
                        for g in range(0, len(onArrayR)):
                            tempSum += onArrayR[g]['duration']
                        for f in range(0, len(offArray)):
                            tempSum += offArray[f]['duration']
                        if self.durationInclude == 0 and len(offArray) > 0:
                            if offArray[-1]['endTime'] > onArrayC[-1]['endTime'] and offArray[-1]['endTime'] > onArrayL[-1]['endTime'] and offArray[-1]['endTime'] > onArrayR[-1]['endTime']:
                                tempSum = tempSum - offArray[-1]['duration']
                    else:
                        # If HPPStimScrOnly, hab only pays attention to the relevant screen.
                        # Because CheckStop only looks at habDataCompiled, this can be done entirely here.
                        if localType in self.hppStimScrOnly:
                            if 'C' in stimScreens:
                                for c in range(0, len(onArrayC)):
                                    tempSum += onArrayC[c]['duration']
                            if 'L' in stimScreens:
                                for d in range(0, len(onArrayL)):
                                    tempSum += onArrayL[d]['duration']
                            if 'R' in stimScreens:
                                for f in range(0, len(onArrayR)):
                                    tempSum += onArrayR[f]['duration']
                        else:
                            for c in range(0, len(onArrayC)):
                                tempSum += onArrayC[c]['duration']
                            for d in range(0, len(onArrayL)):
                                tempSum += onArrayL[d]['duration']
                            for f in range(0, len(onArrayR)):
                                tempSum += onArrayR[f]['duration']
                    self.habDataCompiled[habBlock][self.habCount] += tempSum
                if ttype == 4:
                    return 2
                elif '^' in ttype:
                    self.habCount[habBlock] += 1
                    # Check if criteria need to be set or have been met
                    if self.checkStop(habBlock):  # If criteria met
                        # Check if there are any trials FOLLOWING the hab trials.
                        # First we find the last hab trial in THIS hab block.
                        maxHab = 0
                        if habBlock in self.actualTrialOrder[number][0:len(habBlock)] and '^' in self.actualTrialOrder[number]:
                            maxHab = number
                        if maxHab < len(self.actualTrialOrder) - 1:
                            return 1
                        else:
                            return 2  # End experiment.
                    else:
                        return 0
                else:
                    return 0
        elif number >= len(self.actualTrialOrder) or ttype == 4:
            # End experiment
            return 2
        else:
            #Proceed as normal
            return 0

    def endExperiment(self):
        """
        End experiment, save all data, calculate reliability if needed, close up shop
        :return:
        :rtype:
        """
        tempText = visual.TextStim(self.win2, text="Saving data...", pos=[0, 0], color='white', bold=True, height=40)
        tempText.draw()
        self.win2.flip()
        if self.stimPres:
            self.dummyThing.draw()
            if self.endImageObject is not None:
                self.endImageObject.draw()
            self.win.flip()
            self.winL.flip()
            self.winR.flip()
        if len(self.blockDataList) > 0 and self.blockSum:
            tempMatrix = self.saveBlockFile()
            # Now write the actual data file
            nDupe = ''  # This infrastructure eliminates the risk of overwriting existing data
            o = 1
            blockfilename = self.dataFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + nDupe + '_BlockSumm_' + str(
                            self.today.month) + str(self.today.day) + str(self.today.year) + '.csv'
            while os.path.exists(blockfilename):
                o += 1
                nDupe = str(o)
                blockfilename = self.dataFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + nDupe + '_BlockSumm_' + str(
                                self.today.month) + str(self.today.day) + str(self.today.year) + '.csv'
            with open(blockfilename, 'w') as b:
                blockWriter = csv.DictWriter(b, fieldnames=self.dataColumns, extrasaction='ignore', lineterminator='\n')
                blockWriter.writeheader()
                for z in range(0, len(tempMatrix)):
                    blockWriter.writerow(tempMatrix[z])

        # If there is habituation data, create hab summary file. Similar to the block one, but a little easier thanks to
        # the tagging of habituation trial numbers.
        wasHab = False
        for q, r in self.blockList.items():
            if r['habituation'] in [1, '1', True, 'True']:
                wasHab = True
        if wasHab:  # If there's a 'Hab' trial type, the main summary file does the trick just fine.
            habMatrix = self.saveHabFile()
            # Now, actually write the file
            nDupe = ''  # This infrastructure eliminates the risk of overwriting existing data
            o = 1
            habfilename = self.dataFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + nDupe + '_HabSumm_' + str(
                self.today.month) + str(self.today.day) + str(self.today.year) + '.csv'
            while os.path.exists(habfilename):
                o += 1
                nDupe = str(o)
                habfilename = self.dataFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + nDupe + '_HabSumm_' + str(
                    self.today.month) + str(self.today.day) + str(self.today.year) + '.csv'
            with open(habfilename, 'w') as h:
                habWriter = csv.DictWriter(h, fieldnames=self.dataColumns, extrasaction='ignore',
                                           lineterminator='\n')
                habWriter.writeheader()
                for z in range(0, len(habMatrix)):
                    habWriter.writerow(habMatrix[z])

        # Shuffle together bad data and good data into the appropriate order.
        if len(self.badTrials) > 0:  # if there are any redos, they need to be shuffled in appropriately.
            for i in range(0, len(self.badTrials)):
                x = 0
                while x < len(self.dataMatrix) and self.dataMatrix[x]['trial'] != self.badTrials[i]['trial']:
                    x += 1
                while x < len(self.dataMatrix) and self.dataMatrix[x]['GNG'] == 0:  # this is to get around the possibility that the same trial had multiple 'false starts'
                    x += 1
                self.dataMatrix.insert(x, self.badTrials[i])  # python makes this stupid easy
        # Trial-level summary file:
        if self.trialSum:
            nDupe = ''  # This infrastructure eliminates the risk of overwriting existing data
            o = 1
            filename = self.dataFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + nDupe + '_' + str(
                self.today.month) + str(
                self.today.day) + str(self.today.year) + '.csv'
            while os.path.exists(filename):
                o += 1
                nDupe = str(o)
                filename = self.dataFolder + self.prefix + str(self.sNum) + '_' + str(
                    self.sID) + nDupe + '_' + str(
                    self.today.month) + str(
                    self.today.day) + str(self.today.year) + '.csv'
            with open(filename, 'w') as f:
                outputWriter = csv.DictWriter(f, fieldnames=self.dataColumns, extrasaction='ignore',
                                              lineterminator='\n')
                outputWriter.writeheader()
                for r in range(0, len(self.dataMatrix)):
                    # print('writing rows')
                    outputWriter.writerow(self.dataMatrix[r])

        if self.stimPres:
            nDupe = ''  # This infrastructure eliminates the risk of overwriting existing data
            o = 1
            filename = self.timingFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + nDupe + '_' + str(
                self.today.month) + str(
                self.today.day) + str(self.today.year) + '_trialTiming.csv'
            while os.path.exists(filename):
                o += 1
                nDupe = str(o)
                filename = self.timingFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + nDupe + '_' + str(
                    self.today.month) + str(
                    self.today.day) + str(self.today.year) + '_trialTiming.csv'
            timingHeaders = ['trialNum', 'trialType', 'event', 'time']
            with open(filename, 'w') as f:
                outputWriter = csv.DictWriter(f, fieldnames=timingHeaders, extrasaction='ignore', lineterminator='\n')
                outputWriter.writeheader()
                for r in range(0, len(self.trialTiming)):
                    # print('writing rows')
                    outputWriter.writerow(self.trialTiming[r])

        # Verbose data saving.
        verboseMatrix = []
        # first, verbose data is not as well organized. However, we should be able to alternate back and forth between
        # on and off until we reach the end of a given trial, to reconstruct it.
        # at the start of each line, add information: sNum, ageMo, ageDay, sex, cond, GNG, ON/OFF
        for n in range(0, len(self.verbDatList['verboseOnC'])):
            self.verbDatList['verboseOnC'][n].update(
                {'snum': self.sNum, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex,
                 'cond': self.cond, 'GNG': 1, 'gazeOnOff': 2})
        for q in range(0, len(self.verbDatList['verboseOnL'])):
            self.verbDatList['verboseOnL'][q].update(
                {'snum': self.sNum, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex,
                 'cond': self.cond, 'GNG': 1, 'gazeOnOff': 1})
        for r in range(0, len(self.verbDatList['verboseOnR'])):
            self.verbDatList['verboseOnR'][r].update(
                {'snum': self.sNum, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex,
                 'cond': self.cond, 'GNG': 1, 'gazeOnOff': 3})
        for m in range(0, len(self.verbDatList['verboseOff'])):  # adding the details to the verbose array
            self.verbDatList['verboseOff'][m].update(
                {'snum': self.sNum, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex,
                 'cond': self.cond, 'GNG': 1, 'gazeOnOff': 0})
        if len(self.badTrials) > 0:
            for o in range(0, len(self.verbBadList['verboseOnC'])):
                self.verbBadList['verboseOnC'][o].update(
                    {'snum': self.sNum, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex,
                     'cond': self.cond, 'GNG': 0, 'gazeOnOff': 2})
            for s in range(0, len(self.verbBadList['verboseOnL'])):
                self.verbBadList['verboseOnL'][s].update(
                    {'snum': self.sNum, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex,
                     'cond': self.cond, 'GNG': 0, 'gazeOnOff': 1})
            for t in range(0, len(self.verbBadList['verboseOnR'])):
                self.verbBadList['verboseOnR'][t].update(
                    {'snum': self.sNum, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex,
                     'cond': self.cond, 'GNG': 0, 'gazeOnOff': 3})
            for p in range(0, len(self.verbBadList['verboseOff'])):  # same details for the bad trials
                self.verbBadList['verboseOff'][p].update(
                    {'snum': self.sNum, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex,
                     'cond': self.cond, 'GNG': 0, 'gazeOnOff': 0})

        # read the final data matrix and go trial by trial.
        # print(verboseOn) #debug, to make sure verboseOn is being constructed correctly
        for q in range(0, len(self.dataMatrix)):
            tnum = self.dataMatrix[q]['trial']
            onIndexL = -1
            onIndexC = -1
            onIndexR = -1
            offIndex = -1
            if self.dataMatrix[q]['GNG'] == 1:  # separate for good and bad trials
                for w in range(0, len(self.verbDatList['verboseOnL'])):
                    if self.verbDatList['verboseOnL'][w]['trial'] == tnum and onIndexL == -1:
                        onIndexL = w
                for x in range(0, len(self.verbDatList['verboseOnC'])):
                    if self.verbDatList['verboseOnC'][x]['trial'] == tnum and onIndexC == -1:  # find the right index in the verbose matrices
                        onIndexC = x
                for y in range(0, len(self.verbDatList['verboseOnR'])):
                    if self.verbDatList['verboseOnR'][y]['trial'] == tnum and onIndexR == -1:  # find the right index in the verbose matrices
                        onIndexR = y
                for z in range(0, len(self.verbDatList['verboseOff'])):
                    if self.verbDatList['verboseOff'][z]['trial'] == tnum and offIndex == -1:
                        offIndex = z
                trialVerbose = []
                if onIndexC >= 0:
                    while onIndexC < len(self.verbDatList['verboseOnC']):
                        if self.verbDatList['verboseOnC'][onIndexC]['trial'] == tnum:
                            trialVerbose.append(self.verbDatList['verboseOnC'][onIndexC])
                        onIndexC += 1
                if onIndexL >= 0:
                    while onIndexL < len(self.verbDatList['verboseOnL']):
                        if self.verbDatList['verboseOnL'][onIndexL]['trial'] == tnum:
                            trialVerbose.append(self.verbDatList['verboseOnL'][onIndexL])
                        onIndexL += 1
                if onIndexR >= 0:
                    while onIndexR < len(self.verbDatList['verboseOnR']):
                        if self.verbDatList['verboseOnR'][onIndexR]['trial'] == tnum:
                            trialVerbose.append(self.verbDatList['verboseOnR'][onIndexR])
                        onIndexR += 1
                if offIndex >= 0:
                    while offIndex < len(self.verbDatList['verboseOff']):
                        if self.verbDatList['verboseOff'][offIndex]['trial']==tnum:
                            trialVerbose.append(self.verbDatList['verboseOff'][offIndex])
                        offIndex += 1
                trialVerbose2 = sorted(trialVerbose, key=lambda trialVerbose:trialVerbose['startTime']) #this is the magic bullet, Sorts by timestamp.
                verboseMatrix.extend(trialVerbose2)
            elif self.dataMatrix[q]['GNG'] == 0:  # bad trials.
                if q > 0 and self.dataMatrix[q - 1]['GNG'] == 0:
                    pass  # stops it from doubling up. If there is more than one consecutive bad trial, it will get all of them in a row the first time,
                else:
                    trialVerbose = []
                    for w in range(0, len(self.verbBadList['verboseOnL'])):
                        if self.verbBadList['verboseOnL'][w]['trial'] == tnum and onIndexL == -1:
                            onIndexL = w
                    for x in range(0, len(self.verbBadList['verboseOnC'])):
                        if self.verbBadList['verboseOnC'][x]['trial'] == tnum and onIndexC == -1:  # find the right index in the verbose matrices
                            onIndexC = x
                    for y in range(0, len(self.verbBadList['verboseOnR'])):
                        if self.verbBadList['verboseOnR'][y]['trial'] == tnum and onIndexR == -1:  # find the right index in the verbose matrices
                            onIndexR = y
                    for z in range(0, len(self.verbBadList['verboseOff'])):
                        if self.verbBadList['verboseOff'][z]['trial'] == tnum and offIndex == -1:
                            offIndex = z
                    if onIndexC >= 0:
                        while onIndexC < len(self.verbBadList['verboseOnC']):
                            if self.verbBadList['verboseOnC'][onIndexC]['trial'] == tnum:
                                trialVerbose.append(self.verbBadList['verboseOnC'][onIndexC])
                            onIndexC += 1
                    if onIndexL >= 0:
                        while onIndexL < len(self.verbBadList['verboseOnL']):
                            if self.verbBadList['verboseOnL'][onIndexL]['trial'] == tnum:
                                trialVerbose.append(self.verbBadList['verboseOnL'][onIndexL])
                            onIndexL += 1
                    if onIndexR >= 0:
                        while onIndexR < len(self.verbBadList['verboseOnR']):
                            if self.verbBadList['verboseOnR'][onIndexR]['trial'] == tnum:
                                trialVerbose.append(self.verbBadList['verboseOnR'][onIndexR])
                            onIndexR += 1
                    if offIndex >= 0:
                        while offIndex < len(self.verbBadList['verboseOff']):
                            if self.verbBadList['verboseOff'][offIndex]['trial']==tnum:
                                trialVerbose.append(self.verbBadList['verboseOff'][offIndex])
                            offIndex += 1
                    trialVerbose2 = sorted(trialVerbose, key=lambda trialVerbose:trialVerbose['startTime']) #this is the magic bullet, Sorts by timestamp.
                    verboseMatrix.extend(trialVerbose2)
        headers2 = ['snum', 'sID', 'months', 'days', 'sex', 'cond', 'GNG', 'gazeOnOff', 'trial', 'trialType',
                    'startTime', 'endTime', 'duration']
        with open(self.verboseFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + nDupe + '_' + str(
                self.today.month) + str(self.today.day) + str(self.today.year) + '_VERBOSE.csv', 'w') as f:
            outputWriter2 = csv.DictWriter(f, fieldnames=headers2, extrasaction='ignore',lineterminator='\n')
            outputWriter2.writeheader()
            for z in range(0, len(verboseMatrix)):
                outputWriter2.writerow(verboseMatrix[z])
        # core.wait(.3) Replaced by end-of-experiment screen
        # "end of experiment" screen. By default this will go to a black screen on the stim view
        # and display "Experiment finished!" on the experimenter view
        tempText.text = "Experiment finished! Press return to close."
        tempText.height = 18
        tempText.draw()
        self.win2.flip()
        if self.stimPres:
            self.dummyThing.draw()  # A safety to stop a weird graphical issue in PsychoPy3.
            if self.endImageObject is not None:
                self.endImageObject.draw()
            self.win.flip()
            self.winL.flip()
            self.winR.flip()
        event.waitKeys(keyList='return')

        self.win2.close()
        if self.stimPres:
            self.win.close()
            self.winL.close()
            self.winR.close()

    def SetupWindow(self):
        """
        An HPP-specific version of the function that sets up the windows and loads everything. With four windows to set
        up it's a real doozy, and has the added problem of needing to assign things properly to each window for stim
        presentation.

        TODO: Windows audio bug when loading an audio file before a movie means that we should change load order to movie first


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

            """
            Put any objects for animation stimuli here
            """


            # Clearing "checking framerate"
            self.win.flip()
            self.winL.flip()
            self.winR.flip()

        # Coder window
        self.win2 = visual.Window((400, 400), fullscr=False, screen=self.expScreenIndex, allowGUI=True, units='pix', waitBlanking=False,
                                  rgb=[-1, -1, -1])
        if self.stimPres:
            tempText = visual.TextStim(self.win2, text="Loading Stimuli", pos=[0, 0], color='white', bold=True, height=40)
            tempText.draw()
            self.win2.flip()
            # Step 1: Load and present "startImage"
            if self.startImage != '':  #TODO: For now start/end is restricted to center screen.
                self.dummyThing.draw()
                tempStim = self.stimList[self.startImage]
                tempStimObj = visual.ImageStim(self.win, tempStim['stimLoc'], size=[self.movieWidth['C'], self.movieHeight['C']])
                tempStimObj.draw()
                self.win.flip() # This should now be on the screen until the first attngetter
                self.winL.flip()
                self.winR.flip()
            self.stimDict = {x: [] for x in self.stimNames.keys()}  # This holds all the loaded movies.
            self.counters = {x: 0 for x in self.stimNames.keys()}  # list of counters, one per index of the dict, so it knows which movie to play
            tempCtr = {x: 0 for x in self.stimNames.keys()}
            for i in self.actualTrialOrder:
                # Adjust for block sub-trials. Looks for a very specific set of traits, which could occur, but...shouldn't.
                if '.' in i:
                    tempI = i
                    while '.' in tempI:
                        tempI = tempI[tempI.index('.')+1:]
                    i = tempI
                x = tempCtr[i]  # Changed so hab trials get the same treatment as everything else.
                # Stimuli data structure: stimDict is a dict of lists for each trial type that the counter iterates through. It now needs to be a list of dicts.
                # StimDict = {trialType:[{C:,L:,R:},{}]} 0 if nothing presented on that screen that trial, otherwise each one
                # {'stimType': tempStim['stimType'], 'stim': tempStimObj}
                if x < len(self.stimNames[i]):
                    tempOutput = {'C':0,'L':0,'R':0}
                    stim = self.stimNames[i][tempCtr[i]]
                    for z, j in stim.items():
                        if j not in [0, '0']:
                            scrn = z
                            tempOutput[scrn] = self.loadStim(stim[scrn], scrn)
                    tempCtr[i] += 1
                    self.stimDict[i].append(tempOutput)

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
            if self.endImage != '': # Load image for end of experiment, if needed.
                tempStim = self.stimList[self.endImage]
                self.endImageObject = visual.ImageStim(self.win, tempStim['stimLoc'], size=[self.movieWidth['C'], self.movieHeight['C']])
            else:
                self.endImageObject = None
        self.keyboard = self.key.KeyStateHandler()
        self.win2.winHandle.push_handlers(self.keyboard)
        if self.stimPres:
            self.win.winHandle.push_handlers(self.keyboard)
            self.winL.winHandle.push_handlers(self.keyboard)
            self.winR.winHandle.push_handlers(self.keyboard)
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
                                         pos=[self.statusOffset - 0, self.statusOffsetY + 0],
                                         fillColor='black')  # These two appear on the status screen window.
        self.statusSquareB = visual.Rect(self.win2, height=80, width=80,
                                         pos=[self.statusOffset + 80, self.statusOffsetY + 0], fillColor='black')
        self.statusSquareL = visual.Rect(self.win2, height=80, width=80,
                                         pos=[self.statusOffset - 80, self.statusOffsetY + 0], fillColor='black')
        self.statusTextA = visual.TextStim(self.win2, text="", pos=self.statusSquareA.pos,
                                           color='white', bold=True, height=30)
        self.statusTextB = visual.TextStim(self.win2, text="", pos=self.statusSquareB.pos,
                                           color='white', bold=True, height=30)
        self.statusTextL =  visual.TextStim(self.win2, text="", pos=self.statusSquareL.pos,
                                           color='white', bold=True, height=30)
        self.trialText = visual.TextStim(self.win2, text="Trial no: ", pos=[-100, 150], color='white')
        self.readyText = visual.TextStim(self.win2, text="Trial not active", pos=[-25, 100], color='white')
        self.doExperiment()  # Get this show on the road!