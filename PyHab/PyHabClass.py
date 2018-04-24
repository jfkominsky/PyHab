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
#PyHab + stimulus control system
#Jonathan Kominsky, 2016-2018
#Keyboard coding: A = ready, B = coder 1 on, L = coder 2 on, R = abort trial, Y = end experiment (for fussouts)
#Between-trials: R = redo previous trial, J = jump to test trial, I = insert additional habituation trial (hab only)

class pyHab():
    
    def __init__(self, settingsDict): #Instead of taking each thing manually, it now just takes all of the settings as a dict.
        if os.name is 'posix': #glorious simplicity of unix filesystem
            self.dirMarker = '/'
            otherOS = '\\'
        elif os.name is 'nt': #Nonsensical Windows-based contrarianism
            self.dirMarker='\\'
            otherOS = '/'
        self.dataColumns = eval(settingsDict['dataColumns'])
        self.prefix=settingsDict['prefix'] #prefix for data files. All data filenames will start with this text.
        self.dataFolder=settingsDict['dataloc']  #datafolder, condpath,moviepath are the ones that need modification.
        if len(self.dataFolder) > 0 and self.dataFolder[-1] is not self.dirMarker:
            self.dataFolder=[self.dirMarker if x==otherOS else x for x in self.dataFolder]
            self.dataFolder=''.join(self.dataFolder)
        
        #UNIVERSAL SETTINGS
        self.maxDur = eval(settingsDict['maxDur']) #maximum number of seconds in a trial - can be a constant or a dictionary with different times for EACH trial type (must include every type). {'A':20,'B':60} etc.
        self.playThrough= eval(settingsDict['playThrough']) #A dict which informs what kind of gaze-contingency each trial type follows.
        self.movieEnd = eval(settingsDict['movieEnd']) #A list of trial types that only end (in stim pres mode) on the end of the movie file associated with them.
        self.maxOff = eval(settingsDict['maxOff']) #maximum number of consecutive seconds of offtime to end trial
        self.minOn = eval(settingsDict['minOn']) #minimum on-time for a trial (seconds)
        self.blindPres = eval(settingsDict['blindPres']) #0, 1, or 2. 0 = show everything. 1 = show trial number + status squares. 2 = no trial #, status squares do not indicate on/off
        self.autoAdvance =  eval(settingsDict['autoAdvance'])#For creating studies where you don't want a lag between trials, just automatic advancement to the next.
        self.randPres= eval(settingsDict['randPres']) #controls whether the program will look for an external randomization file to determine presentation order
        #If not, hab will present the first thing in each of the lists above, and VoE will just go through the lists in order
        self.condPath = settingsDict['condPath'] #path for the condition file.
        self.condFile = settingsDict['condFile']#if you have a condition file, put filename here (WITH EXTENSION). Must be .csv
        self.condList = eval(settingsDict['condList'])#list of conditions for the dropdown menu, if using random presentation.[SOON: GET AUTOMATICALLY FROM FILE]
        if len(self.condPath) > 0 and self.condPath[-1] is not self.dirMarker:
            self.condPath=[self.dirMarker if x==otherOS else x for x in self.condPath]
            self.condPath=''.join(self.condPath)
        
        #ORDER OF PRESENTATION
        #NOTE: a SINGLE instance of 'Hab' will insert a contiguous habituation BLOCK of up to maxHabTrials.
        #Recommend you make sure repetitions of each trial type is a multiple of the list length, if you want even presentation
        self.trialOrder=eval(settingsDict['trialOrder'])
        
        #HABITUATION DESIGN SETTINGS
        self.maxHabTrials = eval(settingsDict['maxHabTrials']) #number of habituation trials in a HAB design
        self.setCritWindow = eval(settingsDict['setCritWindow']) #Number of trials to use when setting the habituation window, e.g., 3 = first three hab trials
        self.setCritDivisor = eval(settingsDict['setCritDivisor']) #Divide sum of looking time over first setHabWindow trials by this value. for average, set equal to setHabWindow. For sum, set to 1.
        self.metCritWindow = eval(settingsDict['metCritWindow']) #size of moving window of trials to sum looking times and compare to habituation criterion. 
        self.metCritDivisor = eval(settingsDict['metCritDivisor'])#If you want to compare, e.g., average rather than sum of looking times of last metCritWindow trials, change this accordingly.
        self.habTrialList = eval(settingsDict['habTrialList']) #A new "meta-hab" trial type consisting of several sub-trial-types.

        #STIMULUS PRESENTATION SETTINGS
        self.stimPres = eval(settingsDict['stimPres']) #For determining if the program is for stimulus presentation (True) or if it's just coding looking times (False)
        if not self.stimPres:
            self.movieEnd = [] #So we don't run into trouble with trials not ending waiting for movies that don't exist.
        self.moviePath = settingsDict['moviePath'] #Folder where movie files can be located (if not in same folder as script)
        #A list of trial types. One is special: 'Hab' (only plays first entry), which should only be used for a habituation block in which you have a variable number of trials depending on a habituation criterion
        self.movieNames = eval(settingsDict['movieNames'])
        self.movieExt = settingsDict['movieExt']
        #File extension/movie type. Multiple types? No problem, just make this '' and put the extensions in the movienames.
        self.screenWidth = eval(settingsDict['screenWidth']) #Display window width, in pixels
        self.screenHeight = eval(settingsDict['screenHeight']) #Display window height, in pixels
        self.movieWidth =  eval(settingsDict['movieWidth'])#movie width
        self.movieHeight =  eval(settingsDict['movieHeight'])#movie height
        self.screenIndex = eval(settingsDict['screenIndex']) #which monitor stimuli are presented on. 1 for secondary monitor, 0 for primary monitor.
        self.ISI = eval(settingsDict['ISI']) #time between loops (in seconds, if desired)
        self.freezeFrame = eval(settingsDict['freezeFrame']) #time that movie remains on first frame at start of trial.
        self.playAttnGetter = eval(settingsDict['playAttnGetter']) #if you want to use the built-in attention-getter, use this. Otherwise set to False.
        if len(self.moviePath) > 0 and self.moviePath[-1] is not self.dirMarker:
            self.moviePath=[self.dirMarker if x==otherOS else x for x in self.moviePath]
            self.moviePath=''.join(self.moviePath)
        '''
        END SETTINGS
        '''
        self.habCount = 0 #For hab designs, checks the # of habituation trials completed
        self.habCrit = 0 #initial setting of habcrit at 0
        self.dataMatrix = [] #primary data array 
        #data format: snum, age in months, age in days, sex, condition, trial, GNGtrial, trial type, hab crit, on-time, number of gazes, off-time, number of look-offs
        #then same again at the end for b-coder?
        self.badTrials=[] # data array for bad trials
        self.verboseOn=[] #"verbose" data aray for gazes on, that includes each individual gaze, when it happened, etc.
        self.verboseOff=[] #same for off-time
        self.verboseOn2=[] #for coder B. Can't assume that they will line up in terms of number of gazes so can't put them in same file.
        self.verboseOff2=[] #for coder B.
        self.badVerboseOn=[] #same as above but for bad trials
        self.badVerboseOff=[] #same as above but for bad trials
        self.badVerboseOn2=[]
        self.badVerboseOff2=[]
        if not self.stimPres:
            #global endTrialSound, endHabSound
            self.endTrialSound=sound.Sound('A',octave=4, sampleRate=44100, secs=0.2)
            self.endHabSound=sound.Sound('G',octave=4, sampleRate=44100, secs=0.2)
        elif len(self.playAttnGetter)>0:
            #global HeyListen
            self.HeyListen =sound.Sound('upchime1.wav',secs=3) #will become attn-getter
        if type(self.maxDur) is int: #Secretly MaxDur will always be a dict, but if it's a constant we just create the dict here
            #global tempDur
            tempDur = self.maxDur
            self.maxDur = {} #create a dict
            #look up unique names in trialOrder to get all the trial types
            for x in self.trialOrder:
                self.maxDur[x] = tempDur #Python: Yes, it really is that easy. 
        self.statusOffset = 0
        self.statusOffsetY = 0
        self.testOffset = 0
        self.frameCount = 0 #the frame counter for the movement of A and B, based on the refresh rate. 
        self.pauseCount = 0 #used for ISI calculations
        self.stimName='' #used for adding the name of the stimulus file to the output.
    '''
    FUNCTIONS
    '''
    def abortTrial(self, onArray, offArray, trial, ttype, onArray2, offArray2,stimName=''): #the 2nd arrays are if there are two coders.
        #only happens when the 'abort' button is pressed. In the main trial loop we can not advance the trial number, this mostly 
        #serves to create a separate data array of bad trials that we can incorporate later
        sumOn = 0
        sumOff = 0
        if ttype == 'Hab':
            #global habCount
            self.habCount -= 1
        for i in range(0,len(onArray)):
            sumOn = sumOn + onArray[i][4]
        for j in range(0,len(offArray)):
            sumOff = sumOff + offArray[j][4]
        #needs to be .extend or you get weird array-within-array-within-array issues that become problematic later
        self.badVerboseOn.extend(onArray)
        self.badVerboseOff.extend(offArray)
        sumOn2=0
        sumOff2=0
        if len(onArray2) > 0 or len(offArray2) > 0:
            for i in range(0,len(onArray2)):
                sumOn2 = sumOn2 + onArray2[i][4]
            for j in range(0,len(offArray2)):
                sumOff2 = sumOff2 + offArray2[j][4]
            self.badVerboseOn2.extend(onArray2)
            self.badVerboseOff2.extend(offArray2)
        #data format: snum, age in months, age in days, sex, condition, trial, GNGtrial, trial type, hab crit, on-time, number of gazes, off-time, number of look-offs
        #then same again at the end for b-coder
        #tempData=[sNum, ageMo, ageDay, sex, cond, trial, 0, ttype, habCrit, sumOn, len(onArray), sumOff, len(offArray),sumOn2, len(onArray2), sumOff2, len(offArray2)]
        tempData={'sNum':self.sNum, 'months':self.ageMo, 'days':self.ageDay, 'sex':self.sex, 'cond':self.cond,'condLabel':self.condLabel, 
                                'trial':trial, 'GNG':0, 'trialType':ttype, 'stimName':stimName, 'habCrit':self.habCrit, 
                                'sumOnA':sumOn, 'numOnA':len(onArray), 'sumOffA':sumOff, 'numOffA':len(offArray),
                                'sumOnB':sumOn2,'numOnB':len(onArray2),'sumOffB':sumOff2,'numOffB':len(offArray2)}
        self.badTrials.append(tempData)
    
    def dataRec(self,onArray,offArray,trial,type,onArray2,offArray2,stimName=''):
        #global habCrit
        sumOn = 0
        sumOff = 0
        #loop through each array adding up gaze duration (on and off).
        for i in range(0,len(onArray)):
            sumOn = sumOn + onArray[i][4]
        for j in range(0,len(offArray)):
            sumOff = sumOff + offArray[j][4]
        sumOn2 = 0
        sumOff2 = 0
        if len(offArray2)>0 or len(onArray2)>0:
            for i in range(0,len(onArray2)):
                sumOn2 = sumOn2 + onArray2[i][4]
            for j in range(0,len(offArray2)):
                sumOff2 = sumOff2 + offArray2[j][4]
            self.verboseOn2.extend(onArray2)
            self.verboseOff2.extend(offArray2)
        #add to verbose master gaze array
        self.verboseOn.extend(onArray)
        self.verboseOff.extend(offArray)
        #data format: snum, age in months, age in days, sex, condition, trial, GNGtrial, trial type, hab crit, on-time, number of gazes, off-time, number of look-offs, same again for B-coder
        #then same again at the end for b-coder?
        #tempData=[sNum, ageMo, ageDay, sex, cond, trial, 1, type, habCrit, sumOn, len(onArray), sumOff, len(offArray),sumOn2,len(onArray2),sumOff2,len(offArray2)]
        tempData={'sNum':self.sNum, 'months':self.ageMo, 'days':self.ageDay, 'sex':self.sex, 'cond':self.cond,'condLabel':self.condLabel, 
                                'trial':trial, 'GNG':1, 'trialType':type, 'stimName':stimName, 'habCrit':self.habCrit, 
                                'sumOnA':sumOn, 'numOnA':len(onArray), 'sumOffA':sumOff, 'numOffA':len(offArray),
                                'sumOnB':sumOn2,'numOnB':len(onArray2),'sumOffB':sumOff2,'numOffB':len(offArray2)}
        self.dataMatrix.append(tempData)
    
    def redoTrial(self,trialNum):
        #basically abort trial but after the fact
        #This will only come up if the last trial is good. If the last trial was aborted and this is called, it will hit the trial before THAT.
        #so, only need to find the trial in dataMatrix
        #print 'redoTrial Active!'
        newTempData={}
        i = 0
        while i < len(self.dataMatrix):
            if self.dataMatrix[i]['trial'] == trialNum:
                trialIndex = i
                newTempData= self.dataMatrix[i]
                #print newTempData
                i+=1
            else:
                i+=1
        #add the new 'bad' trial to badTrials
        #print 'it is now ' + str(newTempData)
        newTempData['GNG'] = 0
        if newTempData['trialType'] == 'Hab':
            #global habCount
            self.habCount -= 1
        self.badTrials.append(newTempData)
        #remove it from dataMatrix
        self.dataMatrix.remove(self.dataMatrix[trialIndex])
        #now for the hard part: shifting the verbose data!
        #basically need to read through the verbose matrices, add everything that references that trial to BadVerboseOn, and mark the relevant lines for later deletion
        for i in range(0, len(self.verboseOn)):
            if self.verboseOn[i][0] == trialNum:
                self.badVerboseOn.append(self.verboseOn[i][:])
                self.verboseOn[i][0] = 99
        for j in range(0, len(self.verboseOff)):
            if self.verboseOff[j][0] == trialNum:
                self.badVerboseOff.append(self.verboseOff[j][:])
                self.verboseOff[j][0] = 99
        #need to do deletions separately because we keep changing the index every time we remove something.
        k = 0
        l = 0
        while k < len(self.verboseOn):
            if self.verboseOn[k][0] == 99:
                self.verboseOn.remove(self.verboseOn[k]) #since this removes the entire index, then we should not advance because the next line will come up.
            else:
                k+=1
        while l < len (self.verboseOff):
            if self.verboseOff[l][0] == 99:
                self.verboseOff.remove(self.verboseOff[l])
            else:
                l += 1
        #and then we need to look at the second coder too...
        if len(self.verboseOn2) > 0: 
            for i in range(0, len(self.verboseOn2)):
                if self.verboseOn2[i][0] == trialNum:
                    self.badVerboseOn2.append(self.verboseOn2[i][:])
                    self.verboseOn2[i][0] = 99
            for j in range(0, len(self.verboseOff2)):
                if self.verboseOff2[j][0] == trialNum:
                    self.badVerboseOff2.append(self.verboseOff2[j][:])
                    self.verboseOff2[j][0] = 99
            m=0
            n=0
            while m < len(self.verboseOn2):
                if self.verboseOn2[m][0] == 99:
                    self.verboseOn2.remove(self.verboseOn2[m])
                else:
                    m += 1
            while n < len(self.verboseOff2):
                if self.verboseOff2[n][0] == 99:
                    self.verboseOff2.remove(self.verboseOff2[n])
                else:
                    n += 1
    
    def checkStop(self,trial,numHab):
        #checks the habitution criteria and returns 'true' if any of them are met.
        #global habCrit #python is weird about scope. this ensures that we are using the experiment-wide habCrit variable
        if numHab == self.setCritWindow: #time to set the hab criterion.
            sumOnTimes = 0
            #find first hab trial
            x = 0
            for j in range(0,len(self.dataMatrix)):
                if self.dataMatrix[j]['trialType'] == 'Hab':
                    x = j
                    break
            for k in range(x, len(self.dataMatrix)):
                if self.dataMatrix[k]['GNG'] == 1 and self.dataMatrix[k]['trialType'] == 'Hab': #just in case there are any bad trials, we don't want to incorporate them into setting the criterion
                    sumOnTimes = sumOnTimes + self.dataMatrix[k]['sumOnA'] #add up total looking time for first three (good) trials
            self.habCrit = sumOnTimes/self.setCritDivisor
        elif self.habCount == self.maxHabTrials:
            #end habituation and goto test
            return True
        elif numHab >= self.setCritWindow + self.metCritWindow: #if we're far enough in that we can plausibly meet the hab criterion
            sumOnTimes = 0
            habs = [i for i, x in enumerate(self.actualTrialOrder) if x == 'Hab'] #list of all habs
            habs.sort()
            index = habs[len(habs)-self.metCritWindow-1]
            for n in range(index, len(self.dataMatrix)): #now, starting with that trial, go through and add up the good trial looking times
                if self.dataMatrix[n]['GNG'] == 1 and self.dataMatrix[n]['trialType'] == 'Hab': #only good trials!
                    sumOnTimes = sumOnTimes + self.dataMatrix[n]['sumOnA'] #add up total looking time
                sumOnTimes=sumOnTimes/self.metCritDivisor
            if sumOnTimes < self.habCrit:
                #end habituation and go to test
                if not self.stimPres:
                    for i in [0, 1, 2]:
                        core.wait(.25) #an inadvertent side effect of this is a short pause before the test trial can begin
                        self.endHabSound.play()
                return True
            else:
                return False
        else:
            return False
    
    def attnGetter(self): #an animation and sound to be called whenever an attentiongetter is needed
         self.HeyListen.play() #add ability to customize?
         x=0
         self.attnGetterSquare.ori=0
         self.attnGetterSquare.fillColor='yellow'
         for i in range(0, 60): #a 1-second animation
             self.attnGetterSquare.ori+=5
             x +=.1
             self.attnGetterSquare.height=sin(x)*120
             self.attnGetterSquare.width=tan(.25*x)*120
             self.attnGetterSquare.draw()
             self.win.flip()
         self.statusSquareA.fillColor='blue'
         if self.blindPres < 2:
             self.statusTextA.text="RDY"
         self.statusSquareA.draw()
         self.statusTextA.draw()
         if self.blindPres <2:
             self.trialText.draw()
             if self.blindPres < 1:
                self.readyText.draw()
         if self.verbose:
             self.statusSquareB.fillColor='blue'
             if self.blindPres < 2:
                 self.statusTextB.text="RDY"
             self.statusSquareB.draw()
             self.statusTextB.draw()
         self.win2.flip()
         if self.stimPres:
             self.win.flip() #clear screen
    
    def dispTrial(self, trialType,dispMovie=False): #if stimPres = false, so too dispMovie.
        '''
        Draws each frame of the trial. For stimPres situation, returns a movie-status value

        :param trialType: Current trial type
        :type trialType: String
        :param dispMovie: Movie file for stimulus presentation (if applicable)
        :type dispMovie: Bool or movieStim3 object.
        :return:
        :rtype:
        '''
        #first, let's just get the status squares out of the way.
        if self.keyboard[self.key.B] and self.blindPres < 2:
            self.statusSquareA.fillColor='green'
            self.statusTextA.text="ON"
        elif trialType==0 and self.blindPres < 2:
            self.statusSquareA.fillColor='blue'
            self.statusTextA.text="RDY"
        elif self.blindPres < 2:
            self.statusSquareA.fillColor='red'
            self.statusTextA.text="OFF"
        else:
            self.statusSquareA.fillColor='blue'
            self.statusTextA.text=""
        self.statusSquareA.draw()
        self.statusTextA.draw()
        if self.blindPres<2:
            self.trialText.draw()
            if self.blindPres < 1:
                self.readyText.draw()
        if self.verbose: 
            if self.keyboard[self.key.L] and self.blindPres < 2:
                self.statusSquareB.fillColor='green'
                self.statusTextB.text="ON"
            elif trialType==0 and self.blindPres < 2:
                self.statusSquareB.fillColor='blue'
                self.statusTextB.text="RDY"
            elif self.blindPres < 2:
                self.statusSquareB.fillColor='red'
                self.statusTextB.text="OFF"
            else:
                self.statusSquareB.fillColor='blue'
                self.statusTextB.text=""
            self.statusSquareB.draw()
            self.statusTextB.draw()
        self.win2.flip() #flips the status screen without delaying the stimulus onset.
        #now for the test trial display
        if self.stimPres:
            if self.frameCount == 0: #initial setup
                dispMovie.draw()
                self.frameCount+=1
                if trialType == 0:
                    self.frameCount=0 # for attn-getter
                    dispMovie.pause()
                self.win.flip()
                return 0
            elif self.frameCount == 1:
                #print('playing')
                dispMovie.play()
                dispMovie.draw()
                self.frameCount+=1
                self.win.flip()
                return 0
            elif dispMovie.getCurrentFrameTime() >= dispMovie.duration-.05 and self.pauseCount< self.ISI*60: #pause, check for ISI.
                dispMovie.pause()
                dispMovie.draw() #might want to have it vanish rather than leave it on the screen for the ISI, in which case comment out this line.
                self.frameCount += 1
                self.pauseCount += 1
                self.win.flip()
                return 1
            elif dispMovie.getCurrentFrameTime() >= dispMovie.duration-.05 and self.pauseCount >= self.ISI*60: #MovieStim's Loop functionality can't do an ISI
                #print('repeating at ' + str(dispMovie.getCurrentFrameTime()))  
                self.frameCount = 0 #changed to 0 to better enable studies that want to blank between trials
                self.pauseCount = 0
                dispMovie.draw() # Comment this out as well to blank between loops.
                self.win.flip()
                dispMovie.seek(0)
                return 1
            else:
                dispMovie.draw()
                self.frameCount+= 1
                self.win.flip()
                return 0
        else:
            return 0 #Totally irrelevant.
    
    def doExperiment(self):
        #the primary control function and main trial loop.
