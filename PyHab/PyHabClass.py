import os, sys
from psychopy import gui, visual, event, core, data, monitors, tools, prefs, logging
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
    TODO: Block condensed save files?

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
        if 'dataFiles' in settingsDict.keys(): # TODO: MAke this work proper
            self.dataFiles = eval(settingsDict['dataFiles'])
        else:
            self.dataFiles = ['Block','Trial']
        self.prefix = settingsDict['prefix']  # prefix for data files. All data filenames will start with this text.
        self.dataFolder = settingsDict['dataloc']  # datafolder, condpath,stimPath are the ones that need modification.
        if len(self.dataFolder) > 0 and self.dataFolder[-1] is not self.dirMarker:
            self.dataFolder = [self.dirMarker if x == otherOS else x for x in self.dataFolder]
            self.dataFolder = ''.join(self.dataFolder)
        # Create verbose data sub-folder. New in 0.8.
        self.verboseFolder = self.dataFolder + 'verbose' + self.dirMarker
        if not os.path.isdir(self.verboseFolder):
            os.makedirs(self.verboseFolder)


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
        if 'calcHabOver' in settingsDict.keys():
            self.calcHabOver = eval(settingsDict['calcHabOver'])
        else:
            if len(self.habTrialList) > 0:
                if 'Hab' in self.habTrialList:
                    self.calcHabOver = ['Hab']  # Mimics old behavior
                else:
                    self.calcHabOver = [self.habTrialList[-1]]
            else:
                self.calcHabOver = []
        if 'blockList' in settingsDict.keys():
            self.blockList = eval(settingsDict['blockList'])
            self.blockDataList = eval(settingsDict['blockDataList'])
        else:
            self.blockList = {}
            self.blockDataList = []


        # STIMULUS PRESENTATION SETTINGS
        self.stimPres = eval(settingsDict['stimPres'])  # For determining if the program is for stimulus presentation (True) or if it's just coding looking times (False)
        if not self.stimPres:
            self.movieEnd = []  # So we don't run into trouble with trials not ending waiting for movies that don't exist.
        self.stimPath = settingsDict['stimPath']  # Folder where movie files can be located (if not in same folder as script)
        self.stimNames = eval(settingsDict['stimNames']) # A dict of trial types with associated lists of stimuli
        self.stimList = eval(settingsDict['stimList'])  # List of all stimuli in the experiment.
        # Go through each item in stimlist, find its stimloc parameter, and replace \\ with / or vise-versa
        for [i,j] in self.stimList.items():
            try:
                j['stimLoc'] = ''.join([self.dirMarker if x == otherOS else x for x in j['stimLoc']])
            except KeyError:  # For image/audio pairs
                j['audioLoc'] = ''.join([self.dirMarker if x == otherOS else x for x in j['audioLoc']])
                j['imageLoc'] = ''.join([self.dirMarker if x == otherOS else x for x in j['imageLoc']])

        self.screenWidth = eval(settingsDict['screenWidth'])  # Display window width, in pixels
        self.screenHeight = eval(settingsDict['screenHeight'])  # Display window height, in pixels
        self.screenColor = settingsDict['screenColor']  #Background color of stim window.
        self.movieWidth = eval(settingsDict['movieWidth'])  # movie width
        self.movieHeight = eval(settingsDict['movieHeight'])  # movie height
        self.screenIndex = eval(settingsDict['screenIndex'])  # which monitor stimuli are presented on. 1 for secondary monitor, 0 for primary monitor.
        self.ISI = eval(settingsDict['ISI'])  # time between loops (by trial type)
        # Backwards compatibility time!
        if type(self.ISI) is not dict:
            # Go through stimNames and make everything work
            tempISI = {}
            for [i,j] in self.stimNames.items():
                tempISI[i] = self.ISI
            self.ISI = tempISI
        try:
            self.expScreenIndex = eval(settingsDict['expScreenIndex'])
        except:
            if self.screenIndex == 1:
                self.expScreenIndex = 0
            else:
                self.expScreenIndex = 1

        # Secondary evals to make sure everything in the dictionaries that needs to be a number is one.
        # maxDur, maxOff, minOn, ISI
        for q in [self.maxDur, self.maxOff, self.minOn, self.ISI]:
            for [i,j] in q.items():
                if isinstance(j, str):
                    try:
                        q[i] = eval(j)
                    except:
                        errDlg = gui.Dlg(title="Settings error")
                        errDlg.addText("A setting for trial type " + i + " contains text where number expected. Please update settings in builder!")
                        errDlg.show()
                        core.quit()

        self.freezeFrame = eval(settingsDict['freezeFrame'])  # time that movie remains on first frame at start of trial.
        self.playAttnGetter = eval(settingsDict['playAttnGetter'])  # Trial-by-trial marker of which attngetter goes with which trial (if applicable).
        self.attnGetterList = eval(settingsDict['attnGetterList'])  # List of all attention-getters
        # Go through each item in attnGetterList, find its stimloc parameter, and replace \\ with / or vise-versa
        for [i,j] in self.attnGetterList.items():
            j['stimLoc'] = ''.join([self.dirMarker if x == otherOS else x for x in j['stimLoc']])
        try: # To allow for better backwards compatibility, won't crash if this was made in a version that has no startImage or endImage lines
            self.startImage = settingsDict['startImage']
            self.endImage = settingsDict['endImage']
            self.nextFlash = eval(settingsDict['nextFlash']) # 0 or 1, whether to flash when A is required for next trial.
        except:
            self.startImage = ''
            self.endImage = ''
            self.nextFlash = 0
        try:
            self.habThresh = eval(settingsDict['habThresh'])
        except:
            self.habThresh = 1.0

        if len(self.stimPath) > 0 and self.stimPath[-1] is not self.dirMarker:  # If it was made in one OS and running in another
            self.stimPath = [self.dirMarker if x == otherOS else x for x in self.stimPath]
            self.stimPath = ''.join(self.stimPath)

        '''
        END SETTINGS
        '''
        self.habCount = 0  # For hab designs, checks the # of habituation trials completed
        self.habCrit = 0  # initial setting of habcrit at 0
        self.habSetWhen = -1
        self.habMetWhen = -1  # Ported from MB4: Tracks both when the habituation criterion is set, and met.
        self.maxHabIndex = 0
        self.habDataCompiled=[0]*self.maxHabTrials  # A new easy way to track just hab trials, even with complex meta-trial structure.
        self.dataMatrix = []  # primary data array
        self.blockDataTags = {}
        for i in self.blockDataList:
            self.blockDataTags[i] = [] # Set up for run to build this list.
        # data format: snum, sID, age in months, age in days, sex, condition, trial, GNGtrial, trial type, hab crit, on-time, number of gazes, off-time, number of look-offs
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

    def abortTrial(self, onArray, offArray, trial, ttype, onArray2, offArray2, stimName = '', habTrialNo = 0):  # the 2nd arrays are if there are two coders.
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
        if habTrialNo <= 0:
            habTrialNo = ''
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
        tempData = {'sNum': self.sNum, 'sID':self.sID, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex, 'cond': self.cond,
                    'condLabel': self.condLabel,'trial': trial, 'GNG': 0, 'trialType': ttype, 'stimName': stimName,
                    'habCrit': self.habCrit, 'habTrialNo': habTrialNo, 'sumOnA': sumOn, 'numOnA': len(onArray), 'sumOffA': sumOff,
                    'numOffA': len(offArray), 'sumOnB': sumOn2, 'numOnB': len(onArray2), 'sumOffB': sumOff2,
                    'numOffB': len(offArray2)}
        self.badTrials.append(tempData)

    def dataRec(self, onArray, offArray, trial, type, onArray2, offArray2, stimName = '', habTrialNo = 0):
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
        :param habTrialNo: If part of a hab block, what hab trial it was part of.
        :type habTrialNo: int
        :return:
        :rtype:
        """
        sumOn = 0
        sumOff = 0
        if habTrialNo <= 0:
            habTrialNo = ''
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
        tempData = {'sNum': self.sNum, 'sID': self.sID, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex, 'cond': self.cond,
                    'condLabel': self.condLabel, 'trial': trial, 'GNG': 1, 'trialType': type, 'stimName': stimName,
                    'habCrit': self.habCrit, 'habTrialNo': habTrialNo, 'sumOnA': sumOn, 'numOnA': len(onArray), 'sumOffA': sumOff,
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
        if self.dataMatrix[trialIndex]['trialType'][0:4] == 'hab.':  # Redoing a habituation trial
            tempName = deepcopy(self.dataMatrix[trialIndex]['trialType'])
            while '.' in tempName:
                tempName = tempName[tempName.index('.')+1:]
            # Subtract data from self.habDataCompiled before checking whether we reduce the hab count, do make indexing
            # the correct part of habDataCompiled easier. Notably, reduces but does not inherently zero out.
            if tempName in self.calcHabOver:  # Make sure it's part of the hab calc
                self.habDataCompiled[self.habCount-1] = self.habDataCompiled[self.habCount-1] - self.dataMatrix[trialIndex]['sumOnA']
                if self.habDataCompiled[self.habCount-1] < 0:  # For rounding errors
                    self.habDataCompiled[self.habCount-1] = 0
            # If it's the end of the hab iteration, then reduce the hab count. TODO: No longer hab only?
            if '^' in self.actualTrialOrder[trialNum-1]:  # This is kind of a dangerous kludge that hopefully won't come up that often.
                self.habCount -= 1
        elif newTempData['trialType'] == 'Hab':
            self.habCount -= 1
            self.habDataCompiled[self.habCount] = 0 # Resets the appropriate instance of the hab data structure
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
        Also responsible for setting the habituation criteria according to settings.
        Prior to any criteria being set, self.HabCrit is 0, and self.habSetWhen is -1.

        Uses a sort of parallel data structure that just tracks hab-relevant gaze totals. As a bonus, this means it now
        works for both single-target and preferential looking designs with no modification.

        :return: True if hab criteria have been met, False otherwise
        :rtype:
        """



        if self.habCount == self.setCritWindow and self.setCritType != 'Threshold':  # time to set the hab criterion. This will be true for both dynamic and first
            sumOnTimes = 0
            for j in range(0,self.habCount):
                sumOnTimes = sumOnTimes + self.habDataCompiled[j]
            self.habCrit = sumOnTimes / self.setCritDivisor
            self.habSetWhen = deepcopy(self.habCount)
        elif self.setCritType == 'Peak':  # Checks if we need to update the hab criterion
            sumOnTimes = 0
            index = self.habCount - self.setCritWindow #How far back should we look?
            for n in range(index, self.habCount):  # now, starting with that trial, go through and add up the good trial looking times
                sumOnTimes = sumOnTimes + self.habDataCompiled[n]
            sumOnTimes = sumOnTimes / self.setCritDivisor
            if sumOnTimes > self.habCrit:
                self.habCrit = sumOnTimes
                self.habSetWhen = deepcopy(self.habCount)
        elif self.setCritType == 'Max' and self.habCount > self.setCritWindow:  # Absolute max looking time among hab trials, regardless of order.
            sumOnTimes = 0
            habOns = deepcopy(self.habDataCompiled)
            habOns.sort()  # Rearranges the array into lowest-highest.
            lastHabUsed = 0
            for i in range(-1*self.setCritWindow,0):
                sumOnTimes = sumOnTimes + habOns[i]
                # This convoluted mess finds the last instance of the 'max' value(s) used in the computation.
                lastHabUsed = max(lastHabUsed,len(self.habDataCompiled) - self.habDataCompiled[::-1].index(habOns[i]))
            sumOnTimes = sumOnTimes / self.setCritDivisor
            if sumOnTimes > self.habCrit:
                self.habCrit = sumOnTimes
                self.habSetWhen = lastHabUsed
        elif self.setCritType == 'Threshold' and self.habCount >= self.setCritWindow and self.habSetWhen == -1:
            sumOnTimes = 0
            index = self.habCount - self.setCritWindow  # How far back should we look?
            for j in range(index,self.habCount):
                sumOnTimes = sumOnTimes + self.habDataCompiled[j]
            if sumOnTimes > self.habThresh:
                self.habCrit = sumOnTimes / self.setCritDivisor
                self.habSetWhen = deepcopy(self.habCount)

        # Now we separate out the set and met business.
        if self.habCount == self.maxHabTrials:
            # end habituation and goto test
            if not self.stimPres:
                for i in [0, 1, 2]:
                    core.wait(.25)  # an inadvertent side effect of playing the sound is a short pause before the test trial can begin
                    self.endHabSound.play()
            self.habMetWhen = self.habCount
            return True
        elif self.habCount >= self.setCritWindow + self.metCritWindow and self.habSetWhen > -1:  # if we're far enough in that we can plausibly meet the hab criterion
            # Problem: Fixed window, peak, and max as relates to habsetwhen....
            # Fixed window is probably the only thing that should ignore habsetwhen.
            if self.habCount < self.habSetWhen + self.metCritWindow and self.metCritStatic == 'Moving': # Was the hab set "late" and are we too early as a result
                return False
            else:
                sumOnTimes = 0
                index = self.habCount - self.metCritWindow
                if (self.metCritStatic == 'Moving') or (self.habCount-self.setCritWindow) % self.metCritWindow == 0:
                    for n in range(index, self.habCount):  # now, starting with that trial, go through and add up the good trial looking times
                        sumOnTimes = sumOnTimes + self.habDataCompiled[n]
                    sumOnTimes = sumOnTimes / self.metCritDivisor
                    if sumOnTimes < self.habCrit:
                        # end habituation and go to test
                        if not self.stimPres:
                            for i in [0, 1, 2]:
                                core.wait(.25)  # TODO: an inadvertent side effect of playing the sound is a short pause before the test trial can begin
                                self.endHabSound.play()
                        self.habMetWhen = self.habCount
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
            dMovie.seek(0.0)
            self.frameCount = 0
            self.ISI['NobodyNameTheirTrialTypeThis'] = 0.0 # A goofy solution but it'll work. dispMovieStim requires a trial type, and the ISI for an attngetter needs to be 0.
            while self.dispMovieStim('NobodyNameTheirTrialTypeThis', dMovie) < 2:
                pass

        self.dispCoderWindow(0)
        #self.win.flip()  # clear screen (change?)

    def flashCoderWindow(self, rep=False):
        """
        Flash the background of the coder window to alert the experimenter they need to initiate the next trial.
        .2 seconds of white and black, flashed twice. Can lengthen gap between trial but listens for 'A' on every flip.

        :return:
        :rtype:
        """
        flashing = True

        # at 60fps, 200ms = 12 frames.
        for i in range(0,12):
            self.win2.color='white'
            self.dispCoderWindow()
            if self.keyboard[self.key.A]:
                flashing = False
                break
        if flashing:
            for i in range(0,12):
                self.win2.color='black'
                self.dispCoderWindow()
                if self.keyboard[self.key.A]:
                    flashing = False
                    break
            if flashing and not rep:
                self.flashCoderWindow(rep=True)
        self.win2.color='black'




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
            self.dummyThing.draw()
            self.frameCount += 1
            dispMovie.draw()
            if trialType == 0:
                self.frameCount = 0  # for post-attn-getter pause
                dispMovie.pause()
            else:
                dispMovie.seek(0.0) # Moved up here from below so that it CAN loop at all
            self.win.flip()
            return 0
        elif self.frameCount == 1:
            # print('playing')
            dispMovie.play()
            dispMovie.draw()
            self.frameCount += 1
            self.win.flip()
            return 0
        elif dispMovie.getCurrentFrameTime() >= dispMovie.duration - dispMovie._frameInterval*2 and self.pauseCount < self.ISI[trialType] * 60:  # pause, check for ISI.
            self.dummyThing.draw()
            dispMovie.pause()
            dispMovie.draw()  # might want to have it vanish rather than leave it on the screen for the ISI, in which case comment out this line.
            self.frameCount += 1
            self.pauseCount += 1
            self.win.flip() # TODO: Goes blank if ISI is long enough. Pyglet problem.
            return 1
        elif dispMovie.getCurrentFrameTime() >= dispMovie.duration - dispMovie._frameInterval*2 and self.pauseCount >= self.ISI[trialType] * 60:  # MovieStim's Loop functionality can't do an ISI
            self.dummyThing.draw()
            # print('repeating at ' + str(dispMovie.getCurrentFrameTime()))
            self.frameCount = 0  # changed to 0 to better enable studies that want to blank between trials
            self.pauseCount = 0
            dispMovie.draw()  # Comment this out as well to blank between loops.
            self.win.flip()
            dispMovie.pause()
            #dispMovie.seek(0.0) #This seek seems to cause the replays.
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

    def dispAudioStim(self, trialType, dispAudio):
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
            if dispAudio.status not in [STARTED, PLAYING] and self.pauseCount < self.ISI[trialType] * 60:
                self.pauseCount += 1
                return 1
            elif dispAudio.status not in [STARTED, PLAYING] and self.pauseCount >= self.ISI[trialType] * 60:
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
                t = self.dispAudioStim(trialType, dispMovie['stim'])
            elif dispMovie['stimType'] == 'Image with audio': # Audio and image together
                if trialType != 0:  # No still-frame equivalent
                    t = self.dispAudioStim(trialType,dispMovie['stim']['Audio'])
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
        tempHabCount = deepcopy(self.habCount)
        if trialNum > 1:  # This stops it from trying to redo a trial before the experiment begins.
            trialNum -= 1
            trialType = self.actualTrialOrder[trialNum - 1]
            while '.' in trialType:
                trialType = trialType[trialType.index('.')+1:]
            numTrialsRedo += 1
            if self.stimPres:
                self.counters[trialType] -= 1
                if self.counters[trialType] < 0:
                    self.counters[trialType] = 0
            while trialType in autoAdv and trialNum > 1:  # go find the last non-AA trial and redo from there
                trialNum -= 1
                trialType = self.actualTrialOrder[trialNum - 1]
                while '.' in trialType:
                    trialType = trialType[trialType.index('.') + 1:]
                numTrialsRedo += 1
                if self.stimPres:
                    self.counters[trialType] -= 1
                    if self.counters[trialType] < 0:  # b/c counters operates over something that is like actualTrialOrder, it should never go beneath 0
                        self.counters[trialType] = 0
            if self.stimPres:
                if self.counters[trialType] >= len(self.stimNames[trialType]):  # Comes up with multiple repetitions of few movies
                    self.stimName = self.stimNames[trialType][self.counters[trialType] % len(self.stimNames[trialType])]
                    disMovie = self.stimDict[trialType][self.counters[trialType] % len(self.stimNames[trialType])]
                else:
                    self.stimName = self.stimNames[trialType][self.counters[trialType]]
                    disMovie = self.stimDict[trialType][self.counters[trialType]]
                self.counters[trialType] += 1
                if self.counters[trialType] < 0:
                    self.counters[trialType] = 0
            else:
                disMovie = 0
            self.trialText.text = "Trial no. " + str(trialNum)
            if self.blindPres < 1:
                self.rdyTextAppend = " NEXT: " + self.actualTrialOrder[trialNum - 1] + " TRIAL"
        for i in range(trialNum, trialNum + numTrialsRedo):  # Should now rewind all the way to the last non-AA trial.
            self.redoTrial(i)
        if self.habCount != tempHabCount:  # Did we change a trial that can change checkStop?
            # If hab type is threshold, max, or peak, we might need to recalculate dynamically
            if self.habSetWhen >= self.habCount:
                self.habSetWhen = -1
                self.habCrit = 0
                if self.setCritType != 'First':  # If it's 'first', it'll just solve itself.
                    dummy = self.checkStop()
            # If habituation has been reached, we have to basically undo what happens when a hab crit is met.
            if self.habMetWhen > -1 and self.habCount != self.maxHabTrials - 1:  # If it was the last hab trial possible, it'll just solve itself with no further action
                if not self.checkStop():  # Almost always true in this case, because we're redoing a hab trial.
                    self.habMetWhen = -1  # Reset
                    tempTN = trialNum + max(len(self.habTrialList), 1)  # Starting with the next trial.
                    ctr = 0
                    for h in range(self.habCount+1, self.maxHabTrials):
                        [irrel, irrel2] = self.insertHab(tn=tempTN+ctr*max(len(self.habTrialList), 1), hn=h)
                        ctr += 1
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
        tempNum = self.maxHabIndex
        # It's actually necessary to decrement the counter for the current trial type to deal with jump/insert!
        currType = self.actualTrialOrder[trialNum - 1]
        while '.' in currType:  # Dealing with blocks and recursions
            currType = currType[currType.index('.') + 1:]
        self.counters[currType] -= 1
        if self.counters[currType] < 0:
            self.counters[currType] = 0
        # trialNum is in fact the index after the current trial at this point
        # so we can just erase everything between that and the first non-hab trial.
        del self.actualTrialOrder[(trialNum - 1):(tempNum + 1)]
        try:
            trialType = self.actualTrialOrder[trialNum - 1]  # Doesn't look for hab trial because...should never happen!
            if self.stimPres:
                if self.counters[trialType] >= len(self.stimNames[trialType]):  # Comes up with multiple repetitions of few movies
                    self.stimName = self.stimNames[trialType][self.counters[trialType] % len(self.stimNames[trialType])]
                    disMovie = self.stimDict[trialType][self.counters[trialType] % len(self.stimNames[trialType])]
                else:
                    self.stimName = self.stimNames[trialType][self.counters[trialType]]
                    disMovie = self.stimDict[trialType][self.counters[trialType]]
                self.counters[trialType] += 1
            else:
                disMovie = 0
            if self.blindPres < 1:
                self.rdyTextAppend = " NEXT: " + trialType + " TRIAL"
            return [disMovie, trialType]
        except IndexError:  # Comes up when there are no non-hab trials
            self.endExperiment()
            return[0,'4']

    def insertHab(self, tn, hn=-1):
        """
        Literally insert a new hab trial or meta-trial into actualTrialOrder, get the right movie, etc.

        :param tn: trial number to insert the trial
        :type tn: int
        :param hn: HabCount number to insert the hab trial. By default, whatever the current habcount is. However, there
        are edge cases when recovering from "redo" trials when we want to throw in a hab trial further down the line.
        :type hn: int
        :return: [disMovie, trialType], the former being the movie file to play if relevant, and the latter being the new trial type
        :rtype: list
        """
        trialNum = tn
        if hn == -1:
            hn = self.habCount
        habNum = hn
        if len(self.habTrialList) > 0:
            self.blockExpander(self.habTrialList, 'hab', hab=True, habNum=habNum+1, insert=trialNum-1)
            # reset self.maxHabIndex based on last instance of '^'. TODO: No longer hab only?
            for n in range(trialNum, len(self.actualTrialOrder)):
                if '^' in self.actualTrialOrder[n]:
                    self.maxHabIndex = n
        else:
            self.actualTrialOrder.insert(trialNum - 1, 'Hab')
            self.maxHabIndex = trialNum - 1
        trialType = self.actualTrialOrder[trialNum - 1]
        while '.' in trialType:
            trialType = trialType[trialType.index('.') + 1:]
        if self.stimPres and habNum == self.habCount:  # If we're inserting something way down the line, don't mess with it yet.
            if self.counters[trialType] >= len(self.stimNames[trialType]):  # Comes up with multiple repetitions of few movies
                self.stimName = self.stimNames[trialType][self.counters[trialType] % len(self.stimNames[trialType])]
            else:
                self.stimName = self.stimNames[trialType][self.counters[trialType]]

            if self.counters[trialType] >= len(self.stimNames[trialType]):  # Comes up with multiple repetitions of few movies
                self.stimName = self.stimNames[trialType][self.counters[trialType] % len(self.stimNames[trialType])]
                disMovie = self.stimDict[trialType][
                    self.counters[trialType] % len(self.stimNames[trialType])]
            else:
                self.stimName = self.stimNames[trialType][self.counters[trialType]]
                disMovie = self.stimDict[trialType][
                    self.counters[trialType]]
            self.counters[trialType] += 1
            if self.counters[trialType] < 0:
                self.counters[trialType] = 0
        else:
            disMovie = 0
        if self.blindPres < 1:  # TODO: Do we need this?
            self.rdyTextAppend = " NEXT: " + self.actualTrialOrder[trialNum - 1] + " TRIAL"
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
            if len(self.badTrials) > 0:
                badTrialTrials = [x['trial'] for x in self.badTrials]  # Gets just trial numbers
                if trialNum in badTrialTrials:
                    self.trialText.text = "Trial no. " + str(trialNum) + " (" + str(
                        badTrialTrials.count(trialNum) + 1) + "x)"
                else:
                    self.trialText.text = "Trial no. " + str(trialNum)
            else:
                self.trialText.text = "Trial no. " + str(trialNum)
            self.statusSquareA.fillColor = 'black'
            self.statusSquareB.fillColor = 'black'
            trialType = self.actualTrialOrder[trialNum - 1]
            while '.' in trialType:
                trialType = trialType[trialType.index('.')+1:]
            # select movie for trial
            if self.stimPres:
                if self.counters[trialType] >= len(self.stimNames[trialType]):  # Comes up with multiple repetitions of few movies
                    self.stimName = self.stimNames[trialType][self.counters[trialType] % len(self.stimNames[trialType])]
                    disMovie = self.stimDict[trialType][self.counters[trialType] % len(self.stimNames[trialType])]
                else:
                    self.stimName = self.stimNames[trialType][self.counters[trialType]]
                    disMovie = self.stimDict[trialType][self.counters[trialType]]
                self.counters[trialType] += 1
            else:
                disMovie = 0
            if self.blindPres < 1:
                self.rdyTextAppend = " NEXT: " + self.actualTrialOrder[trialNum - 1] + " TRIAL"
            end = False
            skip = False
            if trialType not in AA and self.nextFlash in [1,'1',True,'True']: # The 'flasher' to alert the experimenter they need to start the next trial
                self.flashCoderWindow()
            while not self.keyboard[self.key.A] and trialType not in AA and not end:  # wait for 'ready' key, check at frame intervals
                if self.keyboard[self.key.Y]:
                    end = True
                elif self.keyboard[self.key.R] and not didRedo:
                    if self.stimPres:
                        if self.counters[trialType] > 0:
                            self.counters[trialType] -= 1
                    [disMovie,trialNum] = self.redoSetup(trialNum, AA) #This returns a new value for DisMovie and trialNum
                    if self.stimPres:
                        if disMovie['stimType'] == 'Movie':
                            disMovie['stim'].loadMovie(disMovie['stim'].filename) # "Seek" causes audio bugs. This just reloads the movie. More memory load, but reliable.
                    trialType = self.actualTrialOrder[trialNum - 1]
                    while '.' in trialType:
                        trialType = trialType[trialType.index('.') + 1:]
                    didRedo = True
                elif self.keyboard[self.key.J] and self.habMetWhen == -1 and 'Hab' in self.trialOrder:  # jump to test in a hab design
                    [disMovie, trialType] = self.jumpToTest(trialNum)
                elif self.actualTrialOrder[trialNum-1][0:3] not in ['Hab', 'hab'] and self.keyboard[self.key.I] and 'Hab' in self.trialOrder and self.habMetWhen > 0: # insert additional hab trial
                    [disMovie, trialType] = self.insertHab(trialNum)
                    while '.' in trialType:
                        trialType = trialType[trialType.index('.') + 1:]
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
                        waitStart = True
                else:
                    if trialType in self.playAttnGetter:
                        core.wait(self.attnGetterList[self.playAttnGetter[trialType]]['stimDur'] + self.freezeFrame)  # an attempt to match the delay caused by the attention-getter playing.
                        waitStart = True
                    else:
                        waitStart = True
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
                        if self.counters[trialType] > 0:
                            self.counters[trialType] -= 1
                        [disMovie, trialNum] = self.redoSetup(trialNum, AA)  # This returns a new value for DisMovie and trialNum
                        if disMovie['stimType'] == 'Movie':
                            disMovie['stim'].loadMovie(disMovie['stim'].filename)
                        trialType = self.actualTrialOrder[trialNum - 1]
                        while '.' in trialType:
                            trialType = trialType[trialType.index('.') + 1:]
                        didRedo = True
                    elif self.keyboard[self.key.J] and 'Hab' in self.trialOrder and self.habMetWhen == -1:  # jump to test in a hab design.
                        [disMovie,trialType] = self.jumpToTest(trialNum)
                    elif self.keyboard[self.key.I] and self.habMetWhen > 0:  # insert additional hab trial
                        [disMovie,trialType] = self.insertHab(trialNum)
                        while '.' in trialType:
                            trialType = trialType[trialType.index('.') + 1:]
                    elif self.keyboard[self.key.S] and trialType != 'Hab' and '^' not in trialType:  #  Skip trial. Doesn't work on things required for habituation.
                        # TODO: No longer hab only? Actually this may be fine.
                        skip = True
                    else:
                        self.dispCoderWindow(0)
            if not end or skip: #If Y has not been pressed, do the trial! Otherwise, end the experiment.
                x = self.doTrial(trialNum, self.actualTrialOrder[trialNum - 1], disMovie)  # the actual trial, returning one of four status values at the end
                AA = self.autoAdvance  # After the very first trial AA will always be just the autoadvance list.
            elif skip:
                x = 0 # Simply proceed to next trial.
            else:
                x = 2
            if x == 2:  # end experiment, either due to final trial ending or 'end experiment altogether' button.
                runExp = False
                didRedo = False
                self.endExperiment()
            elif x == 3:  # bad trial, redo!
                trialNum = trialNum
                didRedo = True
                if self.stimPres:
                    self.dummyThing.draw()
                    self.win.flip() #Blank the screen.
                    self.counters[trialType] -= 1
                    if self.counters[trialType] < 0:
                        self.counters[trialType] = 0
            elif x == 1:  # end hab block!
                tempNum = self.maxHabIndex
                # trialNum is in fact the index after the current trial at this point
                # so we can just erase everything between that and the first non-hab trial.
                del self.actualTrialOrder[trialNum:tempNum + 1]  # oddly, the del function does not erase the final index.
                trialNum += 1
                trialType = self.actualTrialOrder[trialNum - 1]  # No need to check for hab sub-trials.
                if self.blindPres == 0:
                    self.rdyTextAppend = " NEXT: " + trialType + " TRIAL"
                didRedo = False
            elif x == 0:  # continue hab/proceed as normal
                trialNum += 1
                trialType = self.actualTrialOrder[trialNum - 1]
                while '.' in trialType:
                    trialType = trialType[trialType.index('.') + 1:]
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

    def doTrial(self, number, ttype, disMovie):
        """
        Control function for individual trials, to be called by doExperiment
        Returns a status value (int) that tells doExperiment what to do next

        :param number: Trial number
        :type number: int
        :param ttype: Trial type
        :type ttype: string
        :param  disMovie: A dictionary as follows {'stim':[psychopy object for stimulus presentation], 'stimType':[movie,image,audio, pair]}
        :type disMovie: dictionary
        :return: int, 0 = proceed to next trial, 1 = hab crit met, 2 = end experiment, 3 = trial aborted
        :rtype:
        """
        self.trialText.text = "Trial no. " + str(number)
        habTrial = False  # Just for tracking if this is part of a habituation
        localType = deepcopy(ttype)
        while '.' in localType:
            localType = localType[localType.index('.')+1:]
        if ttype[0:3] == 'hab' and '.' in ttype:  # Hab sub-trials.
            dataType = 'hab' + ttype[ttype.index('.'):]  # Collapses down the number and ^ markings for the data file
            habTrial = True
        elif len(self.habTrialList) == 0 and ttype == 'Hab':
            dataType = ttype
            habTrial = True
        else:
            dataType = ttype
        self.frameCount = 0  # reset display
        self.pauseCount = 0  # needed for ISI
        # returns 0 if do next trial, 1 if end hab, 2 if end experiment, 3 if abort/abort
        if self.stimPres and disMovie['stimType'] == 'Movie':
            disMovie['stim'].seek(0.0)
            disMovie['stim'].pause()
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
        abort = False
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
                abort = True
                runTrial = False
                endTrial = core.getTime() - startTrial
                # determine if they were looking or not at end of trial and update appropriate array
                if gazeOn:
                    onDur = endTrial - startOn
                    # Current format: Trial number, type, start of event, end of event, duration of event.
                    tempGazeArray = {'trial':number, 'trialType':dataType, 'startTime':startOn, 'endTime':endTrial, 'duration':onDur}
                    onArray.append(tempGazeArray)
                else:
                    offDur = endTrial - startOff
                    tempGazeArray = {'trial':number, 'trialType':dataType, 'startTime':startOff, 'endTime':endTrial, 'duration':offDur}
                    offArray.append(tempGazeArray)
            elif core.getTime() - startTrial >= .5 and self.keyboard[self.key.S] and ttype != 'Hab' and '^' not in ttype:
                # New feature: End trial and go forward manually. Disabled for hab trials and meta-trials.
                # Disabled for the first half-second to stop you from skipping through multiple auto-advancing trials
                # TODO: No longer hab only?
                if localType in self.movieEnd:
                    endFlag = True
                else:
                    runTrial = False
                    endTrial = core.getTime() - startTrial
                    if not self.stimPres:
                        self.endTrialSound.play()
                    # determine if they were looking or not at end of trial and update appropriate array
                    if gazeOn:
                        onDur = endTrial - startOn
                        tempGazeArray = {'trial':number, 'trialType':dataType, 'startTime':startOn, 'endTime':endTrial, 'duration':onDur}
                        onArray.append(tempGazeArray)
                    else:
                        offDur = endTrial - startOff
                        tempGazeArray = {'trial':number, 'trialType':dataType, 'startTime':startOff, 'endTime':endTrial, 'duration':offDur}
                        offArray.append(tempGazeArray)

            elif self.keyboard[self.key.Y]:  # the 'end the study' button, for fuss-outs
                runTrial = False
                endTrial = core.getTime() - startTrial
                # determine if they were looking or not at end of trial and update appropriate array
                if gazeOn:
                    onDur = endTrial - startOn
                    tempGazeArray = {'trial':number, 'trialType':dataType, 'startTime':startOn, 'endTime':endTrial, 'duration':onDur}
                    onArray.append(tempGazeArray)
                else:
                    offDur = endTrial - startOff
                    tempGazeArray = {'trial':number, 'trialType':dataType, 'startTime':startOff, 'endTime':endTrial, 'duration':offDur}
                    offArray.append(tempGazeArray)
                if len(onArray) == 0:
                    onArray.append({'trial':0, 'trialType':0, 'startTime':0, 'endTime':0, 'duration':0})
                if len(offArray) == 0:
                    offArray.append({'trial':0, 'trialType':0, 'startTime':0, 'endTime':0, 'duration':0})  # keeps it from crashing while trying to write data.
                ttype = 4  # to force an immediate quit.
            # Now for the non-abort states.
            elif core.getTime() - startTrial >= self.maxDur[localType] and not endFlag:  # reached max trial duration
                if localType in self.movieEnd:
                    endFlag = True
                else:
                    runTrial = False
                    endTrial = core.getTime() - startTrial
                    if not self.stimPres:
                        self.endTrialSound.play()
                    # determine if they were looking or not at end of trial and update appropriate array
                    if gazeOn:
                        onDur = endTrial - startOn
                        tempGazeArray = {'trial':number, 'trialType':dataType, 'startTime':startOn, 'endTime':endTrial, 'duration':onDur}
                        onArray.append(tempGazeArray)
                    else:
                        offDur = endTrial - startOff
                        tempGazeArray = {'trial':number, 'trialType':dataType, 'startTime':startOff, 'endTime':endTrial, 'duration':offDur}
                        offArray.append(tempGazeArray)
            elif not gazeOn:  # if they are not looking as of the previous refresh, check if they have been looking away for too long
                nowOff = core.getTime() - startTrial
                if sumOn >= self.minOn[localType] and nowOff - startOff >= self.maxOff[localType] and self.playThrough[localType] == 0 and not endFlag:
                    # if they have previously looked for at least .5s and now looked away for 2 continuous sec
                    if localType in self.movieEnd:
                        endFlag = True
                    else:
                        runTrial = False
                        endTrial = core.getTime() - startTrial
                        if not self.stimPres:
                            self.endTrialSound.play()
                        endOff = nowOff
                        offDur = nowOff - startOff
                        tempGazeArray = {'trial':number, 'trialType':dataType, 'startTime':startOff, 'endTime':endOff, 'duration':offDur}
                        offArray.append(tempGazeArray)
                elif self.keyboard[self.key.B]:  # if they have started looking since the last refresh and not met criterion
                    gazeOn = True
                    numOn = numOn + 1
                    startOn = core.getTime() - startTrial
                    endOff = core.getTime() - startTrial
                    # by definition, if this is tripped there will be a preceding 'off' section if this is tripped because gazeOn is set at start
                    offDur = endOff - startOff
                    tempGazeArray = {'trial':number, 'trialType':dataType, 'startTime':startOff, 'endTime':endOff, 'duration':offDur}
                    offArray.append(tempGazeArray)
            elif gazeOn:
                nowOn = core.getTime() - startTrial
                if self.playThrough[localType] == 1 and sumOn + (nowOn - startOn) >= self.minOn[localType] and not endFlag:  # For trial types where the only crit is min-on.
                    if localType in self.movieEnd:
                        endFlag = True
                    else:
                        runTrial = False
                        endTrial = core.getTime() - startTrial
                        if not self.stimPres:
                            self.endTrialSound.play()
                        endOn = core.getTime() - startTrial
                        onDur = endOn - startOn
                        tempGazeArray = {'trial':number, 'trialType':dataType, 'startTime':startOn, 'endTime':endOn, 'duration':onDur}
                        onArray.append(tempGazeArray)
                if gazeOn and not self.keyboard[self.key.B]:  # if they were looking and have looked away.
                    gazeOn = False
                    endOn = core.getTime() - startTrial
                    onDur = endOn - startOn
                    numOff = numOff + 1
                    startOff = core.getTime() - startTrial
                    tempGazeArray = {'trial':number, 'trialType':dataType, 'startTime':startOn, 'endTime':endOn, 'duration':onDur}
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
                    tempGazeArray2 = {'trial':number, 'trialType':dataType, 'startTime':startOff2, 'endTime':endOff2, 'duration':offDur2}
                    offArray2.append(tempGazeArray2)
            elif gazeOn2 and not self.keyboard[self.secondKey]:  # if they were looking and have looked away.
                gazeOn2 = False
                endOn2 = core.getTime() - startTrial2
                onDur2 = endOn2 - startOn2
                numOff2 = numOff2 + 1
                startOff2 = core.getTime() - startTrial2
                tempGazeArray2 = {'trial':number, 'trialType':dataType, 'startTime':startOn2, 'endTime':endOn2, 'duration':onDur2}
                onArray2.append(tempGazeArray2)
                sumOn2 = sumOn2 + onDur2
            movieStatus = self.dispTrial(localType, disMovie)
            if localType in self.movieEnd and endFlag and movieStatus >= 1:
                runTrial = False
                endTrial = core.getTime() - startTrial
                if gazeOn:
                    onDur = endTrial - startOn
                    tempGazeArray = {'trial':number, 'trialType':dataType, 'startTime':startOn, 'endTime':endTrial, 'duration':onDur}
                    onArray.append(tempGazeArray)
                else:
                    offDur = endTrial - startOff
                    tempGazeArray = {'trial':number, 'trialType':dataType, 'startTime':startOff, 'endTime':endTrial, 'duration':offDur}
                    offArray.append(tempGazeArray)
        if gazeOn2:
            onDur2 = endTrial - startOn2
            tempGazeArray2 = {'trial':number, 'trialType':dataType, 'startTime':startOn2, 'endTime':endTrial, 'duration':onDur2}
            onArray2.append(tempGazeArray2)
        else:
            offDur2 = endTrial - startOff2
            tempGazeArray2 = {'trial':number, 'trialType':dataType, 'startTime':startOff2, 'endTime':endTrial, 'duration':offDur2}
            offArray2.append(tempGazeArray2)
        # print offArray
        # print onArray2
        # print offArray2
        if habTrial:
            habDataRec = self.habCount + 1
        else:
            habDataRec = 0
        if self.stimPres:
            # Reset everything, stop playing sounds and movies.
            if disMovie['stimType'] == 'Movie':
                disMovie['stim'].seek(0.0)
                disMovie['stim'].pause()
            elif disMovie['stimType'] == 'Audio':
                disMovie['stim'].stop()
            elif disMovie['stimType'] == 'Image with audio':
                disMovie['stim']['Audio'].stop()
        if self.stimPres and number < len(self.actualTrialOrder):
            if self.actualTrialOrder[number] not in self.autoAdvance:
                self.dummyThing.draw()
                self.win.flip()  # blanks the screen outright between trials if NOT auto-advancing into the next trial
        if abort:  # if the abort button was pressed
            if self.stimPres and disMovie['stimType'] == 'Movie':
                disMovie['stim'].seek(0.0)
                disMovie['stim'].pause()
            self.abortTrial(onArray, offArray, number, dataType, onArray2, offArray2, self.stimName, habDataRec)
            return 3
        else:
            self.dataRec(onArray, offArray, number, dataType, onArray2, offArray2, self.stimName, habDataRec)
        if self.habMetWhen == -1 and len(self.habTrialList) > 0 and not abort:   # if still during habituation
            if dataType[0:4] == 'hab.' and localType in self.calcHabOver:
                tempSum = 0
                for c in range(0, len(onArray)):
                    tempSum += onArray[c]['duration']
                self.habDataCompiled[self.habCount] += tempSum
            if '^' in ttype: # TODO: No longer hab only?
                self.habCount += 1  # Note: Occurs after data recording, making recording hab trial number hard.
                # Check if criteria need to be set or have been met
                if self.checkStop():  # If criteria met
                    # Check if there are any trials FOLLOWING the hab trials.
                    if self.maxHabIndex < len(self.actualTrialOrder)-1:
                        return 1
                    else:
                        return 2  # End experiment.
                else:
                    return 0
            else:
                return 0
        elif ttype == 'Hab' and self.habMetWhen == -1 and not abort:
            tempSum = 0
            for c in range(0, len(onArray)):
                tempSum += onArray[c]['duration']
            self.habDataCompiled[self.habCount] += tempSum
            self.habCount += 1
            if self.checkStop():  # If criteria met
                # Check if there are any trials FOLLOWING the hab trials.
                if self.actualTrialOrder[-1] != 'Hab':
                    return 1
                else:
                    return 2  # End experiment.
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
        End experiment, save all data, calculate reliability if needed, close up shop. Displays "saving data" and
        end-of-experiment screen.

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

        # Block-level summary data. Omits bad trials.
        if len(self.blockDataList > 0):
            tempMatrix = self.saveBlockFile()
            # Now write the actual data file
            nDupe = ''  # This infrastructure eliminates the risk of overwriting existing data
            o = 1
            blockfilename = self.dataFolder + self.prefix + str(self.sNum) + '_' + str(
                self.sID) + nDupe + '_BlockSumm_' + str(
                self.today.month) + str(self.today.day) + str(self.today.year) + '.csv'
            while os.path.exists(blockfilename):
                o += 1
                nDupe = str(o)
                blockfilename = self.dataFolder + self.prefix + str(self.sNum) + '_' + str(
                    self.sID) + nDupe + '_BlockSumm_' + str(
                    self.today.month) + str(self.today.day) + str(self.today.year) + '.csv'
            with open(blockfilename, 'w') as b:
                blockWriter = csv.DictWriter(b, fieldnames=self.dataColumns, extrasaction='ignore', lineterminator='\n')
                blockWriter.writeheader()
                for z in range(0, len(tempMatrix)):
                    blockWriter.writerow(tempMatrix[z])

        # If there is habituation data, create hab summary file. Similar to the block one, but a little easier thanks to
        # the tagging of habituation trial numbers.
        if self.habSetWhen > 0 and len(self.habTrialList) > 0:  # If there's a 'Hab' trial type, the main summary file does the trick just fine.
            habMatrix = self.saveHabFile()
            # Now, actually write the file
            nDupe = ''  # This infrastructure eliminates the risk of overwriting existing data
            o = 1
            habfilename = self.dataFolder + self.prefix + str(self.sNum) + '_' + str(
                self.sID) + nDupe + '_HabSumm_' + str(
                self.today.month) + str(self.today.day) + str(self.today.year) + '.csv'
            while os.path.exists(habfilename):
                o += 1
                nDupe = str(o)
                habfilename = self.dataFolder + self.prefix + str(self.sNum) + '_' + str(
                    self.sID) + nDupe + '_HabSumm_' + str(
                    self.today.month) + str(self.today.day) + str(self.today.year) + '.csv'
            with open(habfilename, 'w') as h:
                habWriter = csv.DictWriter(h, fieldnames=self.dataColumns, extrasaction='ignore', lineterminator='\n')
                habWriter.writeheader()
                for z in range(0, len(habMatrix)):
                    habWriter.writerow(habMatrix[z])

        # Shuffle together bad data and good data into the appropriate order.
        if len(self.badTrials) > 0:  # if there are any redos, they need to be shuffled in appropriately.
            for i in range(0, len(self.badTrials)):
                x = 0
                while x < len(self.dataMatrix) and self.dataMatrix[x]['trial'] != self.badTrials[i]['trial']:
                    x += 1
                while  x < len(self.dataMatrix) and self.dataMatrix[x]['GNG'] == 0:  # this is to get around the possibility that the same trial had multiple 'false starts'
                    x += 1
                self.dataMatrix.insert(x, self.badTrials[i])  # python makes this stupid easy
        nDupe = '' # This infrastructure eliminates the risk of overwriting existing data
        o = 1
        filename = self.dataFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + nDupe + '_' + str(self.today.month) + str(
                self.today.day) + str(self.today.year) + '.csv'
        while os.path.exists(filename):
            o += 1
            nDupe = str(o)
            filename = self.dataFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + nDupe + '_' + str(
                self.today.month) + str(
                self.today.day) + str(self.today.year) + '.csv'
        with open(filename, 'w') as f:
            outputWriter = csv.DictWriter(f, fieldnames=self.dataColumns, extrasaction='ignore', lineterminator='\n')
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
        with open(self.verboseFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + nDupe + '_' + str(self.today.month) + str(self.today.day) + str(self.today.year) + '_VERBOSE.csv', 'w') as f:
            outputWriter2 = csv.DictWriter(f, fieldnames=headers2, extrasaction='ignore', lineterminator='\n')
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
            with open(self.verboseFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + nDupe + '_' + str(self.today.month) + str(self.today.day) + str(self.today.year) + '_VERBOSEb.csv', 'w') as f:
                outputWriter3 = csv.DictWriter(f, fieldnames=headers2, extrasaction='ignore', lineterminator='\n')
                outputWriter3.writeheader()
                for k in range(0, len(verboseMatrix2)):
                    outputWriter3.writerow(verboseMatrix2[k])
            rel = self.reliability(verboseMatrix, verboseMatrix2)
            headers3 = ['WeightedPercentageAgreement', 'CohensKappa', 'AverageObserverAgreement', 'PearsonsR']
            with open(self.dataFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + nDupe + '_' + str(self.today.month) + str(self.today.day) + str(self.today.year) + '_Stats.csv', 'w') as f:
                outputWriter4 = csv.DictWriter(f, fieldnames=headers3, extrasaction='ignore', lineterminator='\n')
                outputWriter4.writeheader()
                outputWriter4.writerow(rel)
        # core.wait(.3) Replaced by end-of-experiment screen
        # "end of experiment" screen. By default this will go to a black screen on the stim view
        # and display "Experiment finished!" on the experimenter view
        tempText.text = "Experiment finished! Press return to close."
        tempText.height = 18
        tempText.draw()
        self.win2.flip()
        if self.stimPres:
            self.dummyThing.draw()
            if self.endImageObject is not None:
                self.endImageObject.draw()
            self.win.flip()
        event.waitKeys(keyList='return')

        self.win2.close()
        if self.stimPres:
            self.win.close()

    def saveBlockFile(self):
        """
        A function that create a block-level summary file and saves it. Copies the primary data matrix (only good trials)
        and loops over it, compressing all blocks. Does not work for habs, which follow their own rules.

        :return: A condensed copy of dataMatrix with all blocks of the relevant types condensed to one line.
        :rtype: list
        """
        tempMatrix = deepcopy(self.dataMatrix)
        tempIndex = 0
        blockDone = False
        lastTrialNumber = tempMatrix[-1]['trial']
        # Making this generalizeable for preferential looking studies.
        if 'sumOnL' in self.dataMatrix[0].keys():
            sumFields = ['sumOnL','numOnL','sumOnR', 'numOnR', 'sumOff', 'numOff']
        else:
            sumFields = ['sumOnA', 'numOnA', 'sumOffA', 'numOffA', 'sumOnB', 'numOnB', 'sumOffB', 'numOffB']
        while not blockDone:
            nt = tempMatrix[tempIndex]['trial']
            for i, j in self.blockDataTags.items():
                for k in range(0, len(j)):
                    if nt in j[k]:
                        tempType = tempMatrix[tempIndex]['trialType']
                        if tempType[0:tempType.index('.')] == i:
                            tempMatrix[tempIndex]['trialType'] = i  # Rename the type line for the block as a whole.
                        else: # If it's nested, maintain the prefixes.
                            nestType = deepcopy(tempType)
                            prefix = ''
                            while nestType[0:nestType.index('.')] != i:
                                prefix = prefix+nestType[0:nestType.index('.')]+'.'
                                nestType = nestType[nestType.index('.')+1:]
                            tempMatrix[tempIndex]['trialType'] = prefix+i  # Rename the type line for the block as a whole.
                        for l in range(1, len(j[k])):  # Taking advantage of continguity of blocks.
                            if j[k][l] <= lastTrialNumber:  # For studies that end early.
                                # Fields to modify: sum and num on/off a/b, append stimnames.
                                tempLine = tempMatrix.pop(tempIndex + 1)  # Because we'll be sequentially popping them off, it'll always be the next one
                                tempMatrix[tempIndex]['stimName'] = tempMatrix[tempIndex]['stimName'] + '+' + tempLine['stimName']
                                for z in range(0, len(sumFields)):
                                    tempMatrix[tempIndex][sumFields[z]] = tempMatrix[tempIndex][sumFields[z]] + tempLine[sumFields[z]]
            tempIndex += 1
            if tempIndex >= len(tempMatrix):
                blockDone = True
        for i in range(0, len(tempMatrix)):
            tempMatrix[i]['trial'] = i+1
        return tempMatrix

    def saveHabFile(self):
        """
        Creates a habituation summary data file, which has one line per hab trial, and only looks at parts of the hab
        trial that were included in calcHabOver. This is notably easier in some ways because the hab trials are already
        tagged in dataMatrix

        :return: A condensed copy of dataMatrix with all hab trials condensed only to those that were used to compute habituation.
        :rtype: list
        """
        habMatrix = []
        # Making this generalizeable for preferential looking studies.
        if 'sumOnL' in self.dataMatrix[0].keys():
            sumFields = ['sumOnL', 'numOnL', 'sumOnR', 'numOnR', 'sumOff', 'numOff']
        else:
            sumFields = ['sumOnA', 'numOnA', 'sumOffA', 'numOffA', 'sumOnB', 'numOnB', 'sumOffB', 'numOffB']
        for i in range(0, len(self.dataMatrix)):
            if isinstance(self.dataMatrix[i]['habTrialNo'], int):
                tempType = deepcopy(self.dataMatrix[i]['trialType'])
                while '.' in tempType:
                    tempType = tempType[tempType.index('.') + 1:]
                if tempType in self.calcHabOver:  # If not, this should specifically be ignored.
                    tempNo = self.dataMatrix[i]['habTrialNo']
                    addTo = False
                    addIndex = -1
                    tempLine = deepcopy(self.dataMatrix[i])
                    tempLine['trialType'] = 'Hab'
                    for j in range(0, len(habMatrix)):
                        if habMatrix[j]['habTrialNo'] == tempNo:
                            addTo = True
                            addIndex = deepcopy(j)
                    if addTo:
                        habMatrix[addIndex]['stimName'] = habMatrix[addIndex]['stimName'] + '+' + tempLine['stimName']
                        for z in range(0, len(sumFields)):
                            habMatrix[addIndex][sumFields[z]] = habMatrix[addIndex][sumFields[z]] + tempLine[sumFields[z]]
                    else:
                        habMatrix.append(tempLine)
                else:
                    pass
            else:  # For all non-habituation trials.
                habMatrix.append(deepcopy(self.dataMatrix[i]))
        for i in range(0, len(habMatrix)):
            habMatrix[i]['trial'] = i+1
        return habMatrix

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

        Also expands habituation blocks appropriately and tags trials with habituation iteration number as well as
        the symbol for the end of a hab block (^)

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
                startDlg.addText("Date of test (leave blank for today)")
                startDlg.addField('DOT(month): ')
                startDlg.addField('DOT(day): ')
                startDlg.addField('DOT(year): ')
            startDlg.show()
        if startDlg.OK:
            fail = False # A bool for detecting if we have to start over at any point.
            thisInfo = startDlg.data
            self.sNum = thisInfo[0]
            self.sID = thisInfo[1]
            self.sex = thisInfo[2]
            # now for the exciting bit: converting DOB into months/days.
            self.today = date.today()
            # First, check valid entries
            try:
                for i in range(3,6):
                    irrel = int(thisInfo[i])
            except:
                fail = True
            if not fail:
                # then, check if 4-digit or 2-digit year.
                if len(thisInfo[5]) > 2:
                    year = int(thisInfo[5])
                else:
                    year = 2000 + int(thisInfo[5])
                DOB = date(year, int(thisInfo[3]), int(thisInfo[4]))
                if self.stimPres:
                    DOT = self.today
                elif len(thisInfo[9]) == 0 or len(thisInfo[8]) == 0 or len(thisInfo[7]) == 0:
                    DOT = self.today
                else:
                    try:
                        if len(thisInfo[9]) > 2:
                            year = int(thisInfo[9])
                        else:
                            year = 2000 + int(thisInfo[9])
                        DOT = date(year, int(thisInfo[7]), int(thisInfo[8]))
                    except:
                        DOT = self.today
                        warnDlg = gui.Dlg("Warning! Invalid date!")
                        warnDlg.addText("DOT is invalid. Defaulting to today's date.")
                        irrel = warnDlg.show()
                # Dateutil's relativedelta is included in psychopy and just better than every other option!
                ageDif = relativedelta(DOT, DOB)
                self.ageMo = ageDif.years * 12 + ageDif.months
                self.ageDay = ageDif.days  # Impossibly simple, but it works.
                # build stimulus order
                if self.randPres and len(self.condList) > 0:  # Extra check: We WANT conditions and we HAVE them too.
                    self.condLabel = thisInfo[6]
                    testReader = csv.reader(open(self.condPath + self.condFile, 'rU'))
                    testStuff = []
                    for row in testReader:
                        testStuff.append(row)
                    testDict = dict(testStuff)
                    self.cond = testDict[self.condLabel]  # this will read as order of movies in N groups, in a 2-dimensional array
                    # type conversion required. Eval will read the string into a dictionary (now).
                    self.cond = eval(self.cond)
                    # now to rearrange the lists of each trial type.
                    finalDict = {}
                    finalBlock = {}
                    for i, j in self.cond.items():
                        newTempTrials = []
                        for q in range(0, len(j)):
                            if type(j[q]) is int:  # Dealing with old versions.
                                newTempTrials.append(self.stimNames[i][j[q] - 1])
                                #print("Converting old conditions...")

                            else:
                                newTempTrials.append(j[q])
                        if i in self.blockList.keys():
                            finalBlock[i] = newTempTrials
                        finalDict[i] = newTempTrials
                    self.stimNames = finalDict
                    self.blockList = finalBlock
                else:
                    self.cond = thisInfo[6]
                    self.condLabel = self.cond
                # Set actual order of trials
                self.actualTrialOrder = []  # in this version, mostly a key for the hab trials and blocks.
                for i in range(0, len(self.trialOrder)):
                    if self.trialOrder[i] == 'Hab':
                        for j in range(0, self.maxHabTrials):
                            if len(self.habTrialList) > 0:
                                self.blockExpander(self.habTrialList, 'hab', hab=True, habNum=j + 1)
                            else:
                                self.actualTrialOrder.append('Hab')
                        self.maxHabIndex = len(self.actualTrialOrder) - 1  # Tracks the very last hab trial.
                    elif self.trialOrder[i] in self.blockList.keys():
                        #TODO block data structure
                        if self.trialOrder[i] in self.blockDataList:
                            start = len(self.actualTrialOrder)
                        self.blockExpander(self.blockList[self.trialOrder[i]], self.trialOrder[i])
                        if self.trialOrder[i] in self.blockDataList:
                            end = len(self.actualTrialOrder)
                            tempList = list(range(start+1,end+1))
                            self.blockDataTags[self.trialOrder[i]].append(tempList)
                    else:
                        self.actualTrialOrder.append(self.trialOrder[i])
                if len(testMode) == 0: # If we're in test mode, skip setting up the window and launching the experiment.
                    if len(self.actualTrialOrder) == 0:
                        errWindow = gui.Dlg("Warning: No trials!")
                        errWindow.addText(
                            "There are no trials in the study flow! Please return to the builder and add trials to the study flow.")
                        errWindow.show()
                    else:
                        self.SetupWindow()
            else:
                self.run()

    def blockExpander(self, blockTrials, prefixes, hab=False, habNum=0, insert=-1):
        """
        A method for constructing actualTrialOrder while dealing with recursive blocks. Can create incredibly long trial
        codes, but ensures that all information is accurately preserved. Works for both hab blocks and other things.
        For hab blocks, we can take advantage of the fact that hab cannot appear inside any other block. It will always
        be the top-level block, and so we can adjust the prefix once and it will carry through.

        :param blockTrials: The list of trials in self.blockList or self.habSubTrials
        :type blockTrials: list
        :param prefixes: A recursively growing stack of prefixes. If block A has B and block B has C, then an instance
        of A will be A.B.C in self.actualTrialOrder. This keeps track of the A.B. part.
        :type prefixes: str
        :param hab: Are we dealing with a habituation trial expansion?
        :type hab: bool
        :param habNum: If we are dealing with a habituation trial expansion, what number of it are we on?
        :type habNum: int
        :param insert: An int specifying where in actualTrialOrder to put a trial. Needed to generalize this function for insertHab
        :type insert: int
        :return:
        :rtype:
        """
        if hab:
            prefixes = prefixes + str(habNum)
        for q in range(0, len(blockTrials)):
            tempName = blockTrials[q]
            if tempName in self.blockList.keys():
                if tempName in self.blockDataList:
                    start = len(self.actualTrialOrder)
                self.blockExpander(self.blockList[tempName], prefixes+'.'+tempName, hab=False, insert=insert)
                if tempName in self.blockDataList:
                    end = len(self.actualTrialOrder)
                    tempList = list(range(start + 1, end + 1))
                    self.blockDataTags[tempName].append(tempList)
                if hab and q == len(self.habTrialList) - 1: # Go back and pin on the ^ if needed. A little cheaty
                    revise = deepcopy(self.actualTrialOrder[-1])
                    revise = revise[:revise.index('.')] + '^' + revise[revise.index('.'):]
                    self.actualTrialOrder[-1] = revise
            else:
                if hab and q == len(self.habTrialList) - 1:
                    prefixes = prefixes + '^'  # End-of-hab-cycle marker
                tempName = prefixes + '.' + tempName
                if insert == -1:
                    self.actualTrialOrder.append(tempName)
                else:
                    self.actualTrialOrder.insert(insert, tempName)
                    insert += 1




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
            self.win = visual.Window((self.screenWidth, self.screenHeight), fullscr=False, screen=self.screenIndex, allowGUI=False,
                                     units='pix', color=self.screenColor)
            self.dummyThing = visual.Circle(self.win, size=1, color=self.win.color) # This is for fixing a display glitch in PsychoPy3 involving multiple windows of different sizes.
        # Coder window
        self.win2 = visual.Window((400, 400), fullscr=False, screen=self.expScreenIndex, allowGUI=True, units='pix', waitBlanking=False,
                                  rgb=[-1, -1, -1])
        if self.stimPres:
            tempText = visual.TextStim(self.win2, text="Loading Stimuli", pos=[0, 0], color='white', bold=True, height=40)
            tempText.draw()
            self.win2.flip()
            # Step 1: Load and present "startImage"
            if self.startImage is not '':
                self.dummyThing.draw()
                tempStim = self.stimList[self.startImage]
                tempStimObj = visual.ImageStim(self.win, tempStim['stimLoc'], size=[self.movieWidth, self.movieHeight])
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
                if x < len(self.stimNames[i]):
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

            if len(list(self.playAttnGetter.keys())) > 0:
                for i in list(self.attnGetterList.keys()):
                    if self.attnGetterList[i]['stimType'] == 'Audio':
                        self.attnGetterList[i]['file'] = sound.Sound(self.attnGetterList[i]['stimLoc'])
                    else:
                        self.attnGetterList[i]['file'] = visual.MovieStim3(self.win, self.attnGetterList[i]['stimLoc'],
                                                                           size=[self.movieWidth, self.movieHeight],
                                                                           flipHoriz=False, flipVert=False, loop=False)
            if self.endImage is not '': # Load image for end of experiment, if needed.
                tempStim = self.stimList[self.endImage]
                self.endImageObject = visual.ImageStim(self.win, tempStim['stimLoc'], size=[self.movieWidth, self.movieHeight])
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
