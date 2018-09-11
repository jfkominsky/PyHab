import os, sys
from psychopy import gui, visual, event, core, data, monitors, tools, prefs, logging
from psychopy.constants import (STARTED, PLAYING)  # Added for new stimulus types
if os.name is 'posix':
    prefs.general['audioLib'] = ['pyo']
    prefs.general['audioDevice'] = ['Built-in Output']
from psychopy import sound
import pyglet
from pyglet import input as pyglet_input
import wx, random, csv
from math import *
from datetime import *
from dateutil.relativedelta import *
from copy import deepcopy # needed for exactly one usage in redotrial because it's the only reasonable way.


class PyHab:
    """

    PyHab looking time coding + stimulus control system

    Jonathan Kominsky, 2016-2018

    Keyboard coding: A = ready, B = coder 1 on, L = coder 2 on, R = abort trial, Y = end experiment (for fussouts)

    Between-trials: R = redo previous trial, J = jump to test trial, I = insert additional habituation trial (hab only)

    Throughout this script, win2 is the coder display, win is the stimulus presentation window.
    dataMatrix is the primary data storage for the summary data file. It is a list of dicts, each
    dict corresponds to a trial.

    Anything called "verbose" is part of the verbose data file. There are up to four such structures:
    On (for gaze-on events)
    Off (for gaze-off events)
    On2 and Off2 (for the optional secondary coder)
    Each coder's on and off are recorded in a separate dict with trial, gaze on/off, start, end, and duration.

    """

    def __init__(self, settingsDict):
        """
        Read all settings from settings file

        :param settingsDict: a dict built from a csv by the launcher script and passed to the class
        :type settingsDict: dict
        """
        if os.name is 'posix':  # glorious simplicity of unix filesystem
            self.dirMarker = '/'
            otherOS = '\\'
        elif os.name is 'nt':  # Nonsensical Windows-based contrarianism
            self.dirMarker = '\\'
            otherOS = '/'
        self.dataColumns = eval(settingsDict['dataColumns'])
        self.prefix = settingsDict['prefix']  # prefix for data files. All data filenames will start with this text.
        self.dataFolder = settingsDict['dataloc']  # datafolder, condpath,stimPath are the ones that need modification.
        if len(self.dataFolder) > 0 and self.dataFolder[-1] is not self.dirMarker:
            self.dataFolder = [self.dirMarker if x == otherOS else x for x in self.dataFolder]
            self.dataFolder = ''.join(self.dataFolder)

        # UNIVERSAL SETTINGS
        self.maxDur = eval(settingsDict['maxDur'])  # maximum number of seconds in a trial - can be a constant or a dictionary with different times for EACH trial type (must include every type). {'A':20,'B':60} etc.
        self.playThrough = eval(settingsDict['playThrough'])  # A dict which informs what kind of gaze-contingency each trial type follows.
        self.movieEnd = eval(settingsDict['movieEnd'])  # A list of trial types that only end (in stim pres mode) on the end of the movie file associated with them.
        self.maxOff = eval(settingsDict['maxOff'])  # maximum number of consecutive seconds of offtime to end trial - by trial type
        self.minOn = eval(settingsDict['minOn'])  # minimum on-time for a trial (seconds) - by trial type
        self.blindPres = eval(settingsDict['blindPres'])  # 0, 1, or 2. 0 = show everything. 1 = show trial number + status squares. 2 = no trial #, status squares do not indicate on/off
        self.autoAdvance = eval(settingsDict['autoAdvance'])  # For creating studies where you don't want a lag between trials, just automatic advancement to the next.
        self.randPres = eval(settingsDict['randPres'])  # controls whether the program will look for an external randomization file to determine presentation order
        # If not, hab will present the first thing in each of the lists above, and VoE will just go through the lists in order
        self.condPath = settingsDict['condPath']  # path for the condition file.
        self.condFile = settingsDict['condFile']  # if you have a condition file, put filename here (WITH EXTENSION). Must be .csv
        self.condList = eval(settingsDict['condList'])  # list of conditions for the dropdown menu, if using random presentation.[SOON: GET AUTOMATICALLY FROM FILE]
        if len(self.condPath) > 0 and self.condPath[-1] is not self.dirMarker:
            self.condPath = [self.dirMarker if x == otherOS else x for x in self.condPath]
            self.condPath = ''.join(self.condPath)

        # ORDER OF PRESENTATION
        # NOTE: a SINGLE instance of 'Hab' will insert a contiguous habituation BLOCK of up to maxHabTrials.
        # Recommend you make sure repetitions of each trial type is a multiple of the list length, if you want even presentation
        self.trialOrder = eval(settingsDict['trialOrder'])

        # HABITUATION DESIGN SETTINGS
        self.maxHabTrials = eval(settingsDict['maxHabTrials'])  # number of habituation trials in a HAB design
        self.setCritWindow = eval(settingsDict['setCritWindow'])  # Number of trials to use when setting the habituation window, e.g., 3 = first three hab trials
        self.setCritDivisor = eval(settingsDict['setCritDivisor'])  # Divide sum of looking time over first setHabWindow trials by this value. for average, set equal to setHabWindow. For sum, set to 1.
        self.setCritType = settingsDict['setCritType']  # Criterion set by dynamic window or first set of trials
        self.metCritWindow = eval(settingsDict['metCritWindow'])  # size of moving window of trials to sum looking times and compare to habituation criterion.
        self.metCritDivisor = eval(settingsDict['metCritDivisor'])  # If you want to compare, e.g., average rather than sum of looking times of last metCritWindow trials, change this accordingly.
        self.metCritStatic = settingsDict['metCritStatic']  # Criterion evaluated over moving or static windows
        self.habTrialList = eval(settingsDict['habTrialList'])  # A new "meta-hab" trial type consisting of several sub-trial-types.

        # STIMULUS PRESENTATION SETTINGS
        self.stimPres = eval(settingsDict['stimPres'])  # For determining if the program is for stimulus presentation (True) or if it's just coding looking times (False)
        if not self.stimPres:
            self.movieEnd = []  # So we don't run into trouble with trials not ending waiting for movies that don't exist.
        self.stimPath = settingsDict['stimPath']  # Folder where movie files can be located (if not in same folder as script)
        self.stimNames = eval(settingsDict['stimNames'])
        # ^ A list of trial types. One is special: 'Hab' (only plays first entry), which should only be used for a habituation block in which you have a variable number of trials depending on a habituation criterion
        self.stimList = eval(settingsDict['stimList'])  # List of all stimuli in the experiment.
        self.screenWidth = eval(settingsDict['screenWidth'])  # Display window width, in pixels
        self.screenHeight = eval(settingsDict['screenHeight'])  # Display window height, in pixels
        self.screenColor = settingsDict['screenColor']  #Background color of stim window.
        self.movieWidth = eval(settingsDict['movieWidth'])  # movie width
        self.movieHeight = eval(settingsDict['movieHeight'])  # movie height
        self.screenIndex = eval(settingsDict['screenIndex'])  # which monitor stimuli are presented on. 1 for secondary monitor, 0 for primary monitor.
        self.ISI = eval(settingsDict['ISI'])  # time between loops (in seconds, if desired)
        self.freezeFrame = eval(settingsDict['freezeFrame'])  # time that movie remains on first frame at start of trial.
        self.playAttnGetter = eval(settingsDict['playAttnGetter'])  # Trial-by-trial marker of which attngetter goes with which trial (if applicable).
        self.attnGetterList = eval(settingsDict['attnGetterList'])  # List of all attention-getters
        if len(self.stimPath) > 0 and self.stimPath[-1] is not self.dirMarker:  # If it was made in one OS and running in another
            self.stimPath = [self.dirMarker if x == otherOS else x for x in self.stimPath]
            self.stimPath = ''.join(self.stimPath)

        '''
        END SETTINGS
        '''
        self.habCount = 0  # For hab designs, checks the # of habituation trials completed
        self.habCrit = 0  # initial setting of habcrit at 0
        self.dataMatrix = []  # primary data array
        # data format: snum, age in months, age in days, sex, condition, trial, GNGtrial, trial type, hab crit, on-time, number of gazes, off-time, number of look-offs
        # then same again at the end for b-coder?
        self.badTrials = []  # data array for bad trials
        self.verboseOn = []  # "verbose" data aray for gazes on, that includes each individual gaze, when it happened, etc.
        self.verboseOff = []  # same for off-time
        self.verboseOn2 = []  # for coder B. Can't assume that they will line up in terms of number of gazes so can't put them in same file.
        self.verboseOff2 = []  # for coder B.
        self.badVerboseOn = []  # same as above but for bad trials
        self.badVerboseOff = []  # same as above but for bad trials
        self.badVerboseOn2 = []  # as above for coder B
        self.badVerboseOff2 = []  # as above for coder B
        if not self.stimPres:
            self.endTrialSound = sound.Sound('A', octave=4, sampleRate=44100, secs=0.2)
            self.endHabSound = sound.Sound('G', octave=4, sampleRate=44100, secs=0.2)
        if type(self.maxDur) is int:  # Secretly MaxDur will always be a dict, but if it's a constant we just create the dict here
            tempDur = self.maxDur
            self.maxDur = {}  # create a dict
            # look up unique names in trialOrder to get all the trial types
            for x in self.trialOrder:
                self.maxDur[x] = tempDur  # Python: Yes, it really is that easy.
        self.statusOffset = 0
        self.statusOffsetY = 0
        self.testOffset = 0
        self.frameCount = 0  # the frame counter for the movement of A and B, based on the refresh rate.
        self.pauseCount = 0  # used for ISI calculations
        self.stimName = ''  # used for adding the name of the stimulus file to the output.
        self.key = pyglet.window.key  # This initiates the keyhandler. Here so we can then set the relevant keys.
        self.secondKey = self.key.L
        self.verbDatList = {'verboseOn':[], 'verboseOff':[], 'verboseOn2':[], 'verboseOff2':[]} # a dict of the verbose data arrays
        self.verbBadList = {'verboseOn':[], 'verboseOff':[], 'verboseOn2':[], 'verboseOff2':[]} # Corresponding for bad data

    '''
    FUNCTIONS
    '''

    def abortTrial(self, onArray, offArray, trial, ttype, onArray2, offArray2, stimName=''):  # the 2nd arrays are if there are two coders.
        """
        Only happens when the 'abort' button is pressed during a trial. Creates a "bad trial" entry
        out of any data recorded for the trial so far, to be saved later.

        :param onArray: Gaze-on events for coder 1
        :type onArray: list of dicts {trial, trialType, startTime, endTime, duration}
        :param offArray: Gaze-off events for coder 1
        :type offArray: list of dicts {trial, trialType, startTime, endTime, duration}
        :param trial: trial number
        :type trial: int
        :param ttype: trial type
        :type ttype: string
        :param onArray2: Gaze-on events for (optional) coder 2
        :type onArray2: list of dicts
        :param offArray2: Gaze-off events for (optional) coder 2
        :type offArray2: list of dicts
        :param stimName: If presenting stimuli, name of the stim file
        :type stimName: string
        :return:
        :rtype:
        """

        sumOn = 0
        sumOff = 0
        if ttype == 'Hab':
            self.habCount -= 1
        for i in range(0, len(onArray)):
            sumOn = sumOn + onArray[i]['duration']
        for j in range(0, len(offArray)):
            sumOff = sumOff + offArray[j]['duration']
        # needs to be .extend or you get weird array-within-array-within-array issues that become problematic later
        self.verbBadList['verboseOn'].extend(onArray)
        self.verbBadList['verboseOff'].extend(offArray)
        sumOn2 = 0
        sumOff2 = 0
        if len(onArray2) > 0 or len(offArray2) > 0:
            for i in range(0, len(onArray2)):
                sumOn2 = sumOn2 + onArray2[i]['duration']
            for j in range(0, len(offArray2)):
                sumOff2 = sumOff2 + offArray2[j]['duration']
            self.verbBadList['verboseOn2'].extend(onArray2)
            self.verbBadList['verboseOff2'].extend(offArray2)
        tempData = {'sNum': self.sNum, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex, 'cond': self.cond,
                    'condLabel': self.condLabel,'trial': trial, 'GNG': 0, 'trialType': ttype, 'stimName': stimName,
                    'habCrit': self.habCrit, 'sumOnA': sumOn, 'numOnA': len(onArray), 'sumOffA': sumOff,
                    'numOffA': len(offArray), 'sumOnB': sumOn2, 'numOnB': len(onArray2), 'sumOffB': sumOff2,
                    'numOffB': len(offArray2)}
        self.badTrials.append(tempData)

    def dataRec(self, onArray, offArray, trial, type, onArray2, offArray2, stimName=''):
        """
        Records the data for a trial that ended normally.

        :param onArray: Gaze-on events for coder 1
        :type onArray: list of dicts {trial, trialType, startTime, endTime, duration}
        :param offArray: Gaze-off events for coder 1
        :type offArray: list of dicts {trial, trialType, startTime, endTime, duration}
        :param trial: trial number
        :type trial: int
        :param type: trial type
        :type type: string
        :param onArray2: Gaze-on events for (optional) coder 2
        :type onArray2: list
        :param offArray2: Gaze-off events for (optional) coder 2
        :type offArray2: list
        :param stimName: If presenting stimuli, name of the stim file
        :type stimName: string
        :return:
        :rtype:
        """
        sumOn = 0
        sumOff = 0
        # loop through each array adding up gaze duration (on and off).
        for i in range(0, len(onArray)):
            sumOn = sumOn + onArray[i]['duration']
        for j in range(0, len(offArray)):
            sumOff = sumOff + offArray[j]['duration']
        sumOn2 = 0
        sumOff2 = 0
        if len(offArray2) > 0 or len(onArray2) > 0:
            for i in range(0, len(onArray2)):
                sumOn2 = sumOn2 + onArray2[i]['duration']
            for j in range(0, len(offArray2)):
                sumOff2 = sumOff2 + offArray2[j]['duration']
            self.verbDatList['verboseOn2'].extend(onArray2)
            self.verbDatList['verboseOff2'].extend(offArray2)
        # add to verbose master gaze array
        self.verbDatList['verboseOn'].extend(onArray)
        self.verbDatList['verboseOff'].extend(offArray)
        tempData = {'sNum': self.sNum, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex, 'cond': self.cond,
                    'condLabel': self.condLabel, 'trial': trial, 'GNG': 1, 'trialType': type, 'stimName': stimName,
                    'habCrit': self.habCrit, 'sumOnA': sumOn, 'numOnA': len(onArray), 'sumOffA': sumOff,
                    'numOffA': len(offArray), 'sumOnB': sumOn2, 'numOnB': len(onArray2), 'sumOffB': sumOff2,
                    'numOffB': len(offArray2)}
        self.dataMatrix.append(tempData)

    def redoTrial(self, trialNum):
        """
        Allows you to redo a trial after it has ended. Similar to abort trial, but under
        the assumption that the data has already been recorded and needs to be replaced.
        Decrementing of trial numbers is handled in doExperiment when the relevant key is
        pressed.

        :param trialNum: Trial number to redo
        :type trialNum: int
        :return:
        :rtype:
        """

        newTempData = {}
        i = 0
        while i < len(self.dataMatrix):
            if self.dataMatrix[i]['trial'] == trialNum and self.dataMatrix[i]['GNG'] == 1:
                trialIndex = i
                newTempData = self.dataMatrix[i]
                break
            else:
                i += 1
        # add the new 'bad' trial to badTrials
        newTempData['GNG'] = 0
        if newTempData['trialType'] == 'Hab':
            self.habCount -= 1
        self.badTrials.append(newTempData)
        # remove it from dataMatrix
        self.dataMatrix.remove(self.dataMatrix[trialIndex])
        # basically need to read through the verbose matrices, add everything that references that trial to the 'bad'
        # verbose data matrices, and mark the relevant lines for later deletion
        for q,z in self.verbDatList.items():
            if len(z) > 0: # Avoid any blank arrays (e.g. if there is no coder 2)
                for i in range(0, len(self.verbDatList[q])):
                    if self.verbDatList[q][i]['trial'] == trialNum:
                        # Deepcopy needed to stop it from tying the badlist entries to the regular entries and removing them.
                        self.verbBadList[q].append(deepcopy(self.verbDatList[q][i]))
                        self.verbDatList[q][i]['trial'] = 99
                # Elegantly removes all tagged lines of verbose data
                self.verbDatList[q] = [vo for vo in self.verbDatList[q] if vo['trial'] != 99]



    def checkStop(self):
        """
        After a hab trial, checks the habitution criteria and returns 'true' if any of them are met.

        :return: True if hab criteria have been met, False otherwise
        :rtype:
        """

        if self.habCount == self.setCritWindow:  # time to set the hab criterion. This will be true for both dynamic and first
            sumOnTimes = 0
            # find first hab trial
            x = 0
            for j in range(0, len(self.dataMatrix)):
                if self.dataMatrix[j]['trialType'] == 'Hab':
                    x = j
                    break
            for k in range(x, len(self.dataMatrix)):
                if self.dataMatrix[k]['GNG'] == 1 and self.dataMatrix[k]['trialType'] == 'Hab':
                    # just in case there are any bad trials, we don't want to incorporate them into setting the criterion
                    # add up total looking time for first three (good) trials
                    sumOnTimes = sumOnTimes + self.dataMatrix[k]['sumOnA']
            self.habCrit = sumOnTimes / self.setCritDivisor
        elif self.setCritType == 'Peak':  # Checks if we need to update the hab criterion
            sumOnTimes = 0
            habs = [i for i, x in enumerate(self.actualTrialOrder) if x == 'Hab']  # list of all habs
            habs.sort()
            index = habs[self.habCount - self.setCritWindow] #How far back should we look?
            for n in range(index, len(self.dataMatrix)):  # now, starting with that trial, go through and add up the good trial looking times
                if self.dataMatrix[n]['GNG'] == 1 and self.dataMatrix[n]['trialType'] == 'Hab':  # only good trials!
                    sumOnTimes = sumOnTimes + self.dataMatrix[n]['sumOnA']  # add up total looking time
            sumOnTimes = sumOnTimes / self.setCritDivisor
            if sumOnTimes > self.habCrit:
                self.habCrit = sumOnTimes
        elif self.setCritType == 'Max' and self.habCount > self.setCritWindow:  # Absolute max looking time among hab trials, regardless of order.
            habOns = []
            for n in range(0, len(self.dataMatrix)):
                if self.dataMatrix[n]['GNG'] == 1 and self.dataMatrix[n]['trialType'] == 'Hab':
                    habOns.append(self.dataMatrix[n]['sumOnA'])
            habOns.sort()
            sumOnTimes = habOns[-1] + habOns[-2] + habOns[-3]
            sumOnTimes = sumOnTimes / self.setCritDivisor
            if sumOnTimes > self.habCrit:
                self.habCrit = sumOnTimes

        # Now we separate out the set and met business.
        if self.habCount == self.maxHabTrials:
            # end habituation and goto test
            if not self.stimPres:
                for i in [0, 1, 2]:
                    core.wait(.25)  # an inadvertent side effect of playing the sound is a short pause before the test trial can begin
                    self.endHabSound.play()
            return True
        elif self.habCount >= self.setCritWindow + self.metCritWindow:  # if we're far enough in that we can plausibly meet the hab criterion
            sumOnTimes = 0
            habs = [i for i, x in enumerate(self.actualTrialOrder) if x == 'Hab']  # list of all habs
            habs.sort()
            index = habs[self.habCount - self.metCritWindow]
            if (self.metCritStatic == 'Moving') or (self.habCount-self.setCritWindow) % self.metCritWindow == 0:
                for n in range(index, len(self.dataMatrix)):  # now, starting with that trial, go through and add up the good trial looking times
                    if self.dataMatrix[n]['GNG'] == 1 and self.dataMatrix[n]['trialType'] == 'Hab':  # only good trials!
                        sumOnTimes = sumOnTimes + self.dataMatrix[n]['sumOnA']  # add up total looking time
                sumOnTimes = sumOnTimes / self.metCritDivisor
                if sumOnTimes < self.habCrit:
                    # end habituation and go to test
                    if not self.stimPres:
                        for i in [0, 1, 2]:
                            core.wait(.25)  # an inadvertent side effect of playing the sound is a short pause before the test trial can begin
                            self.endHabSound.play()
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False


    def attnGetter(self, trialType):
        """
        Plays either a default attention-getter animation or a user-defined one.
        Separate settings for audio w/shape and video file attention-getters.

        :return:
        :rtype:
        """
        attnGetter = self.attnGetterList[self.playAttnGetter[trialType]]  # Reads attention-getter from list of AGs.
        if attnGetter['stimType'] is 'Audio':
            if attnGetter['shape'] is 'Rectangle':
                useShape = self.attnGetterSquare
            elif attnGetter['shape'] is 'Cross':
                useShape = self.attnGetterCross
                sizeMult = 50
            else:
                useShape = self.attnGetterStar
                sizeMult = 1
            x = 0
            useShape.ori = 0
            useShape.fillColor = attnGetter['color']
            animDur = int(60*attnGetter['file'].getDuration())
            attnGetter['file'].play()
            for i in range(0, animDur):  # Animation set to length of sound
                useShape.ori += 5  # Defines rotation speed in degrees. Arbitrary.
                x += .1
                if attnGetter['shape'] is 'Rectangle':
                    useShape.height = sin(x) * (2*animDur) # I don't know why this one works so well, but it does.
                    useShape.width = tan(.25 * x) * (2*animDur)
                else:
                    useShape.size = tan(.025 * x) * (sizeMult*self.baseSize)
                useShape.draw()
                self.win.flip()
        else:
            dMovie = attnGetter['file']
            self.frameCount = 0
            self.pauseCount = self.ISI*60 #To make it end instantly while ignoring ISI
            while self.dispMovieStim(1, dMovie) < 2:
                pass

        self.dispCoderWindow(0)
        #self.win.flip()  # clear screen (change?)

    def dispCoderWindow(self, trialType = -1):
        """
        Draws the coder window, according to trial type and blinding settings.

        :param trialType: -1 = black (betwen trials). 0 = ready state. Otherwise irrelevant.
        :type trialType: int or string
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
            elif self.keyboard[self.key.B]:
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
            elif self.keyboard[self.secondKey]:
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
        if self.blindPres < 2:
            self.trialText.draw()
            if self.blindPres < 1:
                self.readyText.draw()
        self.win2.flip()  # flips the status screen without delaying the stimulus onset.

    def dispMovieStim(self, trialType, dispMovie):
        """
        Draws movie stimuli to the stimulus display, including movie-based attention-getters.

        :param trialType: 0 for paused, otherwise a string
        :type trialType: int or str
        :param dispMovie: The moviestim3 object for the stimuli
        :type dispMovie: moviestim3 object
        :return: an int specifying whether the movie is in progress (0), paused on its last frame (1), or ending and looping (2)
        :rtype: int
        """

        if self.frameCount == 0:  # initial setup
            dispMovie.draw()
            self.frameCount += 1
            if trialType == 0:
                self.frameCount = 0  # for post-attn-getter pause
                dispMovie.pause()
            self.win.flip()
            return 0
        elif self.frameCount == 1:
            # print('playing')
            dispMovie.play()
            dispMovie.draw()
            self.frameCount += 1
            self.win.flip()
            return 0
        elif dispMovie.getCurrentFrameTime() >= dispMovie.duration - .05 and self.pauseCount < self.ISI * 60:  # pause, check for ISI.
            dispMovie.pause()
            dispMovie.draw()  # might want to have it vanish rather than leave it on the screen for the ISI, in which case comment out this line.
            self.frameCount += 1
            self.pauseCount += 1
            self.win.flip()
            return 1
        elif dispMovie.getCurrentFrameTime() >= dispMovie.duration - .05 and self.pauseCount >= self.ISI * 60:  # MovieStim's Loop functionality can't do an ISI
            # print('repeating at ' + str(dispMovie.getCurrentFrameTime()))
            self.frameCount = 0  # changed to 0 to better enable studies that want to blank between trials
            self.pauseCount = 0
            dispMovie.draw()  # Comment this out as well to blank between loops.
            self.win.flip()
            dispMovie.seek(0)
            return 2
        else:
            dispMovie.draw()
            self.frameCount += 1
            self.win.flip()
            return 0

    def dispImageStim(self, dispImage):
        """
        Very simple. Draws still-image stimuli and flips window

        :param dispImage: the visual.ImageStim object
        :type dispImage: visual.ImageStim object
        :return: constant, 1
        :rtype: int
        """
        dispImage.draw()
        self.win.flip()
        return 1  # This essentially allows it to end at any time if this is set to "movieend"

    def dispAudioStim(self, dispAudio):
        """
        For playing audio stimuli. A little more complicated than most because it needs to track whether the audio
        is playing or not. Audio plays separately from main thread.

        :param dispAudio: the stimuli as a sound.Sound object
        :type dispAudio: sound.Sound object
        :return: an int specifying whether the audio is in progress (0), we are in an ISI (1),
            or the audio is looping (2)
        :rtype: int
        """
        if self.frameCount == 0:  # We're going to use this as a mask for the status of the audio file
            dispAudio.play()
            self.frameCount = 1
            return 0
        elif self.frameCount == 1:
            if dispAudio.status not in [STARTED, PLAYING] and self.pauseCount < self.ISI * 60:
                self.pauseCount += 1
                return 1
            elif dispAudio.status not in [STARTED, PLAYING] and self.pauseCount >= self.ISI * 60:
                self.frameCount = 0
                return 2
            else:
                return 0


    def dispTrial(self, trialType, dispMovie = False): #If no stim, dispMovie defaults to false.
        """
        Draws each frame of the trial. For stimPres, returns a movie-status value for determining when the movie has
        ended

        :param trialType: Current trial type
        :type trialType: string
        :param dispMovie: A dictionary containing both the stimulus type and the object with the stimulus file(s) (if applicable)
        :type dispMovie: bool or dict
        :return: 1 or 0. 1 = end of movie for trials that end on that.
        :rtype: int
        """
        self.dispCoderWindow(trialType)
        # now for the test trial display
        if self.stimPres:
            if dispMovie['stimType'] == 'Movie':
                t = self.dispMovieStim(trialType, dispMovie['stim'])
            elif dispMovie['stimType'] == 'Image':
                t = self.dispImageStim(dispMovie['stim'])
            elif dispMovie['stimType'] == 'Audio' and trialType != 0:  # No still-frame equivalent
                t = self.dispAudioStim(dispMovie['stim'])
            elif dispMovie['stimType'] == 'Image with audio': # Audio and image together
                if trialType != 0:  # No still-frame equivalent
                    t = self.dispAudioStim(dispMovie['stim']['Audio'])
                else:
                    t = 0
                p = self.dispImageStim(dispMovie['stim']['Image'])
            else:
                t = 0
        else:
            t = 0  # Totally irrelevant.
        return t

    def redoSetup(self, tn, autoAdv):
        """
        Lays the groundwork for redoTrial, including correcting the trial order, selecting the right stim, etc.
        :param tn: Trial number (trialNum)
        :type tn: int
        :param autoAdv: The current auto-advance trial type list (different on first trial for Reasons)
        :type autoAdv: list
        :return: list, [disMovie, trialNum], the former being the movie file to play if relevant, and the latter being the new trial number
        :rtype:
        """
        numTrialsRedo = 0
        trialNum = tn
        if trialNum > 1:  # This stops it from trying to redo a trial before the experiment begins.
            trialNum -= 1
            trialType = self.actualTrialOrder[trialNum - 1]
            numTrialsRedo += 1
            if self.stimPres:
                self.counters[trialType] -= 1
                if self.counters[trialType] < 0:
                    self.counters[trialType] = 0
            while trialType in autoAdv and trialNum > 1:  # go find the last non-AA trial and redo from there
                trialNum -= 1
                trialType = self.actualTrialOrder[trialNum - 1]
                numTrialsRedo += 1
                if self.stimPres:
                    self.counters[trialType] -= 1
                    if self.counters[trialType] < 0:  # b/c counters operates over something that is like actualTrialOrder, it should never go beneath 0
                        self.counters[trialType] = 0
            if self.stimPres:
                if self.counters[trialType] >= len(self.stimNames[trialType]):  # Comes up with multiple repetitions of few movies
                    self.stimName = self.stimNames[trialType][self.counters[trialType] % len(self.stimNames[trialType])]
                else:
                    self.stimName = self.stimNames[trialType][self.counters[trialType]]
                disMovie = self.stimDict[trialType][self.counters[trialType]]
                self.counters[trialType] += 1
                if self.counters[trialType] >= len(self.stimDict[trialType]):
                    self.counters[trialType] = 0
            else:
                disMovie = 0
            self.trialText.text = "Trial no. " + str(trialNum)
            if self.blindPres < 1:
                self.rdyTextAppend = " NEXT: " + trialType + " TRIAL"
        for i in range(trialNum, trialNum + numTrialsRedo):  # Should now rewind all the way to the last non-AA trial.
            self.redoTrial(i)
        return [disMovie, trialNum]

    def jumpToTest(self, tn):
        """
        Jumps out of a hab block into whatever the first trial is that is not a hab trial or in a hab meta-trial-type
        :param tn: trial number
        :type tn: int
        :return: [disMovie, trialType] as insertHab, the former being the movie file to play if relevant, and the latter being the new trial type
        :rtype: list
        """
        trialNum = tn
        if len(self.habTrialList) > 0:
            types = self.habTrialList
        else:
            types = ['Hab']
        habs = [i for i, x in enumerate(self.actualTrialOrder) if x in types] #Find last hab trial or meta-trial
        tempNum = max(habs)
        # trialNum is in fact the index after the current trial at this point
        # so we can just erase everything between that and the first non-hab trial.
        del self.actualTrialOrder[(trialNum - 1):(tempNum + 1)]
        trialType = self.actualTrialOrder[trialNum - 1]
        if self.stimPres:
            if self.counters[trialType] >= len(self.stimNames[trialType]):  # Comes up with multiple repetitions of few movies
                self.stimName = self.stimNames[trialType][self.counters[trialType] % len(self.stimNames[trialType])]
            else:
                self.stimName = self.stimNames[trialType][self.counters[trialType]]
            disMovie = self.stimDict[trialType][self.counters[trialType]]
            self.counters[trialType] += 1
            if self.counters[trialType] >= len(self.stimDict[trialType]):
                self.counters[trialType] = 0
        else:
            disMovie = 0
        if self.blindPres < 1:
            self.rdyTextAppend = " NEXT: " + trialType + " TRIAL"
        return [disMovie, trialType]

    def insertHab(self,tn):
        """
        Literally insert a new hab trial or meta-trial into actualTrialOrder, get the right movie, etc.

        :param tn: trialNum
        :type tn: int
        :return: [disMovie, trialType], the former being the movie file to play if relevant, and the latter being the new trial type
        :rtype: list
        """
        trialNum = tn
        if len(self.habTrialList) > 0:
            for z in range(0, len(self.habTrialList)):
                self.actualTrialOrder.insert(trialNum - 1 + z, self.habTrialList[z])
        else:
            self.actualTrialOrder.insert(trialNum - 1, 'Hab')
        trialType = self.actualTrialOrder[trialNum - 1]
        if self.stimPres: #This will get screwy with habs that have multiple movies associated with them. Redo is the option for going back one...
            if self.counters[trialType] >= len(self.stimNames[trialType]):  # Comes up with multiple repetitions of few movies
                self.stimName = self.stimNames[trialType][self.counters[trialType] % len(self.stimNames[trialType])]
            else:
                self.stimName = self.stimNames[trialType][self.counters[trialType]]
            # Insert movies into stimDict! This is difficult.
            # Stimdict is basically actualTrialOrder, but each index is a dict, {'stimType': , 'stimObject'}
            if len(self.habTrialList) > 0:
                for z in range(0, len(self.habTrialList)):
                    #Figure out what the next counter would be for each thing.
                    tempStim = self.stimList[self.stimNames[self.habTrialList[z]][self.counters[self.habTrialList[z]] % len(self.stimNames[self.habTrialList[z]])]]
                    if tempStim['stimType'] == 'Movie':
                        tempStimObj = visual.MovieStim3(self.win, tempStim['stimLoc'],
                                                        size=[self.movieWidth, self.movieHeight], flipHoriz=False,
                                                        flipVert=False, loop=False)
                    elif tempStim['stimType'] == 'Image':
                        tempStimObj = visual.ImageStim(self.win, tempStim['stimLoc'],
                                                       size=[self.movieWidth, self.movieHeight])
                    elif tempStim['stimType'] == 'Audio':
                        tempStimObj = sound.Sound(tempStim['stimLoc'])
                    else:  # The eternal problem of audio/image pair. Just creates an object that's a dict of audio and image.
                        audioObj = sound.Sound(tempStim['audioLoc'])
                        imageObj = visual.ImageStim(self.win, tempStim['imageLoc'],
                                                    size=[self.movieWidth, self.movieHeight])
                        tempStimObj = {'Audio': audioObj, 'Image': imageObj}
                    tempAdd = {'stimType': tempStim['stimType'], 'stim': tempStimObj}

                    self.stimDict.insert(trialNum - 1 + z, tempAdd)
            else:
                tempStim = self.stimList[self.stimNames[trialType][self.counters[trialType] % len(self.stimNames[trialType])]]
                if tempStim['stimType'] == 'Movie':
                    tempStimObj = visual.MovieStim3(self.win, tempStim['stimLoc'],
                                                    size=[self.movieWidth, self.movieHeight], flipHoriz=False,
                                                    flipVert=False, loop=False)
                elif tempStim['stimType'] == 'Image':
                    tempStimObj = visual.ImageStim(self.win, tempStim['stimLoc'],
                                                   size=[self.movieWidth, self.movieHeight])
                elif tempStim['stimType'] == 'Audio':
                    tempStimObj = sound.Sound(tempStim['stimLoc'])
                else:  # The eternal problem of audio/image pair. Just creates an object that's a dict of audio and image.
                    audioObj = sound.Sound(tempStim['audioLoc'])
                    imageObj = visual.ImageStim(self.win, tempStim['imageLoc'],
                                                size=[self.movieWidth, self.movieHeight])
                    tempStimObj = {'Audio': audioObj, 'Image': imageObj}
                tempAdd = {'stimType': tempStim['stimType'], 'stim': tempStimObj}
                self.stimDict.insert(trialNum - 1, tempAdd)
            disMovie = self.stimDict[trialType][self.counters[trialType]]
            self.counters[trialType] += 1
            if self.counters[trialType] >= len(self.stimDict[trialType]):
                self.counters[trialType] = 0
        else:
            disMovie = 0
        if self.blindPres < 1:
            self.rdyTextAppend = " NEXT: " + trialType + " TRIAL"
        return [disMovie,trialType]

    def doExperiment(self):
        """
        The primary control function and main trial loop.

        :return:
        :rtype:
        """
        self.currTestTrial = 0
        # primary trial loop, go until end of exp.
        runExp = True
        trialNum = 1
        self.trialText.text = "Trial no. " + str(trialNum)
        self.readyText.text = "Before first trial"
        self.rdyTextAppend = ""
        trialType = self.actualTrialOrder[0]
        if self.blindPres < 1:
            self.rdyTextAppend = " NEXT: " + trialType + " TRIAL"
        didRedo = False
        self.dispCoderWindow() #Update coder window
        AA = []  # a localized autoadvance to allow for first trial
        while runExp:
            reviewed = False
            self.trialText.text = "Trial no. " + str(trialNum)
            self.statusSquareA.fillColor = 'black'
            self.statusSquareB.fillColor = 'black'
            trialType = self.actualTrialOrder[trialNum - 1]
            # select movie for trial
            if self.stimPres:
                if self.counters[trialType] >= len(self.stimNames[trialType]):  # Comes up with multiple repetitions of few movies
                    self.stimName = self.stimNames[trialType][self.counters[trialType] % len(self.stimNames[trialType])]
                else:
                    self.stimName = self.stimNames[trialType][self.counters[trialType]]
                disMovie = self.stimDict[trialType][self.counters[trialType]]
                self.counters[trialType] += 1
            else:
                disMovie = 0
            if self.blindPres < 1:
                self.rdyTextAppend = " NEXT: " + self.actualTrialOrder[trialNum - 1] + " TRIAL"
            end = False
            while not self.keyboard[self.key.A] and trialType not in AA and not end:  # wait for 'ready' key, check at frame intervals
                if self.keyboard[self.key.Y]:
                    end = True
                elif self.keyboard[self.key.R] and not didRedo:
                    [disMovie,trialNum] = self.redoSetup(trialNum, AA) #This returns a new value for DisMovie and trialNum
                    trialType = self.actualTrialOrder[trialNum - 1]
                    didRedo = True
                elif self.keyboard[self.key.J] and 'Hab' in self.actualTrialOrder[trialNum:]:  # jump to test in a hab design
                    [disMovie, trialType] = self.jumpToTest(trialNum)
                elif trialType != 'Hab' and self.keyboard[self.key.I] and 'Hab' in self.trialOrder and trialType not in self.habTrialList:  # insert additional hab trial
                    [disMovie, trialType] = self.insertHab(trialNum)

                elif trialNum > 1 and not self.stimPres and self.keyboard[self.key.P] and not reviewed:  # Print data so far, as xHab. Non-stimulus version only. Only between trials.
                    reviewed = True
                    print("hab crit, on-timeA, numOnA, offtimeA, numOffA, onTimeB, numOnB, offTimeB, numOffB")
                    print("-------------------------------------------------------------------------------------------")
                    for i in range(0, len(self.dataMatrix)):
                        dataList = [self.dataMatrix[i]['habCrit'], self.dataMatrix[i]['sumOnA'],
                                    self.dataMatrix[i]['numOnA'], self.dataMatrix[i]['sumOffA'],
                                    self.dataMatrix[i]['numOffA'], self.dataMatrix[i]['sumOnB'],
                                    self.dataMatrix[i]['numOnB'], self.dataMatrix[i]['sumOffB'],
                                    self.dataMatrix[i]['numOffB']]
                        print(dataList)
                self.readyText.text = "No trial active" + self.rdyTextAppend
                self.dispCoderWindow()
            if not end: #This if statement checks if we're trying to quit.
                self.frameCount = 0
                # framerate = win.getActualFrameRate()
                # print(framerate)               #just some debug code.
                if self.blindPres < 2:
                    self.readyText.text = "Trial active"
                if trialType not in AA: # Blank coder window if not auto-advancing
                    self.dispCoderWindow(0)
                if self.stimPres:
                    if trialType in self.playAttnGetter: #Shockingly, this will work.
                        self.attnGetter(trialType)  # plays the attention-getter
                        core.wait(.1)  # this wait is important to make the attentiongetter not look like it is turning into the stimulus
                        self.frameCount = 0
                        irrel = self.dispTrial(0, disMovie)
                        core.wait(self.freezeFrame)  # this delay ensures that the trial only starts after the images have appeared on the screen, static, for 200ms
                        waitStart = True
                    else:
                        self.frameCount = 0
                        waitStart = False
                else:
                    if trialType in self.playAttnGetter:
                        core.wait(self.attnGetterList[self.playAttnGetter[trialType]]['stimDur'] + self.freezeFrame)  # an attempt to match the delay caused by the attention-getter playing.
                        waitStart = True
                    else:
                        waitStart = False
                while waitStart and trialType not in AA and not end:  # Wait for first gaze-on
                    if self.keyboard[self.key.Y]:  # End experiment right there and then.
                        end = True
                    elif self.keyboard[self.key.A]:
                        self.dispCoderWindow(0)
                        if self.stimPres:
                            if trialType in self.playAttnGetter:
                                self.attnGetter(trialType)
                                core.wait(.1)
                            irrel = self.dispTrial(0, disMovie)
                            core.wait(self.freezeFrame)
                        else:
                            if trialType in self.playAttnGetter:
                                core.wait(self.attnGetterList[self.playAttnGetter[trialType]]['stimDur'] + self.freezeFrame)  # an attempt to match the delay caused by the attention-getter playing.
                    elif self.lookKeysPressed():
                        waitStart = False
                        self.dispCoderWindow(trialType)
                    elif self.keyboard[self.key.R] and not didRedo:  # Redo last trial, mark last trial as bad
                        [disMovie, trialNum] = self.redoSetup(trialNum, AA)  # This returns a new value for DisMovie and trialNum
                        trialType = self.actualTrialOrder[trialNum - 1]
                        didRedo = True
                    elif self.keyboard[self.key.J] and trialType == 'Hab':  # jump to test in a hab design
                        [disMovie,trialType] = self.jumpToTest(trialNum)
                    elif trialType != 'Hab' and self.keyboard[self.key.I] and 'Hab' in self.trialOrder and trialType not in self.habTrialList:  # insert additional hab trial
                        [disMovie,trialType] = self.insertHab(trialNum)
                    else:
                        self.dispCoderWindow(0)
            if not end: #If Y has not been pressed, do the trial! Otherwise, end the experiment.
                x = self.doTrial(trialNum, trialType, disMovie)  # the actual trial, returning one of four status values at the end
                AA = self.autoAdvance  # After the very first trial AA will always be whatever it was set to at the top.
            else:
                x = 2
            if x == 2:  # end experiment, either due to final trial ending or 'end experiment altogether' button.
                runExp = False
                didRedo = False
                self.endExperiment()
            elif x == 3:  # bad trial, redo!
                trialNum = trialNum
                didRedo = True
                self.win.flip() #Blank the screen.
                self.counters[trialType] -= 1
                if self.counters[trialType] < 0:
                    self.counters[trialType] = 0
            elif x == 1:  # end hab block!
                if len(self.habTrialList) > 0: # Now accounts for meta-trials in which hab is not the last one.
                    habs = [i for i, z in enumerate(self.actualTrialOrder) if z in self.habTrialList]
                else:
                    habs = [i for i, z in enumerate(self.actualTrialOrder) if z == 'Hab']
                tempNum = max(habs)
                # trialNum is in fact the index after the current trial at this point
                # so we can just erase everything between that and the first non-hab trial.
                del self.actualTrialOrder[trialNum:tempNum + 1]  # oddly, the del function does not erase the final index.
                trialNum += 1
                trialType = self.actualTrialOrder[trialNum - 1]
                if self.blindPres == 0:
                    self.rdyTextAppend = " NEXT: " + trialType + " TRIAL"
                didRedo = False
            elif x == 0:  # continue hab/proceed as normal
                trialNum += 1
                trialType = self.actualTrialOrder[trialNum - 1]
                if not self.blindPres:
                    self.rdyTextAppend = " NEXT: " + trialType + " TRIAL"
                didRedo = False

    def lookKeysPressed(self):
        """
        A simple boolean function to allow for more modularity with preferential looking
        Basically, allows you to set an arbitrary set of keys to start a trial once the attngetter has played.
        In this case, only B (coder A on) is sufficient.

        :return: True if the B key is pressed, False otherwise.
        :rtype:
        """
        if self.keyboard[self.key.B]:
            return True
        else:
            return False

    def doTrial(self, number, type, disMovie):
        """
        Control function for individual trials, to be called by doExperiment
        Returns a status value (int) that tells doExperiment what to do next

        :param number: Trial number
        :type number: int
        :param type: Trial type
        :type type: string
        :param disMovie: Movie object for stimulus presentation
        :type disMovie: movieStim3 object
        :return: int, 0 = proceed to next trial, 1 = hab crit met, 2 = end experiment, 3 = trial aborted
        :rtype:
        """
        self.trialText.text = "Trial no. " + str(number)
        if type == 'Hab':
            self.habCount += 1
        self.frameCount = 0  # reset display
        self.pauseCount = 0  # needed for ISI
        # returns 0 if do next trial, 1 if end hab, 2 if end experiment, 3 if abort/redo
        if self.stimPres and disMovie['stimType'] == 'Movie':
            disMovie['stim'].seek(0)
        startTrial = core.getTime()
        startTrial2 = core.getTime()
        onArray = []
        offArray = []
        onArray2 = []
        offArray2 = []
        numOn = 0
        numOff = 0
        sumOn = 0
        sumOn2 = 0
        numOff2 = 0
        numOn2 = 0
        redo = False
        runTrial = True
        endFlag = False
        self.readyText.text = "Trial running"
        if self.keyboard[self.key.B]:
            gazeOn = True
            startOn = 0  # we want these to be 0 because every other time is put in reference to the startTrial timestamp so it's not some absurd number
            numOn = 1
        else:
            gazeOn = False
            numOff = 1
            startOff = 0
        if self.keyboard[self.secondKey]:
            gazeOn2 = True
            startOn2 = 0
            numOn2 = 1
        else:
            gazeOn2 = False
            numOff2 = 1
            startOff2 = 0
        while runTrial:  # runTrial is the key boolean that actually ends the trial. Need an 'end flag' to work with.
            if self.keyboard[self.key.R]:  # 'abort trial' is pressed
                redo = True
                runTrial = False
                endTrial = core.getTime() - startTrial
                # determine if they were looking or not at end of trial and update appropriate array
                if gazeOn:
                    onDur = endTrial - startOn
                    # Current format: Trial number, type, start of event, end of event, duration of event.
                    tempGazeArray = {'trial':number, 'trialType':type, 'startTime':startOn, 'endTime':endTrial, 'duration':onDur}
                    onArray.append(tempGazeArray)
                else:
                    offDur = endTrial - startOff
                    tempGazeArray = {'trial':number, 'trialType':type, 'startTime':startOff, 'endTime':endTrial, 'duration':offDur}
                    offArray.append(tempGazeArray)
            elif self.keyboard[self.key.Y]:  # the 'end the study' button, for fuss-outs
                runTrial = False
                endTrial = core.getTime() - startTrial
                # determine if they were looking or not at end of trial and update appropriate array
                if gazeOn:
                    onDur = endTrial - startOn
                    tempGazeArray = {'trial':number, 'trialType':type, 'startTime':startOn, 'endTime':endTrial, 'duration':onDur}
                    onArray.append(tempGazeArray)
                else:
                    offDur = endTrial - startOff
                    tempGazeArray = {'trial':number, 'trialType':type, 'startTime':startOff, 'endTime':endTrial, 'duration':offDur}
                    offArray.append(tempGazeArray)
                if len(onArray) == 0:
                    onArray.append({'trial':0, 'trialType':0, 'startTime':0, 'endTime':0, 'duration':0})
                if len(offArray) == 0:
                    offArray.append({'trial':0, 'trialType':0, 'startTime':0, 'endTime':0, 'duration':0})  # keeps it from crashing while trying to write data.
                type = 4  # to force an immediate quit.
            # Now for the non-abort states.
            elif core.getTime() - startTrial >= self.maxDur[type] and not endFlag:  # reached max trial duration
                if type in self.movieEnd:
                    endFlag = True
                else:
                    runTrial = False
                    endTrial = core.getTime() - startTrial
                    if not self.stimPres:
                        self.endTrialSound.play()
                    # determine if they were looking or not at end of trial and update appropriate array
                    if gazeOn:
                        onDur = endTrial - startOn
                        tempGazeArray = {'trial':number, 'trialType':type, 'startTime':startOn, 'endTime':endTrial, 'duration':onDur}
                        onArray.append(tempGazeArray)
                    else:
                        offDur = endTrial - startOff
                        tempGazeArray = {'trial':number, 'trialType':type, 'startTime':startOff, 'endTime':endTrial, 'duration':offDur}
                        offArray.append(tempGazeArray)
            elif not gazeOn:  # if they are not looking as of the previous refresh, check if they have been looking away for too long
                nowOff = core.getTime() - startTrial
                if sumOn > self.minOn[type] and nowOff - startOff >= self.maxOff[type] and self.playThrough[type] == 0 and not endFlag:
                    # if they have previously looked for at least .5s and now looked away for 2 continuous sec
                    if type in self.movieEnd:
                        endFlag = True
                    else:
                        runTrial = False
                        endTrial = core.getTime() - startTrial
                        if not self.stimPres:
                            self.endTrialSound.play()
                        endOff = nowOff
                        offDur = nowOff - startOff
                        tempGazeArray = {'trial':number, 'trialType':type, 'startTime':startOff, 'endTime':endOff, 'duration':offDur}
                        offArray.append(tempGazeArray)
                elif self.keyboard[self.key.B]:  # if they have started looking since the last refresh and not met criterion
                    gazeOn = True
                    numOn = numOn + 1
                    startOn = core.getTime() - startTrial
                    endOff = core.getTime() - startTrial
                    # by definition, if this is tripped there will be a preceding 'off' section if this is tripped because gazeOn is set at start
                    offDur = endOff - startOff
                    tempGazeArray = {'trial':number, 'trialType':type, 'startTime':startOff, 'endTime':endOff, 'duration':offDur}
                    offArray.append(tempGazeArray)
            elif gazeOn:
                nowOn = core.getTime() - startTrial
                if self.playThrough[type] == 1 and sumOn + (nowOn - startOn) >= self.minOn[type] and not endFlag:  # For trial types where the only crit is min-on.
                    if type in self.movieEnd:
                        endFlag = True
                    else:
                        runTrial = False
                        endTrial = core.getTime() - startTrial
                        if not self.stimPres:
                            self.endTrialSound.play()
                        endOn = core.getTime() - startTrial
                        onDur = endOn - startOn
                        tempGazeArray = {'trial':number, 'trialType':type, 'startTime':startOn, 'endTime':endOn, 'duration':onDur}
                        onArray.append(tempGazeArray)
                if gazeOn and not self.keyboard[self.key.B]:  # if they were looking and have looked away.
                    gazeOn = False
                    endOn = core.getTime() - startTrial
                    onDur = endOn - startOn
                    numOff = numOff + 1
                    startOff = core.getTime() - startTrial
                    tempGazeArray = {'trial':number, 'trialType':type, 'startTime':startOn, 'endTime':endOn, 'duration':onDur}
                    onArray.append(tempGazeArray)
                    sumOn = sumOn + onDur
            if not gazeOn2:  # if they are not looking as of the previous refresh
                nowOff2 = core.getTime() - startTrial2
                if self.keyboard[self.secondKey]:  # if they have started looking since the last refresh and not met criterion
                    gazeOn2 = True
                    numOn2 = numOn2 + 1
                    startOn2 = core.getTime() - startTrial2
                    endOff2 = core.getTime() - startTrial2
                    offDur2 = endOff2 - startOff2
                    tempGazeArray2 = {'trial':number, 'trialType':type, 'startTime':startOff2, 'endTime':endOff2, 'duration':offDur2}
                    offArray2.append(tempGazeArray2)
            elif gazeOn2 and not self.keyboard[self.secondKey]:  # if they were looking and have looked away.
                gazeOn2 = False
                endOn2 = core.getTime() - startTrial2
                onDur2 = endOn2 - startOn2
                numOff2 = numOff2 + 1
                startOff2 = core.getTime() - startTrial2
                tempGazeArray2 = {'trial':number, 'trialType':type, 'startTime':startOn2, 'endTime':endOn2, 'duration':onDur2}
                onArray2.append(tempGazeArray2)
                sumOn2 = sumOn2 + onDur2
            movieStatus = self.dispTrial(type, disMovie)
            if type in self.movieEnd and endFlag and movieStatus >= 1:
                runTrial = False
                endTrial = core.getTime() - startTrial
                if gazeOn:
                    onDur = endTrial - startOn
                    tempGazeArray = {'trial':number, 'trialType':type, 'startTime':startOn, 'endTime':endTrial, 'duration':onDur}
                    onArray.append(tempGazeArray)
                else:
                    offDur = endTrial - startOff
                    tempGazeArray = {'trial':number, 'trialType':type, 'startTime':startOff, 'endTime':endTrial, 'duration':offDur}
                    offArray.append(tempGazeArray)
        if gazeOn2:
            onDur2 = endTrial - startOn2
            tempGazeArray2 = {'trial':number, 'trialType':type, 'startTime':startOn2, 'endTime':endTrial, 'duration':onDur2}
            onArray2.append(tempGazeArray2)
        else:
            offDur2 = endTrial - startOff2
            tempGazeArray2 = {'trial':number, 'trialType':type, 'startTime':startOff2, 'endTime':endTrial, 'duration':offDur2}
            offArray2.append(tempGazeArray2)
        # print offArray
        # print onArray2
        # print offArray2
        if self.stimPres:
            # Reset everything, stop playing sounds and movies.
            if disMovie['stimType'] == 'Movie':
                disMovie['stim'].seek(0)  # this is the reset, we hope.
                disMovie['stim'].pause()
            elif disMovie['stimType'] == 'Audio':
                disMovie['stim'].stop()
            elif disMovie['stimType'] == 'Image with audio':
                disMovie['stim']['Audio'].stop()
        if self.stimPres and number < len(self.actualTrialOrder):
            if self.actualTrialOrder[number] not in self.autoAdvance:
                self.win.flip()  # blanks the screen outright between trials if NOT auto-advancing into the next trial
        if redo:  # if the abort button was pressed
            self.abortTrial(onArray, offArray, number, type, onArray2, offArray2, self.stimName)
            return 3
        else:
            self.dataRec(onArray, offArray, number, type, onArray2, offArray2, self.stimName)

        if type == 'Hab':  # if still during habituation
            # Check if criteria need to be set or have been met
            if self.checkStop(): # If criteria met
                return 1
            else:
                return 0
        elif number >= len(self.actualTrialOrder) or type == 4:
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
        # sort the data matrices and shuffle them together.
        if len(self.badTrials) > 0:  # if there are any redos, they need to be shuffled in appropriately.
            for i in range(0, len(self.badTrials)):
                x = 0
                while self.dataMatrix[x]['trial'] != self.badTrials[i]['trial']:
                    x += 1
                while self.dataMatrix[x]['GNG'] == 0:  # this is to get around the possibility that the same trial had multiple 'false starts'
                    x += 1
                self.dataMatrix.insert(x, self.badTrials[i])  # python makes this stupid easy
        n = '' # This infrastructure eliminates the risk of overwriting existing data
        o = 1
        filename = self.dataFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + n +'_' + str(self.today.month) + str(
                self.today.day) + str(self.today.year) + '.csv'
        while os.path.exists(filename):
            o += 1
            n = str(o)
            filename = self.dataFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + n + '_' + str(
                self.today.month) + str(
                self.today.day) + str(self.today.year) + '.csv'
        outputWriter = csv.DictWriter(open(filename, 'w'), fieldnames=self.dataColumns,
                                      extrasaction='ignore', lineterminator='\n')  # careful! this OVERWRITES the existing file. Fills from snum.
        outputWriter.writeheader()
        for r in range(0, len(self.dataMatrix)):
            # print('writing rows')
            outputWriter.writerow(self.dataMatrix[r])
        #Verbose data saving.
        verboseMatrix = []
        # first, verbose data is not as well organized. However, we should be able to alternate back and forth between
        # on and off until we reach the end of a given trial, to reconstruct it.
        # at the start of each line, add information: sNum, ageMo, ageDay, sex, cond, GNG, ON/OFF
        for n in range(0, len(self.verbDatList['verboseOn'])):
            self.verbDatList['verboseOn'][n].update({'snum':self.sNum, 'months':self.ageMo, 'days':self.ageDay, 'sex':self.sex,
                                      'cond':self.cond, 'GNG':1, 'gazeOnOff':1})
        for m in range(0, len(self.verbDatList['verboseOff'])):  # adding the details to the verbose array
            self.verbDatList['verboseOff'][m].update({'snum':self.sNum, 'months':self.ageMo, 'days':self.ageDay, 'sex':self.sex,
                                      'cond':self.cond, 'GNG':1, 'gazeOnOff':0})
        if len(self.badTrials) > 0:
            for o in range(0, len(self.verbBadList['verboseOn'])):
                self.verbBadList['verboseOn'][o].update({'snum':self.sNum, 'months':self.ageMo, 'days':self.ageDay, 'sex':self.sex,
                                      'cond':self.cond, 'GNG':0, 'gazeOnOff':1})
            for p in range(0, len(self.verbBadList['verboseOff'])):  # same details for the bad trials
                self.verbBadList['verboseOff'][p].update({'snum':self.sNum, 'months':self.ageMo, 'days':self.ageDay, 'sex':self.sex,
                                      'cond':self.cond, 'GNG':0, 'gazeOnOff':0})
        # read the final data matrix and go trial by trial.
        # print(verboseOn) #debug, to make sure verboseOn is being constructed correctly
        for q in range(0, len(self.dataMatrix)):
            tnum = self.dataMatrix[q]['trial']
            onIndex = -1
            offIndex = -1
            if self.dataMatrix[q]['GNG'] == 1:  # separate for good and bad trials
                for x in range(0, len(self.verbDatList['verboseOn'])):
                    if self.verbDatList['verboseOn'][x]['trial'] == tnum and onIndex == -1:  # find the right index in the verbose matrices
                        onIndex = x
                for y in range(0, len(self.verbDatList['verboseOff'])):
                    if self.verbDatList['verboseOff'][y]['trial'] == tnum and offIndex == -1:
                        offIndex = y
                trialVerbose = []
                if onIndex >= 0:
                    while onIndex < len(self.verbDatList['verboseOn']):
                        if self.verbDatList['verboseOn'][onIndex]['trial'] == tnum:
                            trialVerbose.append(self.verbDatList['verboseOn'][onIndex])
                        onIndex += 1
                if offIndex >= 0:
                    while offIndex < len(self.verbDatList['verboseOff']):
                        if self.verbDatList['verboseOff'][offIndex]['trial'] == tnum:
                            trialVerbose.append(self.verbDatList['verboseOff'][offIndex])
                        offIndex += 1
                trialVerbose2 = sorted(trialVerbose, key=lambda trialVerbose: trialVerbose['startTime'])  #Sorts by "startTime" of each gaze event
                verboseMatrix.extend(trialVerbose2)
            elif self.dataMatrix[q]['GNG'] == 0:  # bad trials.
                if q > 0 and self.dataMatrix[q - 1]['GNG'] == 0:
                    pass  # stops it from doubling up. If there is more than one consecutive bad trial, it will get all of them in a row the first time,
                else:
                    trialVerbose = []
                    for x in range(0, len(self.verbBadList['verboseOn'])):
                        if self.verbBadList['verboseOn'][x]['trial'] == tnum and onIndex == -1:
                            onIndex = x
                    for y in range(0, len(self.verbBadList['verboseOff'])):
                        if self.verbBadList['verboseOff'][y]['trial'] == tnum and offIndex == -1:
                            offIndex = y
                    if onIndex >= 0:
                        while onIndex < len(self.verbBadList['verboseOn']):
                            if self.verbBadList['verboseOn'][onIndex]['trial'] == tnum:
                                trialVerbose.append(self.verbBadList['verboseOn'][onIndex])
                            onIndex += 1
                    if offIndex >= 0:
                        while offIndex < len(self.verbBadList['verboseOff']):
                            if self.verbBadList['verboseOff'][offIndex]['trial'] == tnum:
                                trialVerbose.append(self.verbBadList['verboseOff'][offIndex])
                            offIndex += 1
                    trialVerbose2 = sorted(trialVerbose, key=lambda trialVerbose: trialVerbose['startTime'])  # this is the magic bullet, in theory.
                    verboseMatrix.extend(trialVerbose2)
        headers2 = ['snum', 'months', 'days', 'sex', 'cond', 'GNG', 'gazeOnOff', 'trial', 'trialType', 'startTime', 'endTime', 'duration']
        outputWriter2 = csv.DictWriter(open(
            self.dataFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + n + '_' + str(self.today.month) + str(self.today.day) + str(self.today.year) + '_VERBOSE.csv', 'w'),
                                   fieldnames=headers2, extrasaction='ignore', lineterminator='\n')  # careful! this OVERWRITES the existing file. Fills from snum.
        outputWriter2.writeheader()
        for z in range(0, len(verboseMatrix)):
            outputWriter2.writerow(verboseMatrix[z])
        if len(self.verbDatList['verboseOn2']) > 0: # If there is even a single gaze-on event from coder B, save coder B data.
            verboseMatrix2 = []
            for n in range(0, len(self.verbDatList['verboseOn2'])):
                self.verbDatList['verboseOn2'][n].update({'snum':self.sNum, 'months':self.ageMo, 'days':self.ageDay, 'sex':self.sex,
                                      'cond':self.cond, 'GNG':1, 'gazeOnOff':1})
            for m in range(0, len(self.verbDatList['verboseOff2'])):
                self.verbDatList['verboseOff2'][m].update({'snum':self.sNum, 'months':self.ageMo, 'days':self.ageDay, 'sex':self.sex,
                                      'cond':self.cond, 'GNG':1, 'gazeOnOff':0})
            if len(self.badTrials) > 0:
                for o in range(0, len(self.verbBadList['verboseOn2'])):
                    self.verbBadList['verboseOn2'][o].update({'snum':self.sNum, 'months':self.ageMo, 'days':self.ageDay, 'sex':self.sex,
                                      'cond':self.cond, 'GNG':0, 'gazeOnOff':1})
                for p in range(0, len(self.verbBadList['verboseOff2'])):
                    self.verbBadList['verboseOff2'][p].update({'snum':self.sNum, 'months':self.ageMo, 'days':self.ageDay, 'sex':self.sex,
                                      'cond':self.cond, 'GNG':0, 'gazeOnOff':0})
            for q in range(0, len(self.dataMatrix)):
                tnum = self.dataMatrix[q]['trial']
                onIndex2 = -1
                offIndex2 = -1
                if self.dataMatrix[q]['GNG'] == 1:  # separate for good and bad trials
                    for x in range(0, len(self.verbDatList['verboseOn2'])):
                        if self.verbDatList['verboseOn2'][x]['trial'] == tnum and onIndex2 == -1:  # find the right index in the verbose matrices
                            onIndex2 = x
                    for y in range(0, len(self.verbDatList['verboseOff2'])):
                        if self.verbDatList['verboseOff2'][y]['trial'] == tnum and offIndex2 == -1:
                            offIndex2 = y
                    trialVerbose = []
                    if onIndex2 >= 0:
                        while onIndex2 < len(self.verbDatList['verboseOn2']):
                            if self.verbDatList['verboseOn2'][onIndex2]['trial'] == tnum:
                                trialVerbose.append(self.verbDatList['verboseOn2'][onIndex2])
                            onIndex2 += 1
                    if offIndex2 >= 0:
                        while offIndex2 < len(self.verbDatList['verboseOff2']):
                            if self.verbDatList['verboseOff2'][offIndex2]['trial'] == tnum:
                                trialVerbose.append(self.verbDatList['verboseOff2'][offIndex2])
                            offIndex2 += 1
                    trialVerbose2 = sorted(trialVerbose, key=lambda trialVerbose: trialVerbose['startTime'])
                    verboseMatrix2.extend(trialVerbose2)
                elif self.dataMatrix[q]['GNG'] == 0:  # bad trials. These arrays will be much less predictable, so putting them together is inherently more challenging
                    if q > 0 and self.dataMatrix[q - 1]['GNG'] == 0:
                        pass  # stops it from doubling up. If there is more than one consecutive bad trial, it will get all of them in a row the first time,
                    else:
                        for x in range(0, len(self.verbBadList['verboseOn2'])):
                            if self.verbBadList['verboseOn2'][x]['trial'] == tnum and onIndex2 == -1:
                                onIndex2 = x
                        for y in range(0, len(self.verbBadList['verboseOff2'])):
                            if self.verbBadList['verboseOff2'][y]['trial'] == tnum and offIndex2 == -1:
                                offIndex2 = y
                        trialVerbose = []
                        if onIndex2 >= 0:
                            while onIndex2 < len(self.verbBadList['verboseOn2']):
                                if self.verbBadList['verboseOn2'][onIndex2]['trial'] == tnum:
                                    trialVerbose.append(self.verbBadList['verboseOn2'][onIndex2])
                                onIndex2 += 1
                        if offIndex2 >= 0:
                            while offIndex2 < len(self.verbBadList['verboseOff2']):
                                if self.verbBadList['verboseOff2'][offIndex2]['trial'] == tnum:
                                    trialVerbose.append(self.verbBadList['verboseOff2'][offIndex2])
                                offIndex2 += 1
                        trialVerbose2 = sorted(trialVerbose, key=lambda trialVerbose: trialVerbose['startTime'])
                        verboseMatrix2.extend(trialVerbose2)
            outputWriter3 = csv.DictWriter(open(
                self.dataFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + n + '_' + str(self.today.month) + str(self.today.day) + str(self.today.year) + '_VERBOSEb.csv', 'w'),
                                    fieldnames=headers2, extrasaction='ignore', lineterminator='\n')
            outputWriter3.writeheader()
            for k in range(0, len(verboseMatrix2)):
                outputWriter3.writerow(verboseMatrix2[k])
            rel = self.reliability(verboseMatrix, verboseMatrix2)
            headers3 = ['WeightedPercentageAgreement', 'CohensKappa', 'AverageObserverAgreement', 'PearsonsR']
            outputWriter4 = csv.DictWriter(open(
                self.dataFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + n + '_' + str(self.today.month) + str(self.today.day) + str(self.today.year) + '_Stats.csv', 'w'),
                                      fieldnames=headers3, extrasaction='ignore', lineterminator='\n')
            outputWriter4.writeheader()
            outputWriter4.writerow(rel)
        core.wait(.3)
        self.win2.close()
        if self.stimPres:
            self.win.close()

    def wPA(self, timewarp, timewarp2):
        """
        Calculates weighted percentage agreement, computed as number of agreement frames over total frames.

        :param timewarp: List of every individual frame's gaze-on/gaze-off code for coder A
        :type timewarp: list
        :param timewarp2: As above for coder B
        :type timewarp2: list
        :return: Weighted Percentage Agreement
        :rtype: float
        """
        a = 0
        d = 0
        for (i, j) in zip(timewarp, timewarp2):
            if i[0] == j[0]:
                if i[1] == j[1]:
                    a += 1
                else:
                    d += 1
            else:
                d += 1
        wpagreement = float(a) / float(a + d)
        return wpagreement

    def pearsonR(self, verboseMatrix, verboseMatrix2):
        """
        Computes Pearson's R

        :param verboseMatrix: Verbose data, coder A
        :type verboseMatrix: dict
        :param verboseMatrix2: Verboase data, coder B
        :type verboseMatrix2: dict
        :return: Pearson's R
        :rtype: float
        """
        trialA = []
        trialB = []
        avA = 0
        avB = 0
        # loop to construct trial array, zeroed out.
        for k in range(0, verboseMatrix[-1]['trial']):
            trialA.append(0)
            trialB.append(0)
        # separate loops for computing total on time per trial for each coder, must be done separately from verbose data files
        # b/c no longer access to summary data
        for i in verboseMatrix:
            if i['GNG'] != 0:  # Good trials only
                if i['gazeOnOff'] != 0:  # We only care about total on-time.
                    tn = i['trial'] - 1
                    trialA[tn] += i['duration']  # add the looking time to the appropriate trial index.
        for i in verboseMatrix2:
            if i['GNG'] != 0:  # Good trials only
                if i['gazeOnOff'] != 0:  # We only care about total on-time.
                    tn = i['trial'] - 1
                    trialB[tn] += i['duration']  # add the looking time to the appropriate trial index.
        for j in range(0, len(trialA)):
            avA += trialA[j]
            avB += trialB[j]
        avA = avA / verboseMatrix[-1]['trial']  # final trial number.
        avB = avB / verboseMatrix2[-1]['trial']  # in point of fact should be the same last trial # but eh.
        xy = []
        for i in range(0, len(trialA)):
            trialA[i] -= avA
            trialB[i] -= avB
            xy.append(trialA[i] * trialB[i])
        for i in range(0, len(trialA)):  # square the deviation arrays
            trialA[i] = trialA[i] ** 2
            trialB[i] = trialB[i] ** 2
        r = float(sum(xy) / sqrt(sum(trialA) * sum(trialB)))
        return r

    def cohensKappa(self, timewarp, timewarp2):
        """
        Computes Cohen's Kappa

        :param timewarp: List of every individual frame's gaze-on/gaze-off code for coder A
        :type timewarp: list
        :param timewarp2: As above for coder B
        :type timewarp2: list
        :return: Kappa
        :rtype: float
        """
        wpa = self.wPA(timewarp, timewarp2)
        coderBon = 0
        coderAon = 0
        for i in range(0, len(timewarp)):  # are the 2 timewarps equal? - when can one be bigger?
            if timewarp[i][1] == 1:
                coderAon += 1
            if timewarp2[i][1] == 1:
                coderBon += 1
        pe = (float(coderAon) / len(timewarp)) * (float(coderBon) / len(timewarp2)) + (
                    float(len(timewarp) - coderAon) / len(timewarp)) * (
                         float(len(timewarp2) - coderBon) / len(timewarp2))
        k = float(wpa - pe) / float(1 - pe)
        return k

    def avgObsAgree(self, timewarp, timewarp2):
        """
        Computes average observer agreement as agreement in each trial, divided by number of trials.

        :param timewarp: List of every individual frame's gaze-on/gaze-off code for coder A
        :type timewarp: list
        :param timewarp2: As above for coder B
        :type timewarp2: list
        :return: average observer agreement or N/A if no valid data
        :rtype: float
        """

        finalTrial = timewarp[-1][0]  # 0 is trial number.

        tg = 0
        if finalTrial > 0:  # if there are NO good trials, well it's probably crashed already, but JIC
            for i in range(0, finalTrial):  # need contingency if last trial is bad trial?
                a = 0
                d = 0
                for (m, l) in zip(timewarp, timewarp2):
                    if m[0] == i + 1 and l[0] == i + 1:
                        if m[1] == l[1]:
                            a += 1
                        else:
                            d += 1
                tg = tg + float(a) / (a + d)
            aoagreement = float(tg) / finalTrial
            return aoagreement
        else:
            return 'N/A'

    def reliability(self, verboseMatrix, verboseMatrix2):
        """
        Calculates reliability statistics. Constructed originally by Florin Gheorgiu for PyHab,
        modified by Jonathan Kominsky.


        :param verboseMatrix: A 2-dimensional list with the content of the verbose data file for coder 1
        :type verboseMatrix: list
        :param verboseMatrix2: A 2-dimensional list with the content of the verbose data file for coder 2
        :type verboseMatrix2: list
        :return: A dict of four stats in float form (weighted % agreement, average observer agreement, Cohen's Kappa, and Pearson's R)
        :rtype: dict
        """

        timewarp = []  # frame by frame arrays
        timewarp2 = []

        for i in verboseMatrix:
            if i['GNG'] != 0:  # check for it not to be a bad gaze
                for k in range(0, int(round(i['duration'] * 60))):
                    timewarp.append([i['trial'], i['gazeOnOff']])  # 6 being On or Off and 7 the trial no.
        for i in verboseMatrix2:
            if i['GNG'] != 0:
                for k in range(0, int(round(i['duration'] * 60))):
                    timewarp2.append([i['trial'], i['gazeOnOff']])
        if len(timewarp) > len(timewarp2):  # making sure the frame by frame arrays are of equal length
            diff = len(timewarp) - len(timewarp2)
            for s in range(0, diff):
                timewarp2.append([verboseMatrix2[-1]['trial'], 0])
        elif len(timewarp) < len(timewarp2):
            diff = len(timewarp2) - len(timewarp)
            for s in range(0, diff):
                timewarp.append([verboseMatrix[-1]['trial'], 0])

        stats = {'WeightedPercentageAgreement': self.wPA(timewarp, timewarp2),
                 'CohensKappa': self.cohensKappa(timewarp, timewarp2),
                 'AverageObserverAgreement': self.avgObsAgree(timewarp, timewarp2),
                 'PearsonsR': self.pearsonR(verboseMatrix, verboseMatrix2)}
        return stats

    def isInt(t):
        """
        silly little function for validating a very narrow usage of "cond" field

        :return: Bool: if arbitrary argument t is an int, true.
        :rtype:
        """
        try:
            int(t)
            return True
        except ValueError:
            return False

    def run(self, testMode = []):
        """
        Startup function. Presents subject information dialog to researcher, reads and follows settings and condition
        files. Now with a testing mode to allow us to skip the dialog and ensure the actualTrialOrder structure is being
        put together properly in unit testing.

        :param testMode: Optional and primarily only used for unit testing. Will not launch the window and start the experiment. Contains all the info that would appear in the subject info dialog.
        :type testMode: list
        :return:
        :rtype:
        """
        if len(testMode) > 0: # This is for testing purposes, to make sure we can automatically test most of the features of PyHab
            import mock
            startDlg = mock.MagicMock()
            startDlg.data = testMode
            startDlg.OK = True
        else:
            startDlg = gui.Dlg(title=self.prefix + ' Experiment')
            startDlg.addText('Subject info')
            startDlg.addField('Subject Number: ')
            startDlg.addField('Subject ID: ')
            startDlg.addField('sex: ')
            startDlg.addField('DOB(month): ')
            startDlg.addField('DOB(day): ')
            startDlg.addField('DOB(year): ')
            if self.randPres and len(self.condList) > 0:
                startDlg.addField('Cond: ', choices=self.condList)
            else:
                startDlg.addField('Cond: ')
            if not self.stimPres:
                startDlg.addField('DOT(month): ')
                startDlg.addField('DOT(day): ')
                startDlg.addField('DOT(year): ')
            startDlg.show()
        if startDlg.OK:
            thisInfo = startDlg.data
            self.sNum = thisInfo[0]
            self.sID = thisInfo[1]
            self.sex = thisInfo[2]
            # now for the exciting bit: converting DOB into months/days.
            self.today = date.today()
            DOB = date(2000 + int(thisInfo[5]), int(thisInfo[3]), int(thisInfo[4]))
            if self.stimPres:
                DOT = self.today
            else:
                DOT = date(2000 + int(thisInfo[9]), int(thisInfo[7]), int(thisInfo[8]))
            # Dateutil's relativedelta is included in psychopy and just better than every other option!
            ageDif = relativedelta(DOT, DOB)
            self.ageMo = ageDif.years * 12 + ageDif.months
            self.ageDay = ageDif.days  # Impossibly simple, but it works.
            self.actualTrialOrder = []  # in this version, mostly a key for the hab trials.
            for i in range(0, len(self.trialOrder)):
                if self.trialOrder[i] == 'Hab':
                    for j in range(0, self.maxHabTrials):
                        if len(self.habTrialList) > 0:
                            for q in range(0, len(self.habTrialList)):
                                self.actualTrialOrder.append(self.habTrialList[q])
                        else:
                            self.actualTrialOrder.append('Hab')
                else:
                    self.actualTrialOrder.append(self.trialOrder[i])
            # build trial order
            if self.randPres and len(self.condList) > 0:  # Extra check: We WANT conditions and we HAVE them too.
                self.condLabel = thisInfo[6]
                testReader = csv.reader(open(self.condPath + self.condFile, 'rU'))
                testStuff = []
                for row in testReader:
                    testStuff.append(row)
                testDict = dict(testStuff)
                self.cond = testDict[self.condLabel]  # this will read as order of indeces in N groups, in a 2-dimensional array
                # type conversion required. Eval will read the string into a dictionary (now).
                self.cond = eval(self.cond)
                # now to rearrange the lists of each trial type.
                finalDict = []
                for i, j in self.cond.items():
                    newTempTrials = []
                    for q in range(0, len(j)):
                        newTempTrials.append(self.stimNames[i][j[q] - 1])
                    finalDict.append((i, newTempTrials))
                self.stimNames = dict(finalDict)
            else:
                self.cond = thisInfo[6]
                self.condLabel = self.cond
            if len(testMode) == 0: # If we're in test mode, skip setting up the window and launching the experiment.
                self.SetupWindow()

    def SetupWindow(self):
        """
        Sets up the stimulus presentation and coder windows, loads all the stimuli, then starts the experiment
        with doExperiment()

        :return:
        :rtype:
        """
        # Important to do this first because it gets the windows in the correct order for focus etc.
        if self.stimPres:
            # Stimulus presentation window
            self.win = visual.Window((self.screenWidth, self.screenHeight), fullscr=False, screen=1, allowGUI=False,
                                     units='pix', color=self.screenColor)
        # Coder window
        self.win2 = visual.Window((400, 400), fullscr=False, screen=0, allowGUI=True, units='pix', waitBlanking=False,
                                  rgb=[-1, -1, -1])
        if self.stimPres:
            tempText = visual.TextStim(self.win2, text="Loading Stimuli", pos=[0, 0], color='white', bold=True, height=40)
            tempText.draw()
            self.win2.flip()
            self.stimDict = {x: [] for x in self.stimNames.keys()}  # This holds all the loaded movies.
            self.counters = {x: 0 for x in self.stimNames.keys()}  # list of counters, one per index of the dict, so it knows which movie to play
            tempCtr = {x: 0 for x in self.stimNames.keys()}
            for i in self.actualTrialOrder:
                x = tempCtr[i] # Changed so hab trials get the same treatment as everything else.
                tempStim = self.stimList[self.stimNames[i][x]]
                if tempStim['stimType'] == 'Movie':
                    tempStimObj = visual.MovieStim3(self.win, tempStim['stimLoc'],
                                                  size=[self.movieWidth, self.movieHeight], flipHoriz=False,
                                                  flipVert=False, loop=False)
                elif tempStim['stimType'] == 'Image':
                    tempStimObj = visual.ImageStim(self.win, tempStim['stimLoc'],
                                                   size=[self.movieWidth, self.movieHeight])
                elif tempStim['stimType'] == 'Audio':
                    tempStimObj = sound.Sound(tempStim['stimLoc'])
                else: # The eternal problem of audio/image pair. Just creates an object that's a dict of audio and image.
                    audioObj = sound.Sound(tempStim['audioLoc'])
                    imageObj = visual.ImageStim(self.win, tempStim['imageLoc'],
                                                   size=[self.movieWidth, self.movieHeight])
                    tempStimObj = {'Audio': audioObj, 'Image': imageObj}
                tempAdd = {'stimType':tempStim['stimType'], 'stim':tempStimObj}
                self.stimDict[i].append(tempAdd)
                tempCtr[i] += 1
                if tempCtr[i] >= len(self.stimNames[i]):
                    tempCtr[i] = 0

            if len(list(self.playAttnGetter.keys())) > 0:
                for i in list(self.attnGetterList.keys()):
                    if self.attnGetterList[i]['stimType'] == 'Audio':
                        self.attnGetterList[i]['file'] = sound.Sound(self.attnGetterList[i]['stimLoc'])
                    else:
                        self.attnGetterList[i]['file'] = visual.MovieStim3(self.win, self.attnGetterList[i]['stimLoc'],
                                                                           size=[self.movieWidth, self.movieHeight],
                                                                           flipHoriz=False, flipVert=False, loop=False)

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
        self.trialText = visual.TextStim(self.win2, text="Trial no: ", pos=[-150, 150], color='white')
        self.readyText = visual.TextStim(self.win2, text="Trial not active", pos=[-25, 100], color='white')
        self.doExperiment()  # Get this show on the road!