#        global frameCount 
#        global stimName
        self.statusSquareA.draw()
        self.statusTextA.draw()
        self.currTestTrial=0
        if self.verbose:
            self.statusSquareB.draw()
            self.statusTextB.draw()
        #primary trial loop, go until end of exp.
        runExp = True
        trialNum = 1
        self.trialText.text="Trial no. " + str(trialNum)
        self.readyText.text="Before first trial"
        self.rdyTextAppend=""
        #win.flip()
        trialType = self.actualTrialOrder[0]
        if self.blindPres<1:
            self.rdyTextAppend = " NEXT: " + trialType + " TRIAL"
        didRedo = False
        self.readyText.draw()
        self.win2.flip()
        AA = [] #a localized autoadvance to allow for first trial
        while runExp:
            reviewed = False
            self.trialText.text="Trial no. " + str(trialNum)
            self.statusSquareA.fillColor='black'
            self.statusSquareB.fillColor='black'
            #select movie for trial
            if self.stimPres:
                disMovie= self.movieDict[self.actualTrialOrder[trialNum-1]][self.counters[self.actualTrialOrder[trialNum-1]]] 
                self.counters[self.actualTrialOrder[trialNum-1]]+=1
                if self.counters[self.actualTrialOrder[trialNum-1]] >= len(self.movieDict[self.actualTrialOrder[trialNum-1]]):
                    self.counters[self.actualTrialOrder[trialNum-1]] = 0
                self.stimName=disMovie.filename[len(self.moviePath):len(disMovie.filename)-len(self.movieExt)]
            else:
                disMovie = 0
            if self.blindPres < 1:
                self.rdyTextAppend = " NEXT: " + self.actualTrialOrder[trialNum-1] + " TRIAL"
            while not self.keyboard[self.key.A] and trialType not in AA: #wait for 'ready' key, check at frame intervals
                self.statusSquareA.draw()
                self.readyText.text="No trial active" + self.rdyTextAppend
                if self.blindPres < 2:
                    self.trialText.draw()
                self.readyText.draw()
                if self.verbose:
                    self.statusSquareB.draw()
                if self.keyboard[self.key.Y]:
                    self.endExperiment([[0,0,0,0,0]],[[0,0,0,0,0]],trialNum,trialType,[],[],self.stimName) #takes a bunch of arrays so we feed it blanks
                    core.quit()
                elif self.keyboard[self.key.R] and not didRedo:
                    if trialNum >1:
                        trialNum -= 1
                        self.trialText.text="Trial no. " + str(trialNum)
                        trialType = self.actualTrialOrder[trialNum-1]
                        if self.blindPres < 1:
                            self.rdyTextAppend = " NEXT: " + trialType + " TRIAL"
                        if self.stimPres:
                            disMovie= self.movieDict[self.actualTrialOrder[trialNum-1]][self.counters[self.actualTrialOrder[trialNum-1]]] 
                            self.counters[self.actualTrialOrder[trialNum-1]]+=1
                            if self.counters[self.actualTrialOrder[trialNum-1]] >= len(self.movieDict[self.actualTrialOrder[trialNum-1]]):
                                self.counters[self.actualTrialOrder[trialNum-1]] = 0
                            self.stimName=disMovie.filename[len(self.moviePath):len(disMovie.filename)-len(self.movieExt)]
                        else:
                            disMovie = 0
                    self.redoTrial(trialNum)
                    didRedo = True
                elif self.keyboard[self.key.J] and trialType == 'Hab': #jump to test in a hab design
                    habs = [i for i, x in enumerate(self.actualTrialOrder) if x == 'Hab']
                    tempNum = max(habs)
                    #trialNum is in fact the index after the current trial at this point
                    #so we can just erase everything between that and the first non-hab trial.
                    del self.actualTrialOrder[trialNum-1:tempNum]
                    trialType = self.actualTrialOrder[trialNum-1]
                    if self.stimPres:
                        disMovie= self.movieDict[self.actualTrialOrder[trialNum-1]][self.counters[self.actualTrialOrder[trialNum-1]]] 
                        self.counters[self.actualTrialOrder[trialNum-1]]+=1
                        if self.counters[self.actualTrialOrder[trialNum-1]] >= len(self.movieDict[self.actualTrialOrder[trialNum-1]]):
                            self.counters[self.actualTrialOrder[trialNum-1]] = 0
                        self.stimName=disMovie.filename[len(self.moviePath):len(disMovie.filename)-len(self.movieExt)]
                    else:
                        disMovie = 0
                    if self.blindPres < 1:
                        self.rdyTextAppend=" NEXT: "+ trialType +" TRIAL"
                elif trialType != 'Hab' and self.keyboard[self.key.I] and 'Hab' in self.trialOrder: #insert additional hab trial
                    #literally insert a new trial into actualTrialOrder, get the right movie, etc.
                    if len(self.habTrialList) > 0:
                        for z in range(0, len(self.habTrialList)):
                            self.actualTrialOrder.insert(trialNum - 1 + z, self.habTrialList[z])
                    else:
                        self.actualTrialOrder.insert(trialNum - 1, 'Hab')
                    trialType = self.actualTrialOrder[trialNum -1]
                    if self.stimPres:
                        disMovie= self.movieDict[self.actualTrialOrder[trialNum-1]][self.counters[self.actualTrialOrder[trialNum-1]]] 
                        self.counters[self.actualTrialOrder[trialNum-1]]+=1
                        if self.counters[self.actualTrialOrder[trialNum-1]] >= len(self.movieDict[self.actualTrialOrder[trialNum-1]]):
                            self.counters[self.actualTrialOrder[trialNum-1]] = 0
                            self.stimName=disMovie.filename[len(self.moviePath):len(disMovie.filename)-len(self.movieExt)]
                    else:
                        disMovie = 0
                    if self.blindPres < 1:
                        self.rdyTextAppend=" NEXT: "+ trialType +" TRIAL"
                elif trialNum > 1 and not self.stimPres and self.keyboard[self.key.P] and not reviewed: #Print data so far, as xHab. Non-stimulus version only. Only between trials.
                    reviewed = True
                    print("hab crit, on-timeA, numOnA, offtimeA, numOffA, onTimeB, numOnB, offTimeB, numOffB")
                    print("-------------------------------------------------------------------------------------------")
                    for i in range(0, len(self.dataMatrix)): 
                        dataList = [self.dataMatrix[i]['habCrit'],self.dataMatrix[i]['sumOnA'],self.dataMatrix[i]['numOnA'],self.dataMatrix[i]['sumOffA'],self.dataMatrix[i]['numOffA'],self.dataMatrix[i]['sumOnB'],self.dataMatrix[i]['numOnB'],self.dataMatrix[i]['sumOffB'],self.dataMatrix[i]['numOffB']]
                        print(dataList) 
                self.win2.flip()
            self.frameCount = 0
            #framerate = win.getActualFrameRate() 
            #print(framerate)               #just some debug code.
            if trialType not in AA and self.blindPres < 2:
                self.statusSquareA.fillColor='blue'
                self.statusTextA.text="RDY"
                self.statusSquareA.draw()
                self.statusTextA.draw()
                self.trialText.draw()
                self.readyText.text="Trial active"
                self.readyText.draw()
                if self.verbose:
                    self.statusSquareB.fillColor='blue'
                    self.statusTextB.text="RDY"
                    self.statusSquareB.draw()
                    self.statusTextB.draw()
                self.win2.flip()
            if self.stimPres:
                if trialType in self.playAttnGetter:
                    self.attnGetter() #plays the attention-getter
                    core.wait(.1) #this wait is important to make the attentiongetter not look like it is turning into the stimulus
                    self.frameCount=0
                    irrel = self.dispTrial(0,disMovie)
                    core.wait(self.freezeFrame) #this delay ensures that the trial only starts after the images have appeared on the screen, static, for 200ms
                    waitStart = True
                else:
                    self.frameCount = 0
                    waitStart=False
            else:
                if trialType in self.playAttnGetter:
                    core.wait(.2+self.freezeFrame) #an attempt to match the delay caused by the attention-getter playing.
                    waitStart = True
                else:
                    waitStart = False
            while waitStart and trialType not in AA:
                if self.keyboard[self.key.Y]: #End experiment right there and then.
                    self.endExperiment([[0,0,0,0,0]],[[0,0,0,0,0]],trialNum,trialType,[],[],self.stimName) 
                    core.quit()
                elif self.keyboard[self.key.A]:
                    if self.stimPres:
                        if trialType in self.playAttnGetter:
                            self.attnGetter()
                            core.wait(.1)
                        irrel = self.dispTrial(0,disMovie)
                        core.wait(self.freezeFrame)
                    else:
                        core.wait(.2 + self.freezeFrame)
                elif self.keyboard[self.key.B]:
                    waitStart = False
                    if self.blindPres < 2:
                        self.statusSquareA.fillColor='green'
                        self.statusTextA.text="ON"
                    self.statusSquareA.draw()
                    self.statusTextA.draw()
                    if self.blindPres < 2:
                        self.trialText.draw()
                        if self.blindPres < 1:
                            self.readyText.draw()
                    if self.verbose:
                        if self.keyboard[self.key.L] and self.blindPres < 2: 
                            self.statusSquareB.fillColor='green'
                            self.statusTextB.text="ON"
                        elif self.blindPres < 2:
                            self.statusSquareB.fillColor='red'
                            self.statusTextB.text="OFF"
                        self.statusSquareB.draw()
                        self.statusTextB.draw()
                    self.win2.flip()
                elif self.keyboard[self.key.R] and not didRedo: #Redo last trial, mark last trial as bad
                    if trialNum > 1:
                        trialNum -= 1
                        self.trialText.text="Trial no. " + str(trialNum)
                        trialType = self.actualTrialOrder[trialNum-1]
                        if self.blindPres < 1:
                            self.rdyTextAppend = " NEXT: " + trialType + " TRIAL"
                        if self.stimPres:
                            disMovie= self.movieDict[self.actualTrialOrder[trialNum-1]][self.counters[self.actualTrialOrder[trialNum-1]]] 
                            self.counters[self.actualTrialOrder[trialNum-1]]+=1
                            if self.counters[self.actualTrialOrder[trialNum-1]] >= len(self.movieDict[self.actualTrialOrder[trialNum-1]]):
                                self.counters[self.actualTrialOrder[trialNum-1]] = 0
                            self.stimName=disMovie.filename[len(self.moviePath):len(disMovie.filename)-len(self.movieExt)]
                        else:
                            disMovie = 0
                    self.redoTrial(trialNum)
                    didRedo = True
                elif self.keyboard[self.key.J] and trialType == 'Hab': #jump to test in a hab design
                    habs = [i for i, x in enumerate(self.actualTrialOrder) if x == 'Hab']
                    tempNum = max(habs)
                    #trialNum is in fact the index after the current trial at this point
                    #so we can just erase everything between that and the first non-hab trial.
                    del self.actualTrialOrder[trialNum-1:tempNum]
                    trialType = self.actualTrialOrder[trialNum-1]
                    if self.stimPres:
                        disMovie= self.movieDict[self.actualTrialOrder[trialNum-1]][self.counters[self.actualTrialOrder[trialNum-1]]] 
                        self.counters[self.actualTrialOrder[trialNum-1]]+=1
                        if self.counters[self.actualTrialOrder[trialNum-1]] >= len(self.movieDict[self.actualTrialOrder[trialNum-1]]):
                            self.counters[self.actualTrialOrder[trialNum-1]] = 0
                        self.stimName=disMovie.filename[len(self.moviePath):len(disMovie.filename)-len(self.movieExt)]
                    else:
                        disMovie = 0
                    if self.blindPres < 1:
                        self.rdyTextAppend=" NEXT: "+ trialType +" TRIAL"
                elif trialType != 'Hab' and self.keyboard[self.key.I] and 'Hab' in self.trialOrder: #insert additional hab trial
                    #literally insert a new trial into actualTrialOrder, get the right movie, etc.
                    if len(self.habTrialList)>0:
                        for z in range(0, len(self.habTrialList)):
                            self.actualTrialOrder.insert(trialNum - 1 + z, self.habTrialList[z])
                    else:
                        self.actualTrialOrder.insert(trialNum-1,'Hab')
                    trialType = self.actualTrialOrder[trialNum -1]
                    if self.stimPres: #Here we change the movie file of the current trial only. fine as is.
                        disMovie= self.movieDict[self.actualTrialOrder[trialNum-1]][self.counters[self.actualTrialOrder[trialNum-1]]] 
                        self.counters[self.actualTrialOrder[trialNum-1]]+=1
                        if self.counters[self.actualTrialOrder[trialNum-1]] >= len(self.movieDict[self.actualTrialOrder[trialNum-1]]):
                            self.counters[self.actualTrialOrder[trialNum-1]] = 0
                        self.stimName=disMovie.filename[len(self.moviePath):len(disMovie.filename)-len(self.movieExt)]
                    else:
                        disMovie = 0
                    if self.blindPres < 1:
                        self.rdyTextAppend=" NEXT: "+ trialType +" TRIAL"
                else:
                    self.statusSquareA.fillColor='blue'
                    if self.blindPres <2:
                        self.statusTextA.text="RDY"
                    self.statusSquareA.draw()
                    self.statusTextA.draw()
                    if self.blindPres < 2:
                        self.trialText.draw()
                        if self.blindPres < 1:
                            self.readyText.draw()
                    if self.verbose:
                        self.statusSquareB.fillColor='blue'
                        if self.blindPres < 2:
                            self.statusTextB.text="RDY"
                        self.statusSquareB.draw()
                        self.statusTextB.draw()
                    self.win2.flip() #flips the status screen without delaying the stimulus onset.
                    #dispTrial(0,disMovie)
            x = self.doTrial(trialNum, trialType,disMovie) #the actual trial, returning one of four status values at the end
            AA = self.autoAdvance  #After the very first trial AA will always be whatever it was set to at the top.
            if x == 2: # end experiment, either due to final trial ending or 'end experiment altogether' button.
                runExp = False
                didRedo = False
            elif x == 3: #bad trial, redo!
                trialNum = trialNum
                didRedo = True
            elif x == 1: #end hab block!
                habs = [i for i, z in enumerate(self.actualTrialOrder) if z == 'Hab']
                tempNum = max(habs)
                #trialNum is in fact the index after the current trial at this point
                #so we can just erase everything between that and the first non-hab trial.
                del self.actualTrialOrder[trialNum:tempNum+1] #oddly, the del function does not erase the final index.
                trialNum += 1
                trialType = self.actualTrialOrder[trialNum-1]
                if self.blindPres == 0:
                    self.rdyTextAppend=" NEXT: "+ trialType +" TRIAL"
                didRedo = False
            elif x == 0: #continue hab/proceed as normal
                trialNum += 1
                trialType = self.actualTrialOrder[trialNum-1]
                if not self.blindPres:
                    self.rdyTextAppend=" NEXT: "+ trialType +" TRIAL"
                didRedo = False
    
    def doTrial(self,number, type,disMovie):
        #print(number)
        self.trialText.text = "Trial no. " + str(number)
