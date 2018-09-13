import os, sys
from psychopy import visual, event, core, data, gui, monitors, tools, prefs, logging

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
from PyHabClass import PyHab

class PyHabPL(PyHab):
    """
    A new preferential-looking version of PyHab that extends the base class rather than being a wholly separate class.
    There's still a lot of redundant code here, which will require significant restructuring of the base class to fix.
    """
    def __init__(self, settingsDict):
        PyHab.__init__(self, settingsDict)
        self.secondKey = self.key.M #Variable that determines what the second key is. Overwrites what is set in the default init
        self.verbDatList = {'verboseOn': [], 'verboseOn2': [], 'verboseOff': []}  # a dict of the verbose data arrays
        self.verbBadList = {'verboseOn': [], 'verboseOn2': [],  'verboseOff': []}  # Corresponding for bad data

    def abortTrial(self, onArray, offArray, trial, ttype, onArray2, stimName=''):
        """
        Aborts a trial in progress, saves any data recorded thus far to the bad-data structures

        :param onArray: Gaze-on Left events
        :type onArray: list of dicts {trial, trialType, startTime, endTime, duration}
        :param offArray: Gaze-off events
        :type offArray: list of dicts {trial, trialType, startTime, endTime, duration}
        :param trial: Trial number
        :type trial: int
        :param ttype: Trial type
        :type ttype: string
        :param onArray2: Gaze-on Right events
        :type onArray2: list of dicts {trial, trialType, startTime, endTime, duration}
        :param stimName: If presenting stimuli, name of the stim file
        :type stimName: string
        :return:
        :rtype:
        """
        sumOn = 0
        sumOff = 0
        sumOn2 = 0
        if ttype == 'Hab':
            self.habCount -= 1
        for i in range(0, len(onArray)):
            sumOn = sumOn + onArray[i]['duration']
        for k in range(0, len(onArray2)):
            sumOn2 = sumOn2 + onArray2[k]['duration']
        for j in range(0, len(offArray)):
            sumOff = sumOff + offArray[j]['duration']
        # needs to be .extend or you get weird array-within-array-within-array issues that become problematic later
        self.verbBadList['verboseOn'].extend(onArray)
        self.verbBadList['verboseOn2'].extend(onArray2)
        self.verbBadList['verboseOff'].extend(offArray)
        tempData = {'sNum': self.sNum, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex, 'cond': self.cond,
                    'condLabel': self.condLabel,
                    'trial': trial, 'GNG': 0, 'trialType': ttype, 'stimName': stimName, 'habCrit': self.habCrit,
                    'sumOnL': sumOn, 'numOnL': len(onArray),
                    'sumOnR': sumOn2, 'numOnR': len(onArray2), 'sumOff': sumOff, 'numOff': len(offArray)}
        self.badTrials.append(tempData)

    def dataRec(self, onArray, offArray, trial, type, onArray2, stimName=''):
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
        :param onArray2: Gaze-on Right events
        :type onArray2: list of dicts {trial, trialType, startTime, endTime, duration}
        :param stimName: If presenting stimuli, name of the stim file
        :type stimName: string
        :return:
        :rtype:
        """
        sumOn = 0
        sumOff = 0
        sumOn2 = 0
        #loop through each array adding up gaze duration (on and off).
        for i in range(0,len(onArray)):
            sumOn = sumOn + onArray[i]['duration']
        for j in range(0,len(offArray)):
            sumOff = sumOff + offArray[j]['duration']
        for k in range(0,len(onArray2)):
            sumOn2 = sumOn2 + onArray2[k]['duration']
        #add to verbose master gaze array
        self.verbDatList['verboseOn'].extend(onArray)
        self.verbDatList['verboseOff'].extend(offArray)
        self.verbDatList['verboseOn2'].extend(onArray2)
        tempData={'sNum':self.sNum, 'months':self.ageMo, 'days':self.ageDay, 'sex':self.sex, 'cond':self.cond,'condLabel':self.condLabel,
                                'trial':trial, 'GNG':1, 'trialType':type, 'stimName':stimName, 'habCrit':self.habCrit,
                                'sumOnL':sumOn, 'numOnL':len(onArray),
                                'sumOnR':sumOn2,'numOnR':len(onArray2),'sumOff':sumOff, 'numOff':len(offArray)}
        self.dataMatrix.append(tempData)

    def checkStop(self):
        """
        After a hab trial, checks the habitution criteria and returns 'true' if any of them are met.
        Needs its own version because it has to get both timeOnL and timeOnR

        :param trial: Trial number
        :type trial: int
        :return: True if hab criteria have been met, False otherwise
        :rtype:
        """
        if self.habCount == self.setCritWindow:  # time to set the hab criterion.
            sumOnTimes = 0
            # find first hab trial
            x = 0
            for j in range(0, len(self.dataMatrix)):
                if self.dataMatrix[j]['trialType'] == 'Hab':
                    x = j
                    break
            for k in range(x, len(self.dataMatrix)):
                if self.dataMatrix[k]['GNG'] == 1 and self.dataMatrix[k]['trialType'] == 'Hab':  # just in case there are any bad trials, we don't want to incorporate them into setting the criterion
                    sumOnTimes = sumOnTimes + self.dataMatrix[k]['sumOnL'] + self.dataMatrix[k]['sumOnR']  # add up total looking time for first three (good) trials
            self.habCrit = sumOnTimes / self.setCritDivisor
        elif self.setCritType == 'Peak':  # Checks if we need to update the hab criterion
            sumOnTimes = 0
            habs = [i for i, x in enumerate(self.actualTrialOrder) if x == 'Hab']  # list of all habs
            habs.sort()
            index = habs[self.habCount - self.setCritWindow] #How far back should we look?
            for n in range(index, len(self.dataMatrix)):  # now, starting with that trial, go through and add up the good trial looking times
                if self.dataMatrix[n]['GNG'] == 1 and self.dataMatrix[n]['trialType'] == 'Hab':  # only good trials!
                    sumOnTimes = sumOnTimes + self.dataMatrix[n]['sumOnL'] + self.dataMatrix[n]['sumOnR']  # add up total looking time
            sumOnTimes = sumOnTimes / self.setCritDivisor
            if sumOnTimes > self.habCrit:
                self.habCrit = sumOnTimes
        elif self.setCritType == 'Max' and self.habCount > self.setCritWindow:  # Absolute max looking time among hab trials, regardless of order.
            habOns = []
            for n in range(0, len(self.dataMatrix)):
                if self.dataMatrix[n]['GNG'] == 1 and self.dataMatrix[n]['trialType'] == 'Hab':
                    habOns.append(self.dataMatrix[n]['sumOnL']+self.dataMatrix[n]['sumOnR'])
            habOns.sort()
            sumOnTimes = habOns[-1] + habOns[-2] + habOns[-3]
            sumOnTimes = sumOnTimes / self.setCritDivisor
            if sumOnTimes > self.habCrit:
                self.habCrit = sumOnTimes

        # Now we separate out the set and met business.
        if self.habCount == self.maxHabTrials:
            # end habituation and goto test
            return True
        elif self.habCount >= self.setCritWindow + self.metCritWindow:  # if we're far enough in that we can plausibly meet the hab criterion
            sumOnTimes = 0
            habs = [i for i, x in enumerate(self.actualTrialOrder) if x == 'Hab']  # list of all habs
            habs.sort()
            index = habs[self.habCount - self.metCritWindow]
            if (self.metCritStatic == 'Moving') or (self.habCount-self.setCritWindow) % self.metCritWindow == 0:
                for n in range(index, len(self.dataMatrix)):  # now, starting with that trial, go through and add up the good trial looking times
                    if self.dataMatrix[n]['GNG'] == 1 and self.dataMatrix[n]['trialType'] == 'Hab':  # only good trials!
                        sumOnTimes = sumOnTimes + self.dataMatrix[n]['sumOnL'] + self.dataMatrix[n]['sumOnR'] # add up total looking time
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


    def lookKeysPressed(self):
        """
        A simple boolean function to allow for more modularity with preferential looking
        Basically, allows you to set an arbitrary set of keys to start a trial once the attngetter has played.
        In this case, only B or M are sufficient.

        :return: True if the B or M key is pressed, False otherwise.
        :rtype:
        """
        if self.keyboard[self.key.B] or self.keyboard[self.key.M]:
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
        self.frameCount = 0 #reset display
        self.pauseCount = 0 #needed for ISI
        if self.stimPres and disMovie['stimType'] == 'Movie':
            disMovie['stim'].seek(0)
        startTrial = core.getTime()
        startTrial2=core.getTime()
        onArray = []
        offArray = []
        onArray2=[]
        offArray2=[]
        numOn = 0
        numOff = 0
        sumOn = 0
        sumOn2 = 0
        numOff2 = 0
        numOn2 = 0
        redo = False
        runTrial = True
        endFlag = False
        self.readyText.text="Trial running"
        if self.keyboard[self.key.B]:
            gazeOn = True
            gazeOn2 = False
            startOn = 0 #we want these to be 0 because every other time is put in reference to the startTrial timestamp so it's not some absurd number
            numOn = 1
        elif self.keyboard[self.secondKey]:
            gazeOn2 = True
            gazeOn = False
            startOn2 = 0
            numOn2 = 1
        else:
            gazeOn = False
            gazeOn2 = False
            numOff = 1
            startOff = 0
        while runTrial:
            if self.keyboard[self.key.R]: #'abort trial' is pressed
                redo = True
                runTrial = False
                endTrial = core.getTime() - startTrial
                #determine if they were looking or not at end of trial and update appropriate array
                if gazeOn or gazeOn2:
                    if gazeOn:
                        onDur = endTrial - startOn
                        # Current format: Trial number, type, start of event, end of event, duration of event.
                        tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOn, 'endTime': endTrial,
                                         'duration': onDur}
                        onArray.append(tempGazeArray)
                    if gazeOn2:
                        onDur2 = endTrial - startOn2
                        tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOn2, 'endTime': endTrial,
                                         'duration': onDur2}
                        onArray2.append(tempGazeArray)
                else:
                    offDur = endTrial - startOff
                    tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOff, 'endTime': endTrial,
                                     'duration': offDur}
                    offArray.append(tempGazeArray)
            elif self.keyboard[self.key.Y]: #the 'end the study' button, for fuss-outs
                runTrial = False
                endTrial = core.getTime() - startTrial
                #determine if they were looking or not at end of trial and update appropriate array
                if gazeOn or gazeOn2:
                    if gazeOn:
                        onDur = endTrial - startOn
                        # Current format: Trial number, type, start of event, end of event, duration of event.
                        tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOn, 'endTime': endTrial,
                                         'duration': onDur}
                        onArray.append(tempGazeArray)
                    if gazeOn2:
                        onDur2 = endTrial - startOn2
                        tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOn2, 'endTime': endTrial,
                                         'duration': onDur2}
                        onArray2.append(tempGazeArray)
                else:
                    offDur = endTrial - startOff
                    tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOff, 'endTime': endTrial,
                                     'duration': offDur}
                    offArray.append(tempGazeArray)
                if len(onArray) == 0:
                    onArray.append({'trial': 0, 'trialType': 0, 'startTime': 0, 'endTime': 0,'duration': 0})
                if len(onArray2) == 0:
                    onArray2.append({'trial': 0, 'trialType': 0, 'startTime': 0, 'endTime': 0,'duration': 0})
                if len(offArray) == 0:
                    offArray.append({'trial': 0, 'trialType': 0, 'startTime': 0, 'endTime': 0,'duration': 0}) #keeps it from crashing while trying to write data.
                type = 4 #to force an immediate quit.
            #Now for the non-abort states.
            elif core.getTime() - startTrial >= self.maxDur[type] and not endFlag: #reached max trial duration
                if type in self.movieEnd:
                    endFlag = True
                else:
                    runTrial = False
                    endTrial = core.getTime() - startTrial
                    if not self.stimPres:
                        self.endTrialSound.play()
                    #determine if they were looking or not at end of trial and update appropriate array
                    if gazeOn or gazeOn2:
                        if gazeOn:
                            onDur = endTrial - startOn
                            # Current format: Trial number, type, start of event, end of event, duration of event.
                            tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOn,
                                             'endTime': endTrial,
                                             'duration': onDur}
                            onArray.append(tempGazeArray)
                        if gazeOn2:
                            onDur2 = endTrial - startOn2
                            tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOn2,
                                             'endTime': endTrial,
                                             'duration': onDur2}
                            onArray2.append(tempGazeArray)
                    else:
                        offDur = endTrial - startOff
                        tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOff, 'endTime': endTrial,
                                         'duration': offDur}
                        offArray.append(tempGazeArray)
            elif not gazeOn and not gazeOn2: #if they are not looking as of the previous refresh, check if they have been looking away for too long
                nowOff = core.getTime() - startTrial
                if sumOn + sumOn2 > self.minOn[type] and nowOff - startOff >= self.maxOff[type] and self.playThrough[type] == 0 and not endFlag:
                    #if they have previously looked for at least .5s and now looked away for 2 continuous sec
                    if type in self.movieEnd:
                        endFlag = True
                    else:
                        runTrial = False
                        endTrial = core.getTime() - startTrial
                        if not self.stimPres:
                            self.endTrialSound.play()
                        endOff = nowOff
                        offDur = nowOff - startOff
                        tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOff, 'endTime': endOff,
                                         'duration': offDur}
                        offArray.append(tempGazeArray)
                elif self.keyboard[self.key.B]: #if they have started looking since the last refresh and not met criterion
                    gazeOn = True
                    numOn = numOn + 1
                    startOn = core.getTime() - startTrial
                    endOff = core.getTime() - startTrial
                    #by definition, if this is tripped there will be a preceding 'off' section if this is tripped because gazeOn is set at start
                    offDur = endOff - startOff
                    tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOff, 'endTime': endOff,
                                     'duration': offDur}
                    offArray.append(tempGazeArray)
                elif self.keyboard[self.key.M]: #if they have started looking since the last refresh and not met criterion
                    gazeOn2 = True
                    numOn2 = numOn2 + 1
                    startOn2 = core.getTime() - startTrial
                    endOff = core.getTime() - startTrial
                    #by definition, if this is tripped there will be a preceding 'off' section if this is tripped because gazeOn is set at start
                    offDur = endOff - startOff
                    tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOff, 'endTime': endOff,
                                     'duration': offDur}
                    offArray.append(tempGazeArray)
            elif gazeOn or gazeOn2:
                nowOn = core.getTime() - startTrial
                if gazeOn:
                    tempOn = startOn
                else:
                    tempOn = startOn2
                if self.playThrough[type] == 1 and sumOn + sumOn2 + (nowOn - tempOn) >= self.minOn[type] and not endFlag:
                    if type in self.movieEnd:
                        endFlag = True
                    else:
                        runTrial = False
                        endTrial = core.getTime() - startTrial
                        if not self.stimPres:
                            self.endTrialSound.play()
                        if gazeOn:
                            onDur = endTrial - startOn
                            tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOn, 'endTime': endTrial,
                                             'duration': onDur}
                            onArray.append(tempGazeArray)
                        if gazeOn2:
                            onDur = endTrial - startOn2
                            tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOn2, 'endTime': endTrial,
                                             'duration': onDur}
                            onArray2.append(tempGazeArray)
                if gazeOn and not self.keyboard[self.key.B]: #if they were looking and have looked away.
                    gazeOn = False
                    endOn = core.getTime() - startTrial
                    onDur = endOn - startOn
                    tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOn, 'endTime': endOn,
                                     'duration': onDur}
                    onArray.append(tempGazeArray)
                    sumOn = sumOn + onDur
                    if self.keyboard[self.key.M]:
                        gazeOn2 = True
                        numOn2 = numOn2 + 1
                        startOn2 = core.getTime() - startTrial
                    else:
                        numOff = numOff + 1
                        startOff = core.getTime() - startTrial
                if gazeOn2 and not self.keyboard[self.key.M]: #if they were looking and have looked away.
                    gazeOn2 = False
                    endOn2 = core.getTime() - startTrial2
                    onDur2 = endOn2 - startOn2
                    tempGazeArray2 = {'trial': number, 'trialType': type, 'startTime': startOn2, 'endTime': endOn2,
                                      'duration': onDur2}
                    onArray2.append(tempGazeArray2)
                    sumOn2 = sumOn2 + onDur2
                    if self.keyboard[self.key.B]:
                        gazeOn = True
                        numOn = numOn + 1
                        startOn = core.getTime() - startTrial
                    else:
                        numOff = numOff + 1
                        startOff = core.getTime() - startTrial
            movieStatus = self.dispTrial(type, disMovie)
            if type in self.movieEnd and endFlag and movieStatus >= 1:
                runTrial = False
                endTrial = core.getTime() - startTrial
                if not self.stimPres:
                    self.endTrialSound.play()
                # determine if they were looking or not at end of trial and update appropriate array
                if gazeOn:
                    onDur = endTrial - startOn
                    tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOn, 'endTime': endTrial,
                                             'duration': onDur}
                    onArray.append(tempGazeArray)
                if gazeOn2:
                    onDur = endTrial - startOn2
                    tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOn2, 'endTime': endTrial,
                                             'duration': onDur}
                    onArray2.append(tempGazeArray)
                else:
                    offDur = endTrial - startOff
                    tempGazeArray = {'trial': number, 'trialType': type, 'startTime': startOff, 'endTime': endTrial,
                                     'duration':offDur}
                    offArray.append(tempGazeArray)
        if self.stimPres:
            # Reset everything, stop playing sounds and movies.
            if disMovie['stimType'] == 'Movie':
                disMovie['stim'].seek(0)  # this is the reset, we hope.
                disMovie['stim'].pause()
            elif disMovie['stimType'] == 'Audio':
                disMovie['stim'].stop()
            elif disMovie['stimType'] == 'Image with audio':
                disMovie['stim']['Audio'].stop()
        self.statusSquareA.fillColor='black'
        self.statusSquareB.fillColor='black'
        self.statusTextA.text=""
        self.statusTextB.text=""
        self.statusSquareA.draw()
        self.statusSquareB.draw()
        if self.blindPres < 2:
            self.trialText.draw()
            if self.blindPres < 1:
                self.readyText.draw()
        self.win2.flip()
        if self.stimPres and number < len(self.actualTrialOrder):
            if self.actualTrialOrder[number] not in self.autoAdvance:
                self.win.flip() #blanks the screen outright if not auto-advancing
        if redo: #if the abort button was pressed
            self.abortTrial(onArray, offArray, number, type, onArray2, self.stimName)
            return 3
        else:
            self.dataRec(onArray, offArray, number, type, onArray2, self.stimName)

        if type == 'Hab': #if still during habituation
            #need to check based on number of HAB trial specifically
            if self.checkStop():
                return 1
            else:
                return 0
        elif number >= len(self.actualTrialOrder) or type == 4:
            #self.endExperiment()
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
        #sort the data matrices and shuffle them together.
        if len(self.badTrials) > 0: #if there are any redos, they need to be shuffled in appropriately.
            for i in range(0,len(self.badTrials)):
                x = 0
                while self.dataMatrix[x]['trial'] != self.badTrials[i]['trial']:
                    x += 1
                while self.dataMatrix[x]['GNG'] == 0: #this is to get around the possibility that the same trial had multiple 'false starts'
                    x += 1
                self.dataMatrix.insert(x, self.badTrials[i]) #python makes this stupid easy
        nDupe = ''  # This infrastructure eliminates the risk of overwriting existing data
        o = 1
        filename = self.dataFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + nDupe + '_' + str(self.today.month) + str(self.today.day) + str(self.today.year) + '.csv'
        while os.path.exists(filename):
            o += 1
            nDupe = str(o)
            filename = self.dataFolder + self.prefix + str(self.sNum) + '_' + str(self.sID) + nDupe + '_' + str(self.today.month) + str(self.today.day) + str(self.today.year) + '.csv'
        outputWriter = csv.DictWriter(open(filename,'w'),
                                      fieldnames = self.dataColumns, extrasaction='ignore', lineterminator ='\n') #careful! this OVERWRITES the existing file. Fills from snum.
        outputWriter.writeheader()
        for r in range(0, len(self.dataMatrix)):
            outputWriter.writerow(self.dataMatrix[r])
        #Now to construct and save verbose data
        verboseMatrix = []
        #first, verbose data is not as well organized. However, we should be able to alternate back and forth between
        #on and off until we reach the end of a given trial, to reconstruct it.
        #at the start of each line, add information: sNum, ageMo, ageDay, sex, cond, GNG, ON/OFF
        for n in range(0, len(self.verbDatList['verboseOn'])):
            self.verbDatList['verboseOn'][n].update({'snum': self.sNum, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex,
                                      'cond': self.cond, 'GNG': 1, 'gazeOnOff': 1})
        for m in range(0, len(self.verbDatList['verboseOff'])):  # adding the details to the verbose array
            self.verbDatList['verboseOff'][m].update(
                {'snum': self.sNum, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex,
                 'cond': self.cond, 'GNG': 1, 'gazeOnOff': 0})
        for o in range(0, len(self.verbDatList['verboseOn2'])):
            self.verbDatList['verboseOn2'][o].update({'snum': self.sNum, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex,
                                      'cond': self.cond, 'GNG': 1, 'gazeOnOff': 2})
        if len(self.badTrials) > 0:
            for p in range(0, len(self.verbBadList['verboseOn'])):
                self.verbBadList['verboseOn'][p].update(
                    {'snum': self.sNum, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex,
                     'cond': self.cond, 'GNG': 0, 'gazeOnOff': 1})
            for q in range(0, len(self.verbBadList['verboseOff'])):  # same details for the bad trials
                self.verbBadList['verboseOff'][q].update(
                    {'snum': self.sNum, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex,
                     'cond': self.cond, 'GNG': 0, 'gazeOnOff': 0})
            for r in range(0, len(self.verbBadList['verboseOn2'])):
                self.verbBadList['verboseOn2'][r].update(
                    {'snum': self.sNum, 'months': self.ageMo, 'days': self.ageDay, 'sex': self.sex,
                     'cond': self.cond, 'GNG': 0, 'gazeOnOff': 2})
        #read the final data matrix and go trial by trial.
        #print(verboseOn) #debug, to make sure verboseOn is being constructed correctly
        for q in range(0, len(self.dataMatrix)):
            tnum = self.dataMatrix[q]['trial']
            onIndex = -1
            onIndex2 = -1
            offIndex = -1
            if self.dataMatrix[q]['GNG'] == 1: #separate for good and bad trials
                for x in range(0, len(self.verbDatList['verboseOn'])):
                    if self.verbDatList['verboseOn'][x]['trial'] == tnum and onIndex == -1: #find the right index in the verbose matrices
                        onIndex = x
                for y in range(0, len(self.verbDatList['verboseOff'])):
                    if self.verbDatList['verboseOff'][y]['trial'] == tnum and offIndex == -1:
                        offIndex = y
                for z in range(0, len(self.verbDatList['verboseOn2'])):
                    if self.verbDatList['verboseOn2'][z]['trial'] == tnum and onIndex2 == -1: #find the right index in the verbose matrices
                        onIndex2 = z
                trialVerbose = []
                if onIndex >= 0:
                    while onIndex < len(self.verbDatList['verboseOn']):
                        if self.verbDatList['verboseOn'][onIndex]['trial'] == tnum:
                            trialVerbose.append(self.verbDatList['verboseOn'][onIndex])
                        onIndex += 1
                if onIndex2 >= 0:
                    while onIndex2 < len(self.verbDatList['verboseOn2']):
                        if self.verbDatList['verboseOn2'][onIndex2]['trial'] == tnum:
                            trialVerbose.append(self.verbDatList['verboseOn2'][onIndex2])
                        onIndex2 += 1
                if offIndex >= 0:
                    while offIndex < len(self.verbDatList['verboseOff']):
                        if self.verbDatList['verboseOff'][offIndex]['trial']==tnum:
                            trialVerbose.append(self.verbDatList['verboseOff'][offIndex])
                        offIndex += 1
                trialVerbose2 = sorted(trialVerbose, key=lambda trialVerbose:trialVerbose['startTime']) #this is the magic bullet, in theory.
                verboseMatrix.extend(trialVerbose2)
            elif self.dataMatrix[q]['GNG']==0: #bad trials.
                if q > 0 and self.dataMatrix[q-1]['GNG']==0:
                    pass #stops it from doubling up. If there is more than one consecutive bad trial, it will get all of them in a row the first time,
                else:
                    trialVerbose = []
                    for x in range(0,len(self.verbBadList['verboseOn'])):
                        if self.verbBadList['verboseOn'][x]['trial'] == tnum and onIndex == -1:
                            onIndex = x
                    for y in range(0, len(self.verbBadList['verboseOff'])):
                        if self.verbBadList['verboseOff'][y]['trial'] == tnum and offIndex == -1:
                            offIndex = y
                    for z in range(0, len(self.verbDatList['verboseOn2'])):
                        if self.verbDatList['verboseOn2'][z]['trial'] == tnum and onIndex2 == -1: #find the right index in the verbose matrices
                            onIndex2 = z
                    if onIndex >= 0:
                        while onIndex < len(self.verbBadList['verboseOn']):
                            if self.verbBadList['verboseOn'][onIndex]['trial'] == tnum:
                                trialVerbose.append(self.verbBadList['verboseOn'][onIndex])
                            onIndex += 1
                    if onIndex2 >= 0:
                        while onIndex2 < len(self.verbBadList['verboseOn2']):
                            if self.verbBadList['verboseOn2'][onIndex2]['trial'] == tnum:
                                trialVerbose.append(self.verbBadList['verboseOn2'][onIndex2])
                            onIndex2 += 1
                    if offIndex >=0:
                        while offIndex < len(self.verbBadList['verboseOff']):
                            if self.verbBadList['verboseOff'][offIndex]['trial']==tnum:
                                trialVerbose.append(self.verbBadList['verboseOff'][offIndex])
                            offIndex += 1
                    trialVerbose2 = sorted(trialVerbose, key=lambda trialVerbose:trialVerbose['startTime']) #this is the magic bullet, in theory.
                    verboseMatrix.extend(trialVerbose2)
        headers2 = ['snum', 'months', 'days', 'sex', 'cond', 'GNG', 'gazeOnOff', 'trial', 'trialType',
                                'startTime', 'endTime', 'duration']
        outputWriter2 = csv.DictWriter(open(self.dataFolder+self.prefix+str(self.sNum)+'_'+str(self.sID)+nDupe+'_'+str(self.today.month)+str(self.today.day)+str(self.today.year)+'_VERBOSE.csv','w'),
                                       fieldnames = headers2, extrasaction = 'ignore', lineterminator ='\n') #careful! this OVERWRITES the existing file. Fills from snum.
        outputWriter2.writeheader()
        for z in range(0,len(verboseMatrix)):
            outputWriter2.writerow(verboseMatrix[z])
        core.wait(.3)
        self.win2.close()
        if self.stimPres:
            self.win.close()