#        global habCount
#        global frameCount
#        global pauseCount
        if type == 'Hab':
            self.habCount += 1
        self.frameCount = 0 #reset display
        self.pauseCount = 0 #needed for ISI
        #returns 0 if do next trial, 1 if end hab, 2 if end experiment, 3 if abort/redo
        if self.stimPres:
            disMovie.seek(0)
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
        numOff2=0
        numOn2=0
        redo = False
        runTrial = True
        endFlag = False
        self.readyText.text="Trial running"
        if self.keyboard[self.key.B]:
            gazeOn = True
            startOn = 0 #we want these to be 0 because every other time is put in reference to the startTrial timestamp so it's not some absurd number
            numOn = 1
        else:
            gazeOn = False
            numOff = 1
            startOff = 0
        if self.verbose:
            if self.keyboard[self.key.L]:
                gazeOn2 = True
                startOn2 = 0
                numOn2 = 1
            else:
                gazeOn2 = False
                numOff2 = 1
                startOff2 = 0
        while runTrial: #runTrial is the key boolean that actually ends the trial. Need an 'end flag' to work with.
            if self.keyboard[self.key.R]: #'abort trial' is pressed
                redo = True
                runTrial = False
                endTrial = core.getTime() - startTrial
                #determine if they were looking or not at end of trial and update appropriate array
                if gazeOn:
                    onDur = endTrial - startOn
                    tempGazeArray = [number, type, startOn, endTrial, onDur]
                    onArray.append(tempGazeArray)
                else:
                    offDur = endTrial - startOff
                    tempGazeArray = [number, type, startOff, endTrial, offDur]
                    offArray.append(tempGazeArray)
            elif self.keyboard[self.key.Y]: #the 'end the study' button, for fuss-outs (9 for lab, 6 for home test)
                runTrial = False
                endTrial = core.getTime() - startTrial
                #determine if they were looking or not at end of trial and update appropriate array
                if gazeOn:
                    onDur = endTrial - startOn
                    tempGazeArray = [number, type, startOn, endTrial, onDur]
                    onArray.append(tempGazeArray)
                else:
                    offDur = endTrial - startOff
                    tempGazeArray = [number, type, startOff, endTrial, offDur]
                    offArray.append(tempGazeArray)
                if len(onArray) == 0:
                    onArray.append([0,0,0,0,0])
                if len(offArray) == 0:
                    offArray.append([0,0,0,0,0]) #keeps it from crashing while trying to write data.
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
                    if gazeOn:
                        onDur = endTrial - startOn
                        tempGazeArray = [number, type, startOn, endTrial, onDur]
                        onArray.append(tempGazeArray)
                    else:
                        offDur = endTrial - startOff
                        tempGazeArray = [number, type, startOff, endTrial, offDur]
                        offArray.append(tempGazeArray)
            elif not gazeOn: #if they are not looking as of the previous refresh, check if they have been looking away for too long
                nowOff = core.getTime() - startTrial
                if sumOn > self.minOn and nowOff - startOff >= self.maxOff and self.playThrough[type] == 0 and not endFlag:
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
                        tempGazeArray = [number, type, startOff, endOff, offDur]
                        offArray.append(tempGazeArray)
                elif self.keyboard[self.key.B]: #if they have started looking since the last refresh and not met criterion
                    gazeOn = True
                    numOn = numOn + 1
                    startOn = core.getTime() - startTrial
                    endOff = core.getTime() - startTrial 
                    #by definition, if this is tripped there will be a preceding 'off' section if this is tripped because gazeOn is set at start
                    offDur = endOff - startOff
                    tempGazeArray = [number, type, startOff, endOff, offDur]
                    offArray.append(tempGazeArray)
            elif gazeOn:
                nowOn = core.getTime() - startTrial
                if self.playThrough[type] == 1 and sumOn + (nowOn-startOn) >= self.minOn and not endFlag: #For trial types where the only crit is min-on.
                    if type in self.movieEnd:
                        endFlag = True
                    else:
                        runTrial = False
                        endTrial = core.getTime() - startTrial
                        if not self.stimPres:
                            self.endTrialSound.play()
                        endOn = core.getTime() - startTrial
                        onDur = endOn - startOn
                        tempGazeArray = [number, type, startOn, endOn, onDur]
                        onArray.append(tempGazeArray)
                if gazeOn and not self.keyboard[self.key.B]: #if they were looking and have looked away.
                    gazeOn = False
                    endOn = core.getTime() - startTrial
                    onDur = endOn - startOn
                    numOff = numOff + 1
                    startOff = core.getTime() - startTrial
                    tempGazeArray = [number, type, startOn, endOn, onDur]
                    onArray.append(tempGazeArray)
                    sumOn = sumOn + onDur

            if self.verbose:
                if not gazeOn2: #if they are not looking as of the previous refresh
                    nowOff2 = core.getTime() - startTrial2
                    if self.keyboard[self.key.L]: #if they have started looking since the last refresh and not met criterion
                        gazeOn2 = True
                        numOn2 = numOn2 + 1
                        startOn2 = core.getTime() - startTrial2
                        endOff2 = core.getTime() - startTrial2
                        offDur2 = endOff2 - startOff2
                        tempGazeArray2 = [number, type, startOff2, endOff2, offDur2]
                        offArray2.append(tempGazeArray2)
                elif gazeOn2 and not self.keyboard[self.key.L]: #if they were looking and have looked away.
                    gazeOn2 = False
                    endOn2 = core.getTime() - startTrial2
                    onDur2 = endOn2 - startOn2
                    numOff2 = numOff2 + 1
                    startOff2 = core.getTime() - startTrial2
                    tempGazeArray2 = [number, type, startOn2, endOn2, onDur2]
                    onArray2.append(tempGazeArray2)
                    sumOn2 = sumOn2 + onDur2
            movieStatus = self.dispTrial(type,disMovie)
            if type in self.movieEnd and endFlag and movieStatus == 1:
                runTrial = False
                endTrial = core.getTime() - startTrial
                if gazeOn:
                    onDur = endTrial - startOn
                    tempGazeArray = [number, type, startOn, endTrial, onDur]
                    onArray.append(tempGazeArray)
                else:
                    offDur = endTrial - startOff
                    tempGazeArray = [number, type, startOff, endTrial, offDur]
                    offArray.append(tempGazeArray)
        if self.verbose:
            if gazeOn2:
                onDur2 = endTrial - startOn2
                tempGazeArray2 = [number, type, startOn2, endTrial, onDur2]
                onArray2.append(tempGazeArray2)
            else:
                offDur2 = endTrial - startOff2
                tempGazeArray2 = [number, type, startOff2, endTrial, offDur2]
                offArray2.append(tempGazeArray2)
        #print offArray
        #print onArray2
        #print offArray2
        if self.stimPres:
            disMovie.seek(0) #this is the reset, we hope.
            disMovie.pause()
        self.statusSquareA.fillColor='black'
        self.statusSquareB.fillColor='black'
        self.statusTextA.text=""
        self.statusTextB.text=""
        self.statusSquareA.draw()
        if self.blindPres < 2:
            self.trialText.draw()
            if self.blindPres < 1:
                self.readyText.draw()
        if self.verbose:
            self.statusSquareB.draw()
        self.win2.flip()
        if self.stimPres:
            self.win.flip() #blanks the screen outright.
        if redo: #if the abort button was pressed
            self.abortTrial(onArray, offArray, number,type,onArray2, offArray2,self.stimName)
            return 3
        if type == 'Hab': #if still during habituation
            #need to check based on number of HAB trial specifically
            self.dataRec(onArray, offArray, number, type, onArray2, offArray2,self.stimName)
            if self.checkStop(number, self.habCount):
                return 1
            else:
                return 0
        elif number >= len(self.actualTrialOrder) or type == 4:
            self.endExperiment(onArray, offArray, number,type, onArray2, offArray2,self.stimName)
            return 2
        else:
            self.dataRec(onArray, offArray, number, type, onArray2, offArray2,self.stimName)
            return 0
    
    def endExperiment(self,onArray, offArray, trial, type, onArray2, offArray2,stimName=''):
        sumOn = 0
        sumOff = 0
        sumOn2 = 0
        sumOff2 = 0
        for i in range(0,len(onArray)):
            sumOn = sumOn + onArray[i][4]
        for j in range(0,len(offArray)):
            sumOff = sumOff + offArray[j][4]
        if len(offArray2)>0:
            for i in range(0,len(onArray2)):
                sumOn2 = sumOn2 + onArray2[i][4]
            for j in range(0,len(offArray2)):
                sumOff2 = sumOff2 + offArray2[j][4]
            self.verboseOn2.extend(onArray2)
            self.verboseOff2.extend(offArray2)
        #add to master gaze array
        self.verboseOn.extend(onArray)
        self.verboseOff.extend(offArray)
        #print verboseOn
        #print verboseOn2
        #data format: snum, age in months, age in days, sex, condition, trial, GNGtrial, trial type, hab crit, on-time, number of gazes, off-time, number of look-offs
        #then same again at the end for b-coder?
        if sumOn > 0: #Only add another item to the list if there's a real trial to add!
            tempData={'sNum':self.sNum, 'months':self.ageMo, 'days':self.ageDay, 'sex':self.sex, 'cond':self.cond,'condLabel':self.condLabel, 
                                'trial':trial, 'GNG':1, 'trialType':type, 'stimName':stimName, 'habCrit':self.habCrit, 
                                'sumOnA':sumOn, 'numOnA':len(onArray), 'sumOffA':sumOff, 'numOffA':len(offArray),
                                'sumOnB':sumOn2,'numOnB':len(onArray2),'sumOffB':sumOff2,'numOffB':len(offArray2)}
            #print tempData
            self.dataMatrix.append(tempData)
        #sort the data matrices and shuffle them together.
        if len(self.badTrials) > 0: #if there are any redos, they need to be shuffled in appropriately. 
            for i in range(0,len(self.badTrials)):
                x = 0
                while self.dataMatrix[x]['trial'] != self.badTrials[i]['trial']:
                    x += 1
                while self.dataMatrix[x]['GNG'] == 0: #this is to get around the possibility that the same trial had multiple 'false starts'
                    x += 1
                self.dataMatrix.insert(x, self.badTrials[i]) #python makes this stupid easy
        #first, we create the headers
        #headers = ['snum','months','days', 'sex', 'condition','trial','GNG','trialType','habCrit','onTime','numGazes','offTime', 'numOff','onTimeB','numGazesB','offTimeB','numOffB']
        #could check for existing data file to prevent overwrites?
        outputWriter = csv.DictWriter(open(self.dataFolder+self.prefix+str(self.sNum)+'_'+str(self.sID)+'_'+str(self.today.month)+str(self.today.day)+str(self.today.year)+'.csv','w'), fieldnames = self.dataColumns,extrasaction='ignore',lineterminator ='\n') #careful! this OVERWRITES the existing file. Fills from snum.
        outputWriter.writeheader()
        for r in range(0, len(self.dataMatrix)):
            #print('writing rows')
            outputWriter.writerow(self.dataMatrix[r])
        if self.verbose: #if you want VERBOSE data as well as the regular stuff, there's a whole extra set of steps
            verboseMatrix = []
            #first, verbose data is not as well organized. However, we should be able to alternate back and forth between 
            #on and off until we reach the end of a given trial, to reconstruct it.
            #at the start of each line, add information: sNum, ageMo, ageDay, sex, cond, GNG, ON/OFF
            for n in range(0, len(self.verboseOn)):
                self.verboseOn[n][0:0]=[self.sNum, self.ageMo, self.ageDay, self.sex, self.cond,1,1]
            for m in range(0, len(self.verboseOff)):# adding the details to the verbose array
                self.verboseOff[m][0:0]=[self.sNum, self.ageMo, self.ageDay, self.sex, self.cond,1,0]
            if len(self.badTrials)>0:
                for o in range(0,len(self.badVerboseOn)):
                    self.badVerboseOn[o][0:0]=[self.sNum, self.ageMo, self.ageDay, self.sex,self.cond,0,1]
                for p in range(0,len(self.badVerboseOff)):#same details for the bad trials
                    self.badVerboseOff[p][0:0]=[self.sNum, self.ageMo, self.ageDay, self.sex,self.cond,0,0]
            #read the final data matrix and go trial by trial.
            #print(verboseOn) #debug, to make sure verboseOn is being constructed correctly
            for q in range(0, len(self.dataMatrix)):
                tnum = self.dataMatrix[q]['trial']
                onIndex = -1
                offIndex = -1
                if self.dataMatrix[q]['GNG'] == 1: #separate for good and bad trials
                    for x in range(0, len(self.verboseOn)): 
                        if self.verboseOn[x][7] == tnum and onIndex == -1: #find the right index in the verbose matrices
                            onIndex = x
                    for y in range(0, len(self.verboseOff)):
                        if self.verboseOff[y][7] == tnum and offIndex == -1: 
                            offIndex = y
                    trialVerbose = []
                    if onIndex >= 0:
                        while onIndex < len(self.verboseOn):
                            if self.verboseOn[onIndex][7] == tnum:
                                trialVerbose.append(self.verboseOn[onIndex])
                            onIndex += 1
                    if offIndex >= 0:
                        while offIndex < len(self.verboseOff):
                            if self.verboseOff[offIndex][7]==tnum:
                                trialVerbose.append(self.verboseOff[offIndex])
                            offIndex += 1
                    trialVerbose2 = sorted(trialVerbose, key=lambda trialVerbose:trialVerbose[9]) #this is the magic bullet, in theory.
                    verboseMatrix.extend(trialVerbose2)
                elif self.dataMatrix[q]['GNG']==0: #bad trials. 
                    if q > 0 and self.dataMatrix[q-1]['GNG']==0: 
                        pass #stops it from doubling up. If there is more than one consecutive bad trial, it will get all of them in a row the first time,
                    else:
                        trialVerbose = []
                        for x in range(0,len(self.badVerboseOn)):
                            if self.badVerboseOn[x][7] == tnum and onIndex == -1:
                                onIndex = x
                        for y in range(0, len(self.badVerboseOff)): 
                            if self.badVerboseOff[y][7] == tnum and offIndex == -1:
                                offIndex = y
                        if onIndex >= 0:
                            while onIndex < len(self.badVerboseOn):
                                if self.badVerboseOn[onIndex][7] == tnum:
                                    trialVerbose.append(self.badVerboseOn[onIndex])
                                onIndex += 1
                        if offIndex >=0: 
                            while offIndex < len(self.badVerboseOff):
                                if self.badVerboseOff[offIndex][7]==tnum:
                                    trialVerbose.append(self.badVerboseOff[offIndex])
                                offIndex += 1
                        trialVerbose2 = sorted(trialVerbose, key=lambda trialVerbose:trialVerbose[9]) #this is the magic bullet, in theory.
                        verboseMatrix.extend(trialVerbose2)
            outputWriter2 = csv.writer(open(self.dataFolder+self.prefix+str(self.sNum)+'_'+str(self.sID)+'_'+str(self.today.month)+str(self.today.day)+str(self.today.year)+'_VERBOSE.csv','w'), lineterminator ='\n') #careful! this OVERWRITES the existing file. Fills from snum.
            headers2=['snum', 'months', 'days', 'sex','cond','GNG','gazeOnOff','trial','trialType','startTime','endTime','duration']
            outputWriter2.writerow(headers2)
            for z in range(0,len(verboseMatrix)):
                outputWriter2.writerow(verboseMatrix[z])
            if self.verbose and len(self.verboseOn2)>0:
                verboseMatrix2 = []
                for n in range(0, len(self.verboseOn2)):
                    self.verboseOn2[n][0:0]=[self.sNum, self.ageMo, self.ageDay, self.sex, self.cond,1,1]
                for m in range(0, len(self.verboseOff2)):
                    self.verboseOff2[m][0:0]=[self.sNum, self.ageMo, self.ageDay, self.sex, self.cond,1,0]
                if len(self.badTrials)>0:
                    for o in range(0,len(self.badVerboseOn2)):
                        self.badVerboseOn2[o][0:0]=[self.sNum, self.ageMo, self.ageDay, self.sex, self.cond,0,1]
                    for p in range(0,len(self.badVerboseOff2)):
                        self.badVerboseOff2[p][0:0]=[self.sNum, self.ageMo, self.ageDay, self.sex, self.cond,0,0]
                for q in range(0, len(self.dataMatrix)):
                    tnum = self.dataMatrix[q]['trial']
                    onIndex2 = -1
                    offIndex2 = -1
                    if self.dataMatrix[q]['GNG'] == 1: #separate for good and bad trials
                        for x in range(0, len(self.verboseOn2)): 
                            if self.verboseOn2[x][7] == tnum and onIndex2 == -1: #find the right index in the verbose matrices
                                onIndex2 = x
                        for y in range(0, len(self.verboseOff2)):
                            if self.verboseOff2[y][7] == tnum and offIndex2 == -1: 
                                offIndex2 = y
                        trialVerbose=[]
                        if onIndex2 >=0:
                            while onIndex2 < len(self.verboseOn2):
                                if self.verboseOn2[onIndex2][7]==tnum:
                                    trialVerbose.append(self.verboseOn2[onIndex2])
                                onIndex2 += 1
                        if offIndex2 >=0:
                            while offIndex2 < len(self.verboseOff2):
                                if self.verboseOff2[offIndex2][7]==tnum:
                                    trialVerbose.append(self.verboseOff2[offIndex2])
                                offIndex2 += 1                    
                        trialVerbose2 = sorted(trialVerbose, key=lambda trialVerbose:trialVerbose[9])
                        verboseMatrix2.extend(trialVerbose2)
                    elif self.dataMatrix[q]['GNG']==0: #bad trials. These arrays will be much less predictable, so putting them together is inherently more challenging
                        if q > 0 and self.dataMatrix[q-1]['GNG']==0: 
                            pass #stops it from doubling up. If there is more than one consecutive bad trial, it will get all of them in a row the first time,
                        else:
                            for x in range(0,len(self.badVerboseOn2)):
                                if self.badVerboseOn2[x][7] == tnum and onIndex2 == -1:
                                    onIndex2  = x
                            for y in range(0, len(self.badVerboseOff2)): 
                                if self.badVerboseOff2[y][7] == tnum and offIndex2 == -1:
                                    offIndex2 = y
                            trialVerbose=[]
                            if onIndex2 >=0:
                                while onIndex2 < len(self.badVerboseOn2):
                                    if self.badVerboseOn2[onIndex2][7]==tnum:
                                        trialVerbose.append(self.badVerboseOn2[onIndex2])
                                    onIndex2 += 1
                            if offIndex2 >=0:
                                while offIndex2 < len(self.badVerboseOff2):
                                    if self.badVerboseOff2[offIndex2][7]==tnum:
                                        trialVerbose.append(self.badVerboseOff2[offIndex2])
                                    offIndex2 += 1                    
                            trialVerbose2 = sorted(trialVerbose, key=lambda trialVerbose:trialVerbose[9]) 
                            verboseMatrix2.extend(trialVerbose2)
                outputWriter3 = csv.writer(open(self.dataFolder+self.prefix+str(self.sNum)+'_'+str(self.sID)+'_'+str(self.today.month)+str(self.today.day)+str(self.today.year)+'_VERBOSEb.csv','w'), lineterminator ='\n') 
                outputWriter3.writerow(headers2)
                for k in range(0,len(verboseMatrix2)):
                    outputWriter3.writerow(verboseMatrix2[k])
                rel=self.reliability(verboseMatrix, verboseMatrix2)
                outputWriter4 = csv.writer(open(self.dataFolder+self.prefix+str(self.sNum)+'_'+str(self.sID)+'_'+str(self.today.month)+str(self.today.day)+str(self.today.year)+'_Stats.csv','w'), lineterminator ='\n')
                headers3=['WeightedPercentageAgreement', 'CohensKappa','AverageObserverAgreement','PearsonsR']
                outputWriter4.writerow(headers3)
                outputWriter4.writerow(rel)
        core.wait(.3)
        self.win2.close()
        if self.stimPres:
            self.win.close()
    
    def reliability(self, verboseMatrix, verboseMatrix2):
        a=0
        d=0
        stats=[]
        timewarp=[]#frame by frame arrays
        timewarp2=[]
        for i in verboseMatrix:
            if i[5]!=0:#check for it not to be a bad gaze
                for k in range(0, int(round(i[11]*60))):
                    timewarp.append([i[7],i[6]])#6 being On or Off and 7 the trial no.
        for i in verboseMatrix2:
            if i[5]!=0:
                for k in range(0, int(round(i[11]*60))):
                    timewarp2.append([i[7],i[6]])
        if len(timewarp)>len(timewarp2):#making sure the frame by frame arrays are of equal length
            diff=len(timewarp)-len(timewarp2)
            for s in range(0, diff):
                timewarp2.append([verboseMatrix2[-1][7],0])
        elif len(timewarp)<len(timewarp2):
            diff=len(timewarp2)-len(timewarp)
            for s in range(0, diff):
                timewarp.append([verboseMatrix[-1][7],0])
        for (i, j) in zip(timewarp, timewarp2):
            if i[0]==j[0]:
                if i[1]==j[1]:
                    a+=1
                else:
                    d+=1
            else:
                d+=1
        wpagreement=float(a)/float(a+d)
        stats.append(str(wpagreement))
        #Pearson's R
        trialA=[]
        trialB=[]
        avA=0
        avB=0
        for i in self.dataMatrix:
            if i['GNG']!=0:
                trialA.append(i['sumOnA'])
                trialB.append(i['sumOnB'])
                avA+=i['sumOnA']
                avB+=i['sumOnB']
        avA=avA/self.dataMatrix[-1]['trial']
        avB=avB/self.dataMatrix[-1]['trial']
        xy=[]
        for i in range(0,len(trialA)):
            trialA[i]-= avA
            trialB[i]-= avB
            xy.append(trialA[i]*trialB[i])
        for i in range(0, len(trialA)):# square the deviation arrays
            trialA[i]=trialA[i]**2
            trialB[i]=trialB[i]**2
        r=str(sum(xy)/sqrt(sum(trialA)*sum(trialB)))
        #cohen's Kappa
        coderBon=0
        coderAon=0
        for i in range(0, len(timewarp)):#are the 2 timewarps equal? - when can one be bigger?
            if timewarp[i][1]==1:
                coderAon+=1
            if timewarp2[i][1]==1:
                coderBon+=1
        pe=(float(coderAon)/len(timewarp))*(float(coderBon)/len(timewarp2))+(float(len(timewarp)-coderAon)/len(timewarp))*(float(len(timewarp2)-coderBon)/len(timewarp2))
        k=float(wpagreement-pe)/float(1-pe)
        stats.append(str(k))
        #Average Observer Agreement
        tg = 0
        if self.dataMatrix[-1]['GNG'] == 1: #make sure last trial is good
            finalTrial = self.dataMatrix[-1]['trial']
        else:
            finalTrial = 0
            for i in range(1,len(self.dataMatrix)):
                if self.dataMatrix[-1*i]['GNG']==1:
                    finalTrial = self.dataMatrix[-1*i]['trial']
        if finalTrial > 0: #if there are NO good trials, well it's probably crashed already, but JIC
            for i in range(0, self.dataMatrix[-1]['trial']): #need contingency if last trial is bad trial?
                a=0
                d=0
                for (m, l) in zip(timewarp, timewarp2):
                    if m[0]==i+1 and l[0]==i+1:
                        if m[1]==l[1]:
                            a+=1
                        else:
                            d+=1
                tg=tg + float(a)/(a+d)
            aoagreement=str(float(tg)/self.dataMatrix[-1]['trial'])
            stats.append(aoagreement)
        else:
            stats.append('N/A')
        stats.append(r)
        return stats
    
    def isInt(t): #silly little function for validating a very narrow usage of "cond" field
        try:
            int(t)
            return True
        except ValueError:
            return False
    
    def run(self):
        startDlg = gui.Dlg(title=self.prefix + ' Experiment')
        startDlg.addText('Subject info')
        startDlg.addField('Subject Number: ')
        startDlg.addField('Subject ID: ')
        startDlg.addField('sex: ')
        startDlg.addField('DOB(month): ')
        startDlg.addField('DOB(day): ')
        startDlg.addField('DOB(year): ')
        if self.randPres and len(self.condList)>0:
            startDlg.addField('Cond: ', choices=self.condList)
        else:
            startDlg.addField('Cond: ')
        startDlg.addField('Verbose data/multiple coders? ', choices=['Y','N'])
        if not self.stimPres:
            startDlg.addField('DOT(month): ')
            startDlg.addField('DOT(day): ')
            startDlg.addField('DOT(year): ')
        startDlg.show()
        if startDlg.OK:
            if self.stimPres:
                self.win = visual.Window((self.screenWidth,self.screenHeight),fullscr=False, screen=1,allowGUI=False, units='pix', rgb=[-1,-1,-1])
            self.win2 = visual.Window((400,400),fullscr=False,screen=0,allowGUI=True,units='pix',waitBlanking=False, rgb=[-1,-1,-1])
            thisInfo = startDlg.data
            self.sNum = thisInfo[0]
            self.sID = thisInfo[1]
            self.sex = thisInfo[2]
            #now for the exciting bit: converting DOB into months/days.
            self.today = date.today()
            DOB = date(2000+int(thisInfo[5]), int(thisInfo[3]), int(thisInfo[4]))
            if self.stimPres:
                DOT = self.today
            else:
                DOT = date(2000+int(thisInfo[10]), int(thisInfo[8]), int(thisInfo[9]))
            #Dateutil's relativedelta is included in psychopy and just better than every other option!
            ageDif = relativedelta(DOT,DOB)
            self.ageMo = ageDif.years*12+ageDif.months
            self.ageDay = ageDif.days #Impossibly simple, but it works.
            self.actualTrialOrder=[] #in this version, mostly a key for the hab trials.
            for i in range(0, len(self.trialOrder)):
                if self.trialOrder[i] == 'Hab':
                    for j in range(0,self.maxHabTrials):
                        if len(self.habTrialList) > 0:
                            for q in range(0,len(self.habTrialList)):
                                self.actualTrialOrder.append(self.habTrialList[q])
                        else:
                            self.actualTrialOrder.append('Hab')
                else:
                    self.actualTrialOrder.append(self.trialOrder[i])
            #build trial order
            if self.randPres and len(self.condList) > 0: #Extra check added.
                self.condLabel = thisInfo[6]
                testReader=csv.reader(open(self.condPath+self.condFile,'rU'))
                testStuff=[]
                for row in testReader:
                    testStuff.append(row)
                testDict = dict(testStuff) 
                self.cond = testDict[self.condLabel]  #this will read as order of indeces in N groups, in a 2-dimensional array (hopefully)
                #type conversion required. Eval will read the string into a dictionary (now).
                self.cond=eval(self.cond)
                #now to rearrange the lists of each trial type. 
                finalDict=[]
                if sys.version_info[0] < 3:
                    for i, j in self.cond.iteritems():
                        newTempTrials = []
                        for q in range(0, len(j)):
                            newTempTrials.append(self.movieNames[i][j[q]-1])
                        finalDict.append((i,newTempTrials))
                else:
                    for i, j in self.cond.items():
                        newTempTrials = []
                        for q in range(0, len(j)):
                            newTempTrials.append(self.movieNames[i][j[q]-1])
                        finalDict.append((i,newTempTrials))
                self.movieNames=dict(finalDict)
            else:
                self.cond=thisInfo[6]
                self.condLabel = self.cond
            if self.stimPres:
                tempText=visual.TextStim(self.win2, text="Loading Movies", pos=[0, 0], color='white', bold=True, height=40)
                tempText.draw()
                self.win2.flip()
                self.movieDict = {x:[] for x in self.movieNames.keys()} #This will hold the loaded movies. 
                self.counters = {x:0 for x in self.movieNames.keys()} #list of counters, one per index of the dict, so it knows which movie to play
                tempCtr = {x:0 for x in self.movieNames.keys()}
                for i in self.actualTrialOrder:
                    if i is not 'Hab':
                        tempMovie = visual.MovieStim3(self.win, self.moviePath+self.movieNames[i][tempCtr[i]]+self.movieExt, size=[self.movieWidth,self.movieHeight], flipHoriz=False, flipVert=False, loop=False)
                        self.movieDict[i].append(tempMovie)
                        tempCtr[i] += 1
                        if tempCtr[i] >= len(self.movieNames[i]):
                            tempCtr[i] = 0
                    else: #for hab trials, only load the very first entry in the list, ignore the rest. This is after scrambling, so allows for between manips.
                        tempMovie = visual.MovieStim3(self.win, self.moviePath+self.movieNames[i][0]+self.movieExt, size=[self.movieWidth,self.movieHeight], flipHoriz=False, flipVert=False, loop=False)
                        self.movieDict[i].append(tempMovie)
            self.verbose = thisInfo[7]
            self.key=pyglet.window.key
            self.keyboard = self.key.KeyStateHandler()
            self.win2.winHandle.push_handlers(self.keyboard)
            if self.stimPres:
                self.win.winHandle.push_handlers(self.keyboard)
                self.attnGetterSquare = visual.Rect(self.win, height=40, width=40, pos=[self.testOffset+0,0], fillColor='black')
            #testSquareA=visual.Rect(win, height=80, width=80, pos=[testOffset-560,0], fillColor='red', lineColor='red')
            #testSquareB=visual.Rect(win, height=80, width=80, pos=[testOffset+0,0], fillColor='green', lineColor='green')
            self.statusSquareA=visual.Rect(self.win2, height=80, width=80, pos=[self.statusOffset-60, self.statusOffsetY+0], fillColor='black')# These two appear on the status screen window.
            self.statusSquareB=visual.Rect(self.win2, height=80, width=80, pos=[self.statusOffset+60, self.statusOffsetY+0], fillColor='black') 
            self.statusTextA = visual.TextStim(self.win2, text="", pos=[self.statusOffset-60, self.statusOffsetY+0], color='white', bold=True, height=30)
            self.statusTextB = visual.TextStim(self.win2, text="", pos=[self.statusOffset+60, self.statusOffsetY+0],color='white', bold=True, height=30)
            self.trialText = visual.TextStim(self.win2, text="Trial no: ", pos = [-150,150], color='white')
            self.readyText = visual.TextStim(self.win2, text="Trial not active", pos=[-25,100], color='white')
            self.doExperiment() #Get this show on the road!
            

    