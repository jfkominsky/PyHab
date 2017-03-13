from psychopy import visual, event, core, data, gui, monitors, tools, sound
import pyglet
from pyglet import input as pyglet_input
import wx, random, csv
from math import *
from datetime import *
#import pyglet
#PyHab + stimulus control system
#Jonathan Kominsky, 2016
#Keyboard coding: A = ready, B = coder 1 on, L = coder 2 on, F = abort trial, Y = end experiment (for fussouts)
#Other keyboard commands: R = redo previous trial, J = jump to test trial, I = insert additional habituation trial (hab only)
#Xhab-like data output, to csv: Subject no, age, condition, trial, trialtype, hab crit, ontime, [ontime2,] offtime, [offtime2,]

'''
SETTINGS
'''
#UNIVERSAL SETTINGS
maxDur = 60 #maximum number of seconds in a trial
maxOff = 2 #maximum number of consecutive seconds of offtime to end trial
minOn = 1 #minimum on-time for a trial (seconds)
prefix='PyHab' #prefix for data files. All data filenames will start with this text.
habituationDesign = False #Habituation or familiarization? True = habituation design. False = familiarziation/VoE
moviePath = 'DemoMaterials/' #Folder where movie files can be located (if not in same folder as script)
habMovieNames = ['3x2_1_1_1','3x2_1_2_1','3x2_1_3_1'] #List of names of movies to be used during habituation, WITHOUT FILE EXTENSIONS. 
testMovieNames = ['3x2_2_1_1', '3x2_2_2_1'] #names of files to be used during test.
introMovieNames = [] #if there are intro movies other than the hab and test movies in a VoE design
movieExt = '.mov' #File extension/movie type
randPres=False #controls whether the program will look for an external randomization file to determine presentation order
#If not, hab will present the first thing in each of the lists above, and VoE will just go through the lists in order
condPath = 'DemoMaterials' #path for the condition file.
condFile = 'finalCondListDNO.csv' #if you have a condition file, put filename here (WITH EXTENSION). Must be .csv
condList = ['1','2','3'] #list of conditions for the dropdown menu, if using random presentation.
#HABITUATION DESIGN SETTINGS
maxHabTrials = 14 #number of habituation trials in a HAB design
numTestTrials = 1 #number of test trials in a HAB design (must be at least 1). Set VoE options below
#VOE SETTINGS
#Order of presentation:
#1 = intro trial (goes through introMovieNames in order) 
#2 = familiarization trial 
#3 = test trial 
#Recommend you make sure repetitions of each trial type is a multiple of the list length, if you want even presentation
trialOrder=[2,2,2,2,2,2,3,3,3,3]
'''
END SETTINGS
'''
testTrialCount = 1 #test trials start counting from 1 for reasons of making the settings more intuitive
habCrit = 0 #initial setting of habcrit at 0
dataMatrix = [] #primary data array 
#data format: snum, age in months, age in days, sex, condition, trial, GNGtrial, trial type, hab crit, on-time, number of gazes, off-time, number of look-offs
#then same again at the end for b-coder?
badTrials=[] # data array for bad trials
verboseOn=[] #"verbose" data aray for gazes on, that includes each individual gaze, when it happened, etc.
verboseOff=[] #same for off-time
verboseOn2=[] #for coder B. Can't assume that they will line up in terms of number of gazes so can't put them in same file.
verboseOff2=[] #for coder B.
badVerboseOn=[] #same as above but for bad trials
badVerboseOff=[] #same as above but for bad trials
badVerboseOn2=[]
badVerboseOff2=[]
HeyListen=sound.Sound('upchime1.wav',secs=3) #will become attn-getter
#It turns out the best way to get the status monitor and the stimuli to display on separate screens
#is to have separate windows, now that pyglet deigns to behave.
statusOffset = 0
statusOffsetY = 0
testOffset = 0

frameCount = 0 #the frame counter for the movement of A and B, based on the refresh rate. 

#Total movement should take 120fr + 20fr ISI
'''
FUNCTIONS
'''
def abortTrial(onArray, offArray, trial, ttype, onArray2, offArray2): #the 2nd arrays are if there are two coders.
    #only happens when the 'abort' button is pressed. In the main trial loop we can not advance the trial number, this mostly 
    #serves to create a separate data array of bad trials that we can incorporate later
    sumOn = 0
    sumOff = 0
    for i in range(0,len(onArray)):
        sumOn = sumOn + onArray[i][4]
    for j in range(0,len(offArray)):
        sumOff = sumOff + offArray[j][4]
    sumOn2=0
    sumOff2=0
    if len(onArray2) > 0:
        for i in range(0,len(onArray2)):
                sumOn2 = sumOn2 + onArray2[i][4]
        for j in range(0,len(offArray2)):
            sumOff2 = sumOff2 + offArray2[j][4]
        badVerboseOn2.extend(onArray2)
        badVerboseOff2.extend(offArray2)
    #data format: snum, age in months, age in days, sex, condition, trial, GNGtrial, trial type, hab crit, on-time, number of gazes, off-time, number of look-offs
    #then same again at the end for b-coder
    tempData=[sNum, ageMo, ageDay, sex, cond, trial, 0, ttype, habCrit, sumOn, len(onArray), sumOff, len(offArray),sumOn2, len(onArray2), sumOff2, len(offArray2)]
    badTrials.append(tempData)
    #needs to be .extend or you get weird array-within-array-within-array issues that become problematic later
    badVerboseOn.extend(onArray)
    badVerboseOff.extend(offArray)

def dataRec(onArray,offArray,trial,type,onArray2,offArray2):
    global habCrit
    sumOn = 0
    sumOff = 0
    #loop through each array adding up gaze duration (on and off).
    for i in range(0,len(onArray)):
        sumOn = sumOn + onArray[i][4]
    for j in range(0,len(offArray)):
        sumOff = sumOff + offArray[j][4]
    sumOn2 = 0
    sumOff2 = 0
    if len(onArray2)>0:
        for i in range(0,len(onArray2)):
            sumOn2 = sumOn2 + onArray2[i][4]
        for j in range(0,len(offArray2)):
            sumOff2 = sumOff2 + offArray2[j][4]
        verboseOn2.extend(onArray2)
        verboseOff2.extend(offArray2)
    #add to verbose master gaze array
    verboseOn.extend(onArray)
    verboseOff.extend(offArray)
    #data format: snum, age in months, age in days, sex, condition, trial, GNGtrial, trial type, hab crit, on-time, number of gazes, off-time, number of look-offs, same again for B-coder
    #then same again at the end for b-coder?
    tempData=[sNum, ageMo, ageDay, sex, cond, trial, 1, type, habCrit, sumOn, len(onArray), sumOff, len(offArray),sumOn2,len(onArray2),sumOff2,len(offArray2)]
    dataMatrix.append(tempData)

def redoTrial(trialNum):
    #basically abort trial but after the fact
    #This will only come up if the last trial is good. If the last trial was aborted and this is called, it will hit the trial before THAT.
    #so, only need to find the trial in dataMatrix
    #print 'redoTrial Active!'
    newTempData=[]
    i = 0
    while i < len(dataMatrix):
        if dataMatrix[i][5] == trialNum:
            trialIndex = i
            newTempData.extend(dataMatrix[i])
            print newTempData
            i+=1
        else:
            i+=1
    #add the new 'bad' trial to badTrials
    #print 'it is now ' + str(newTempData)
    newTempData[6] = 0
    badTrials.append(newTempData)
    #remove it from dataMatrix
    dataMatrix.remove(dataMatrix[trialIndex])
    #now for the hard part: shifting the verbose data!
    #basically need to read through the verbose matrices, add everything that references that trial to BadVerboseOn, and mark the relevant lines for later deletion
    for i in range(0, len(verboseOn)):
        if verboseOn[i][0] == trialNum:
            badVerboseOn.append(verboseOn[i])
            verboseOn[i][0] = 99
    for j in range(0, len(verboseOff)):
        if verboseOff[j][0] == trialNum:
            badVerboseOff.append(verboseOff[j])
            verboseOff[j][0] = 99
    #need to do deletions separately because we keep changing the index every time we remove something.
    k = 0
    l = 0
    while k < len(verboseOn):
        if verboseOn[k][0] == 99:
            verboseOn.remove(verboseOn[k]) #since this removes the entire index, then we should not advance because the next line will come up.
        else:
            k+=1
    while l < len (verboseOff):
        if verboseOff[l][0] == 99:
            verboseOff.remove(verboseOff[l])
        else:
            l += 1
    #and then we need to look at the second coder too...
    if len(verboseOn2) > 0:
        for i in range(0, len(verboseOn2)):
            if verboseOn2[i][0] == trialNum:
                badVerboseOn2.append(verboseOn2[i])
                verboseOn2[i][0] = 99
        for j in range(0, len(verboseOff2)):
            if verboseOff2[j][0] == trialNum:
                badVerboseOff2.append(verboseOff2[j])
                verboseOff2[j][0] = 99
        m=0
        n=0
        while m < len(verboseOn2):
            if verboseOn2[m][0] == 99:
                verboseOn2.remove(verboseOn2[m])
            else:
                m += 1
        while n < len(verboseOff2):
            if verboseOff2[n][0] == 99:
                verboseOff2.remove(verboseOff2[n])
            else:
                n += 1

def checkStop(onArray, offArray, trial, onArray2, offArray2):
    #checks the habitution criteria and returns 'true' if any of them are met.
    global habCrit #python is weird about scope. this ensures that we are using the experiment-wide habCrit variable
    sumOn = 0
    sumOff = 0
    #loop through each array adding up gaze duration (on and off).
    for i in range(0,len(onArray)):
        sumOn = sumOn + onArray[i][4]
    for j in range(0,len(offArray)):
        sumOff = sumOff + offArray[j][4]
    sumOn2 = 0
    sumOff2 = 0
    if len(onArray2)>0:
        for i in range(0,len(onArray2)):
            sumOn2 = sumOn2 + onArray2[i][4]
        for j in range(0,len(offArray2)):
            sumOff2 = sumOff2 + offArray2[j][4]
        verboseOn2.extend(onArray2)
        verboseOff2.extend(offArray2)
    #add to verbose master gaze array
    verboseOn.extend(onArray)
    verboseOff.extend(offArray)
    #data format: snum, age in months, age in days, sex, condition, trial, GNGtrial, trial type, hab crit, on-time, number of gazes, off-time, number of look-offs, same again for B-coder
    #then same again at the end for b-coder?
    tempData=[sNum, ageMo, ageDay, sex, cond, trial, 1, 1, habCrit, sumOn, len(onArray), sumOff, len(offArray),sumOn2,len(onArray2),sumOff2,len(offArray2)]
    dataMatrix.append(tempData)
    if trial == 3 and habituationDesign: #time to set the hab criterion!
        sumOnTimes = 0
        for k in range(0,len(dataMatrix)):
            if dataMatrix[k][6] == 1: #just in case there are any bad trials, we don't want to incorporate them into setting the criterion
                sumOnTimes = sumOnTimes + dataMatrix[k][9] #add up total looking time for first three (good) trials
        habCrit = sumOnTimes/2
    elif trial == maxHabTrials:
        #end habituation and goto test
        return True
    elif trial >= 6 and habituationDesign: #if we're far enough in that we can plausibly meet the hab criterion
        sumOnTimes = 0
        index = 0
        m = 0
        while index == 0: #find the appropriate trial number to add up looking times for the last three
            if dataMatrix[m][5] == trial - 2 and dataMatrix[m][6]==1: #needs to be the first GOOD trial with that trial number
                index = m
            else:
                m = m+1
        for n in range(index, len(dataMatrix)): #now, starting with that trial, go through and add up the good trial looking times
            if dataMatrix[n][6] == 1: #only good trials!
                sumOnTimes = sumOnTimes + dataMatrix[n][9] #add up total looking time
        if sumOnTimes < habCrit:
            #end habituation and go to test
            for i in [0, 1, 2]:
                core.wait(.25)
            return True
        else:
            return False
    else:
        return False

def attnGetter(): #an animation and sound to be called whenever an attentiongetter is needed
     HeyListen.play() 
     x=0
     attnGetterSquare.ori=0
     attnGetterSquare.fillColor='yellow'
     for i in range(0, 60): #a 1-second animation
         attnGetterSquare.ori+=5
         x +=.1
         attnGetterSquare.height=sin(x)*120
         attnGetterSquare.width=tan(.25*x)*120
         attnGetterSquare.draw()
         win.flip()
     statusSquareA.fillColor='blue'
     statusTextA.text="RDY"
     statusSquareA.draw()
     statusTextA.draw()
     trialText.draw()
     readyText.draw()
     if verbose:
         statusSquareB.fillColor='blue'
         statusTextB.text="RDY"
         statusSquareB.draw()
         statusTextB.draw()
     win2.flip()
     win.flip() #clear screen

def dispTrial(trialType,dispMovie):
    #this will be the stimulus display, one frame at a time, independent of everything else.
    #For the moment, it is ab status monitor. One that, annoyingly, cannot use text.
    #needs to be completely independent of the timing of anything else, and simply stop when the thing says to stop.
    #display loops. Test trial needs to know condition, but more importantly needs to know test vs. hab. 
    #but hab needs to know cause v. noncause. Start with cause alone.
    global frameCount
    global locAx
    global locBx
    #first, let's just get the status squares out of the way.
    if keyboard[key.B]:
        statusSquareA.fillColor='green'
        statusTextA.text="ON"
    elif trialType==0:
        statusSquareA.fillColor='blue'
        statusTextA.text="RDY"
    else:
        statusSquareA.fillColor='red'
        statusTextA.text="OFF"
    statusSquareA.draw()
    statusTextA.draw()
    trialText.draw()
    readyText.draw()
    if verbose:
        if keyboard[key.L]:
            statusSquareB.fillColor='green'
            statusTextB.text="ON"
        elif trialType==0:
            statusSquareB.fillColor='blue'
            statusTextB.text="RDY"
        else:
            statusSquareB.fillColor='red'
            statusTextB.text="OFF"
        statusSquareB.draw()
        statusTextB.draw()
    win2.flip() #flips the status screen without delaying the stimulus onset.
    #now for the test trial display
    ISI = 20 #n frames between loops(if desired)
    if frameCount == 0: #initial setup
        dispMovie.seek(frameCount) #unreliable!
        dispMovie.draw()
        dispMovie.pause()
        frameCount+=1
        win.flip()
        if trialType == 0:
            frameCount=0 # for attn-getter
    elif frameCount == 1:
        #print('playing')
        dispMovie.play()        
        dispMovie.draw()
        frameCount+=1
        win.flip()
        if trialType == 0: #It's necessary to jump forward to play the movie for one frame before it can pause properly. 
            frameCount=0
            dispMovie.pause()
    elif frameCount>=(dispMovie.duration*60)-3 and frameCount < (dispMovie.duration*60)-3 + ISI: # we're staring counting from 0, so count num frames and subtract 2 to get second-to-last frame. -3 for safety in rounding.
        dispMovie.pause()
        dispMovie.draw() #might want to have it vanish rather than leave it on the screen for the ISI, in which case comment out this line.
        frameCount += 1
        win.flip()
    elif frameCount >= (dispMovie.duration*60)-3 + ISI:
        dispMovie.draw()
        print('repeating at frame ' + str(frameCount))
        frameCount = 0
        win.flip()
    else:
        dispMovie.draw()
        frameCount+= 1
        win.flip()

def doExperiment():
    #the primary control function and main trial loop.
    global frameCount 
    statusSquareA.draw()
    statusTextA.draw()
    if verbose:
        statusSquareB.draw()
        statusTextB.draw()
    #primary trial loop, go until end of exp.
    runExp = True
    trialNum = 1
    trialText.text="Trial no. " + str(trialNum)
    readyText.text="Before first trial"
    trialText.draw()
    readyText.draw()
    win2.flip()
    #win.flip()
    if habituationDesign:
        if maxHabTrials > 0:
            trialType = 1 #here is where we must set trial type, if there are hab trials start with hab, if not goto test
            rdyTextAppend=" NEXT: HAB TRIAL"
        else:
            trialType = 2
            rdyTextAppend=" NEXT: TEST TRIAL"
    else:
        trialType = trialOrder[0]
        disMovie= actualTrialOrder[0]
        if trialOrder[0] == 1:
            rdyTextAppend=" NEXT: INTRO TRIAL"
        elif trialOrder[0] == 2:
            rdyTextAppend=" NEXT: FAM TRIAL"
        elif trialOrder[0] == 3:
            rdyTextAppend=" NEXT: TEST TRIAL"
    didRedo = False
    while runExp:
        statusSquareA.fillColor='black'
        statusSquareB.fillColor='black'
        #select movie for trial
        if habituationDesign:
            if trialType == 1: 
                disMovie = habMovies[cond[0]]
            elif trialType == 2:
                    disMovie = testMovies[cond[1]]
        else: #VoE design
            disMovie=actualTrialOrder[trialNum-1]
        disMovie.seek(0)
        while not keyboard[key.A]: #wait for 'ready' key, check at frame intervals
            statusSquareA.draw()
            readyText.text="No trial active" + rdyTextAppend
            trialText.draw()
            readyText.draw()
            if verbose:
                statusSquareB.draw()
            if keyboard[key.Y]:
                endExperiment([[0,0,0,0,0]],[[0,0,0,0,0]],trialNum,[],[]) #takes a bunch of arrays so we feed it blanks
                core.quit()
            elif keyboard[key.R] and not didRedo:
                if trialNum >1:
                    trialNum -= 1
                redoTrial(trialNum)
                didRedo = True
            elif keyboard[key.J] and not trialType == 2: #jump to test
                if habituationDesign:
                    trialType = 2
                else:
                    for z in range(0,len(trialOrder)):
                        if trialOrder[z] == 3:
                            trialType = actualTrialOrder[z]
                            trialNum = z
                            z=len(trialOrder)
                rdyTextAppend = " NEXT: TEST TRIAL"
            elif trialType == 2 and keyboard[key.I] and habituationDesign: #insert additional hab trial
                trialType =1
                rdyTextAppend = " NEXT: HAB TRIAL"
            win2.flip()
        frameCount = 0
        #framerate = win.getActualFrameRate() 
        #print(framerate)               #just some debug code.
        statusSquareA.fillColor='blue'
        statusTextA.text="RDY"
        statusSquareA.draw()
        statusTextA.draw()
        trialText.draw()
        readyText.text="Trial active"
        readyText.draw()
        if verbose:
            statusSquareB.fillColor='blue'
            statusTextB.text="RDY"
            statusSquareB.draw()
            statusTextB.draw()
        win2.flip()
        attnGetter() #plays the attention-getter
        core.wait(.1) #this wait is important to make the attentiongetter not look like it is turning into the stimulus
        frameCount=1
        dispTrial(0,disMovie)
        core.wait(.2) #this delay ensures that the trial only starts after the images have appeared on the screen, static, for 200ms
        waitStart = True
        while waitStart:
            if keyboard[key.Y]: #End experiment right there and then.
                endExperiment([[0,0,0,0,0]],[[0,0,0,0,0]],trialNum,[],[]) 
                core.quit()
            elif keyboard[key.A]:
                attnGetter()
                core.wait(.1)
                dispTrial(0,disMovie)
                core.wait(.2)
            elif keyboard[key.B]:
                waitStart = False
                statusSquareA.fillColor='green'
                statusTextA.text="ON"
                statusSquareA.draw()
                statusTextA.draw()
                trialText.draw()
                readyText.draw()
                if verbose:
                    if keyboard[key.L]: 
                        statusSquareB.fillColor='green'
                        statusTextB.text="ON"
                    else:
                        statusSquareB.fillColor='red'
                        statusTextB.text="OFF"
                    statusSquareB.draw()
                    statusTextB.draw()
                win2.flip()
            elif keyboard[key.R] and not didRedo: #Redo last trial, mark last trial as bad
                if trialNum > 0:
                    trialNum -= 1
                redoTrial(trialNum)
                didRedo = True
            elif keyboard[key.J] and not trialType == 2: #jump to test
                if habituationDesign:
                    trialType = 2
                else:
                    for z in range(0,len(trialOrder)):
                        if trialOrder[z] == 3:
                            trialType = actualTrialOrder[z]
                            trialNum = z
                            z=len(trialOrder)
                rdyTextAppend = " NEXT: TEST TRIAL"
            elif trialType == 2 and keyboard[key.I] and habituationDesign: #insert additional hab trial
                trialType =1
                rdyTextAppend = " NEXT: HAB TRIAL"
            else:
                dispTrial(0,disMovie)
        x = doTrial(trialNum, trialType,disMovie) #the actual trial, returning one of four status values at the end
        if x == 2: # end experiment, either due to final trial ending or 'end experiment altogether' button.
            runExp = False
            didRedo = False
        elif x == 3: #bad trial, redo!
            trialNum = trialNum
            didRedo = True
        elif x == 1: #goto test trial
            trialNum += 1
            trialType = 2
            rdyTextAppend=" NEXT: TEST TRIAL"
            didRedo = False
        elif x == 0: #continue hab
            trialNum += 1
            if habituationDesign:
                trialType = 1
            else:
                trialType = actualTrialOrder[trialNum-1]
                if trialOrder[trialNum-1] == 3:
                    rdyTextAppend=" NEXT: TEST TRIAL"
            didRedo = False


def doTrial(number, type,disMovie):
    print(number)
    trialText.text = "Trial no. " + str(number)
    global testTrialCount
    global numTestTrials
    global frameCount
    frameCount = 0 #reset display
    #returns 0 if do next hab trial, 1 if do test trial, 2 if done test trial (or end experiment), 3 if abort/redo
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
    readyText.text="Trial running"
    if keyboard[key.B]:
        gazeOn = True
        startOn = 0 #we want these to be 0 because every other time is put in reference to the startTrial timestamp so it's not some absurd number
        numOn = 1
    else:
        gazeOn = False
        numOff = 1
        startOff = 0
    if verbose:
        if keyboard[key.L]:
            gazeOn2 = True
            startOn2 = 0
            numOn2 = 1
        else:
            gazeOn2 = False
            numOff2 = 1
            startOff2 = 0
    while runTrial:
        if keyboard[key.F]: #'abort trial' is pressed
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
        elif keyboard[key.Y]: #the 'end the study' button, for fuss-outs (9 for lab, 6 for home test)
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
        elif core.getTime() - startTrial >= maxDur: #reached max trial duration
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
        elif not gazeOn: #if they are not looking as of the previous refresh, check if they have been looking away for too long
            nowOff = core.getTime() - startTrial
            if sumOn > minOn and nowOff - startOff >= maxOff: 
                #if they have previously looked for at least .5s and now looked away for 2 continuous sec
                runTrial = False
                endTrial = core.getTime() - startTrial
                endOff = nowOff
                offDur = nowOff - startOff
                tempGazeArray = [number, type, startOff, endOff, offDur]
                offArray.append(tempGazeArray)
            elif keyboard[key.B]: #if they have started looking since the last refresh and not met criterion
                gazeOn = True
                numOn = numOn + 1
                startOn = core.getTime() - startTrial
                endOff = core.getTime() - startTrial 
                #by definition, if this is tripped there will be a preceding 'off' section if this is tripped because gazeOn is set at start
                offDur = endOff - startOff
                tempGazeArray = [number, type, startOff, endOff, offDur]
                offArray.append(tempGazeArray)
        elif gazeOn and not keyboard[key.B]: #if they were looking and have looked away.
            gazeOn = False
            endOn = core.getTime() - startTrial
            onDur = endOn - startOn
            numOff = numOff + 1
            startOff = core.getTime() - startTrial
            tempGazeArray = [number, type, startOn, endOn, onDur]
            onArray.append(tempGazeArray)
            sumOn = sumOn + onDur 
        if verbose:
            if not gazeOn2: #if they are not looking as of the previous refresh
                nowOff2 = core.getTime() - startTrial2
                if keyboard[key.L]: #if they have started looking since the last refresh and not met criterion
                    gazeOn2 = True
                    numOn2 = numOn2 + 1
                    startOn2 = core.getTime() - startTrial2
                    endOff2 = core.getTime() - startTrial2
                    offDur2 = endOff2 - startOff2
                    tempGazeArray2 = [number, type, startOff2, endOff2, offDur2]
                    offArray2.append(tempGazeArray2)
            elif gazeOn2 and not keyboard[key.L]: #if they were looking and have looked away.
                gazeOn2 = False
                endOn2 = core.getTime() - startTrial2
                onDur2 = endOn2 - startOn2
                numOff2 = numOff2 + 1
                startOff2 = core.getTime() - startTrial2
                tempGazeArray2 = [number, type, startOn2, endOn2, onDur2]
                onArray2.append(tempGazeArray2)
                sumOn2 = sumOn2 + onDur2
        dispTrial(type,disMovie) 
    if verbose:
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
    statusSquareA.fillColor='black'
    statusSquareB.fillColor='black'
    statusTextA.text=""
    statusTextB.text=""
    statusSquareA.draw()
    readyText.draw()
    trialText.draw()
    if verbose:
        statusSquareB.draw()
    win2.flip()
    win.flip() #blanks the screen outright.
    if redo: #if the abort button was pressed
        abortTrial(onArray, offArray, number,type,onArray2, offArray2)
        return 3
    elif habituationDesign:
        if type == 1: #if still during habituation
            if checkStop(onArray, offArray, number, onArray2, offArray2):
                return 1
            else:
                return 0
        elif type == 2 and testTrialCount < numTestTrials:
            testTrialCount += 1 
            dataRec(onArray, offArray, number, type, onArray2, offArray2)
            return 1
        else: #should only be tripped on a (the last) test trial, or occasionally on the 'kill the whole experiment' button
            endExperiment(onArray, offArray, number, onArray2, offArray2)
            return 2
    elif not habituationDesign: #for VoE designs
        if number >= len(trialOrder):
            endExperiment(onArray, offArray, number, onArray2, offArray2)
            return 2
        else:
            dataRec(onArray, offArray, number, type, onArray2, offArray2)
            return 0 #with a set order, it doesn't really matter!

def endExperiment(onArray, offArray, trial, onArray2, offArray2):
    sumOn = 0
    sumOff = 0
    sumOn2 = 0
    sumOff2 = 0
    for i in range(0,len(onArray)):
        sumOn = sumOn + onArray[i][4]
    for j in range(0,len(offArray)):
        sumOff = sumOff + offArray[j][4]
    if len(onArray2)>0:
        for i in range(0,len(onArray2)):
            sumOn2 = sumOn2 + onArray2[i][4]
        for j in range(0,len(offArray2)):
            sumOff2 = sumOff2 + offArray2[j][4]
        verboseOn2.extend(onArray2)
        verboseOff2.extend(offArray2)
    #add to master gaze array
    verboseOn.extend(onArray)
    verboseOff.extend(offArray)
    #print verboseOn
    #print verboseOn2
    #data format: snum, age in months, age in days, sex, condition, trial, GNGtrial, trial type, hab crit, on-time, number of gazes, off-time, number of look-offs
    #then same again at the end for b-coder?
    tempData=[sNum, ageMo, ageDay, sex, cond, trial, 1, 2, habCrit, sumOn, len(onArray), sumOff, len(offArray),sumOn2,len(onArray2),sumOff2,len(offArray2)]
    #print tempData
    dataMatrix.append(tempData)
    #sort the data matrices and shuffle them together.
    if len(badTrials) > 0: #if there are any redos, they need to be shuffled in appropriately. 
        for i in range(0,len(badTrials)):
            x = 0
            while dataMatrix[x][5] != badTrials[i][5]:
                x += 1
            while dataMatrix[x][6] == 0: #this is to get around the possibility that the same trial had multiple 'false starts'
                x += 1
            dataMatrix.insert(x, badTrials[i]) #python makes this stupid easy
    #first, we create the headers
    headers = ['snum','months','days', 'sex', 'condition','trial','GNG','trialType','habCrit','onTime','numGazes','offTime', 'numOff','onTimeB','numGazesB','offTimeB','numOffB']
    #could check for existing data file to prevent overwrites?
    outputWriter = csv.writer(open(prefix+str(sNum)+'_'+str(sID)+'_'+str(today.month)+str(today.day)+str(today.year)+'.csv','w'), lineterminator ='\n') #careful! this OVERWRITES the existing file. Fills from snum.
    outputWriter.writerow(headers)
    for r in range(0, len(dataMatrix)):
        #print('writing rows')
        outputWriter.writerow(dataMatrix[r])
    if verbose: #if you want VERBOSE data as well as the regular stuff, there's a whole extra set of steps
        verboseMatrix = []
        #first, verbose data is not as well organized. However, we should be able to alternate back and forth between 
        #on and off until we reach the end of a given trial, to reconstruct it.
        #at the start of each line, add information: sNum, ageMo, ageDay, sex, cond, GNG, ON/OFF
        for n in range(0, len(verboseOn)):
            verboseOn[n][0:0]=[sNum, ageMo, ageDay, sex, cond,1,1]
        for m in range(0, len(verboseOff)):# adding the details to the verbose array
            verboseOff[m][0:0]=[sNum, ageMo, ageDay, sex, cond,1,0]
        if len(badTrials)>0:
            for o in range(0,len(badVerboseOn)):
                badVerboseOn[o][0:0]=[sNum, ageMo, ageDay, sex,cond,0,1]
            for p in range(0,len(badVerboseOff)):#same details for the bad trials
                badVerboseOff[p][0:0]=[sNum, ageMo, ageDay, sex,cond,0,0]
        #read the final data matrix and go trial by trial.
        #print(verboseOn) #debug, to make sure verboseOn is being constructed correctly
        for q in range(0, len(dataMatrix)):
            tnum = dataMatrix[q][5]
            onIndex = -1
            offIndex = -1
            onOff = 1 #1 for on, 0 for off, for alternating
            if dataMatrix[q][6] == 1: #separate for good and bad trials
                for x in range(0, len(verboseOn)): 
                    if verboseOn[x][7] == tnum and onIndex == -1: #find the right index in the verbose matrices
                        onIndex = x
                for y in range(0, len(verboseOff)):
                    if verboseOff[y][7] == tnum and offIndex == -1: 
                        offIndex = y
                # so now the challenge is figuring out what happens when the trial number is missing from one of the arrays
                if onIndex >= 0 and offIndex >= 0: #just making sure both are present. If not we get complex
                    if verboseOn[onIndex][9] < verboseOff[offIndex][9]: #if the trial started on a gaze. Currently always will, but want to give option not to
                        onOff = 1
                    else:
                        onOff = 0
                    while verboseOn[onIndex][7] == tnum or verboseOff[offIndex][7] == tnum: #either one is still part of the trial
                        #if somehow the alternation breaks down, so does this loop, but that should be impossible. If you get
                        #a 60-sec-on trial, then after the first gaze it should immediately end after the first iteration.
                        #the last trial, however, is almost guaranteed to go out of bounds and throw an error
                        if onOff == 1: #append the next line of verboseOn
                            verboseMatrix.append(verboseOn[onIndex])
                            onIndex += 1
                            onOff = 0
                        elif onOff == 0: #append the next line of verboseOff
                            verboseMatrix.append(verboseOff[offIndex])
                            offIndex += 1
                            onOff = 1
                        if onIndex == len(verboseOn):
                            onIndex = 0 #ensures that we don't get out-of-range errors. If the whole experiment has exactly one trial it whiffs...I call that fine
                        if offIndex == len(verboseOff):
                            offIndex = 0
                else: #special case: One gaze type is missing altogether (most frequently 60-second-on trial)
                    if onIndex >=0:
                        while verboseOn[onIndex][7] == tnum:
                            verboseMatrix.append(verboseOn[onIndex])
                            onIndex += 1
                            if onIndex == len(verboseOn):
                                onIndex = 0
                    elif offIndex >=0:
                        while verboseOff[offIndex][7]==tnum:
                            verboseMatrix.append(verboseOff[offIndex])
                            offIndex += 1
                            if offIndex == len(verboseOff):
                                offIndex = 0 #catching final-trial overflow issues
            elif dataMatrix[q][6]==0: #bad trials. These arrays will be much less predictable, so putting them together is inherently more challenging
                if q > 0 and dataMatrix[q-1][6]==0: 
                    pass #stops it from doubling up. If there is more than one consecutive bad trial, it will get all of them in a row the first time,
                else:
                    for x in range(0,len(badVerboseOn)):
                        if badVerboseOn[x][7] == tnum and onIndex == -1:
                            onIndex = x
                    for y in range(0, len(badVerboseOff)): 
                        if badVerboseOff[y][7] == tnum and offIndex == -1:
                            offIndex = y
                    if onIndex >= 0 and offIndex >= 0: #making sure we have both gaze types for interweaving
                        if badVerboseOn[onIndex][9] < badVerboseOff[offIndex][9]: #if the trial started on a gaze.
                            onOff = 1
                        else:
                            onOff = 0
                        weaving = True
                        onDone = False
                        offDone = False
                        while weaving: #Current state: Gets a little garbled (but does not fail) if there are multiple redos on the same trial. Otherwise, fine.
                            if onOff == 1:
                                verboseMatrix.append(badVerboseOn[onIndex])
                                onIndex += 1
                                onOff = 0
                                if offDone:
                                    onOff = 1
                                if onIndex == len(badVerboseOn):
                                    onDone = True
                                elif not badVerboseOn[onIndex][7] == tnum:
                                    onDone = True
                            elif onOff == 0:
                                verboseMatrix.append(badVerboseOff[offIndex])
                                offIndex += 1
                                onOff = 1
                                if onDone:
                                    onOff=0
                                if offIndex == len(badVerboseOff):
                                    offDone = True
                                elif not badVerboseOff[offIndex][7] == tnum:
                                    offDone = True
                            if onDone and offDone:
                                weaving = False
                    else: #if we don't even have an entry in one or the other (on or off)
                        weaving = True
                        if onIndex >=0:
                            while weaving and badVerboseOn[onIndex][7] == tnum:
                                verboseMatrix.append(badVerboseOn[onIndex])
                                onIndex += 1
                                if onIndex == len(badVerboseOn):
                                    weaving = False
                                    onIndex -= 1
                        elif offIndex >=0:
                            while weaving and badVerboseOff[offIndex][7]==tnum:
                                verboseMatrix.append(badVerboseOff[offIndex])
                                offIndex += 1
                                if offIndex == len(badVerboseOff):
                                    weaving = False #catching final-trial overflow issues
                                    offIndex -= 1
        outputWriter2 = csv.writer(open(prefix+str(sNum)+'_'+str(sID)+'_'+str(today.month)+str(today.day)+str(today.year)+'_VERBOSE.csv','w'), lineterminator ='\n') #careful! this OVERWRITES the existing file. Fills from snum.
        headers2=['snum', 'months', 'days', 'sex','cond','GNG','gazeOnOff','trial','trialType','startTime','endTime','duration']
        outputWriter2.writerow(headers2)
        for z in range(0,len(verboseMatrix)):
            outputWriter2.writerow(verboseMatrix[z])
        if verbose and len(verboseOn2)>0:
            verboseMatrix2 = []
            for n in range(0, len(verboseOn2)):
                verboseOn2[n][0:0]=[sNum, ageMo, ageDay, sex, cond,1,1]
            for m in range(0, len(verboseOff2)):
                verboseOff2[m][0:0]=[sNum, ageMo, ageDay, sex, cond,1,0]
            if len(badTrials)>0:
                for o in range(0,len(badVerboseOn2)):
                    badVerboseOn2[o][0:0]=[sNum, ageMo, ageDay, sex,cond,0,1]
                for p in range(0,len(badVerboseOff2)):
                    badVerboseOff2[p][0:0]=[sNum, ageMo, ageDay, sex,cond,0,0]
        #read the final data matrix and go trial by trial.
        #print(verboseOn) #debug, to make sure verboseOn is being constructed correctly
            for q in range(0, len(dataMatrix)):
                tnum = dataMatrix[q][5]
                onIndex2 = -1
                offIndex2 = -1
                onOff2 = 1 #1 for on, 0 for off, for alternating
                if dataMatrix[q][6] == 1: #separate for good and bad trials
                    for x in range(0, len(verboseOn2)): 
                        if verboseOn2[x][7] == tnum and onIndex2 == -1: #find the right index in the verbose matrices
                            onIndex2 = x
                    for y in range(0, len(verboseOff2)):
                        if verboseOff2[y][7] == tnum and offIndex2 == -1: 
                            offIndex2 = y
                # so now the challenge is figuring out what happens when the trial number is missing from one of the arrays
                    if onIndex2 >= 0 and offIndex2 >= 0: #just making sure both are present. If not we get complex
                        if verboseOn2[onIndex2][9] < verboseOff2[offIndex2][9]: #if the trial started on a gaze. Currently always will, but want to give option not to
                            onOff2 = 1
                        else:
                            onOff2 = 0
                        while verboseOn2[onIndex2][7] == tnum or verboseOff2[offIndex2][7] == tnum: #either one is still part of the trial
                            #if somehow the alternation breaks down, so does this loop, but that should be impossible. If you get
                        #a 60-sec-on trial, then after the first gaze it should immediately end after the first iteration.
                        #the last trial, however, is almost guaranteed to go out of bounds and throw an error
                            if onOff2 == 1: #append the next line of verboseOn
                                verboseMatrix2.append(verboseOn2[onIndex2])
                                onIndex2 += 1
                                onOff2 = 0
                            elif onOff2 == 0: #append the next line of verboseOff
                                verboseMatrix2.append(verboseOff2[offIndex2])
                                offIndex2 += 1
                                onOff2 = 1
                            if onIndex2 == len(verboseOn2):
                                onIndex2 = 0 #ensures that we don't get out-of-range errors. If the whole experiment has exactly one trial it whiffs...I call that fine
                            if offIndex2 == len(verboseOff2):
                                offIndex2 = 0
                    else: #special case: One gaze type is missing altogether (most frequently 60-second-on trial)
                        if onIndex2 >=0:
                            while verboseOn2[onIndex2][7] == tnum:
                                verboseMatrix2.append(verboseOn2[onIndex2])
                                onIndex2 += 1
                                if onIndex2 == len(verboseOn2):
                                    onIndex2 = 0
                        elif offIndex2 >=0:
                            while verboseOff2[offIndex2][7]==tnum:
                                verboseMatrix2.append(verboseOff2[offIndex2])
                                offIndex2 += 1
                                if offIndex2 == len(verboseOff2):
                                    offIndex2 = 0 #catching final-trial overflow issues
                elif dataMatrix[q][6]==0: #bad trials. These arrays will be much less predictable, so putting them together is inherently more challenging
                    if q > 0 and dataMatrix[q-1][6]==0: 
                        pass #stops it from doubling up. If there is more than one consecutive bad trial, it will get all of them in a row the first time,
                    else:
                        for x in range(0,len(badVerboseOn2)):
                            if badVerboseOn2[x][7] == tnum and onIndex2 == -1:
                                onIndex2  = x
                        for y in range(0, len(badVerboseOff2)): 
                            if badVerboseOff2[y][7] == tnum and offIndex2 == -1:
                                offIndex2 = y
                        if onIndex2 >=0 and offIndex2 >= 0: #making sure we have both gaze types for interweaving
                            if badVerboseOn2[onIndex2][9] < badVerboseOff2[offIndex2][9]: #if the trial started on a gaze.
                                onOff2 = 1
                            else:
                                onOff2 = 0
                            weaving2 = True
                            onDone2 = False
                            offDone2 = False
                            while weaving: #Current state: Gets a little garbled (but does not fail) if there are multiple redos on the same trial. Otherwise, fine.
                                if onOff2 == 1:
                                    verboseMatrix2.append(badVerboseOn2[onIndex2])
                                    onIndex2 += 1
                                    onOff2 = 0
                                    if offDone2:
                                        onOff2 = 1
                                    if onIndex2 == len(badVerboseOn2):
                                        onDone2 = True
                                    elif not badVerboseOn[onIndex2][7] == tnum:
                                        onDone2 = True
                                elif onOff2 == 0:
                                    verboseMatrix2.append(badVerboseOff2[offIndex2])
                                    offIndex2 += 1
                                    onOff2 = 1
                                    if onDone2:
                                        onOff2=0
                                    if offIndex2 == len(badVerboseOff2):
                                        offDone2 = True
                                    elif not badVerboseOff2[offIndex2][7] == tnum:
                                        offDone2 = True
                                if onDone2 and offDone2:
                                    weaving2 = False
                        else: #if we don't even have an entry in one or the other (on or off)
                            weaving2 = True
                            if onIndex2 >=0:
                                while weaving2 and badVerboseOn2[onIndex2][7] == tnum:
                                    verboseMatrix2.append(badVerboseOn2[onIndex2])
                                    onIndex2 += 1
                                    if onIndex2 == len(badVerboseOn2):
                                        weaving2 = False
                                        onIndex2 -= 1
                            elif offIndex2 >=0:
                                while weaving2 and badVerboseOff2[offIndex2][7]==tnum:
                                    verboseMatrix2.append(badVerboseOff2[offIndex2])
                                    offIndex2 += 1
                                    if offIndex2 == len(badVerboseOff2):
                                        weaving2 = False #catching final-trial overflow issues
                                        offIndex2 -= 1
            outputWriter3 = csv.writer(open(prefix+str(sNum)+'_'+str(sID)+'_'+str(today.month)+str(today.day)+str(today.year)+'_VERBOSEb.csv','w'), lineterminator ='\n') 
            outputWriter3.writerow(headers2)
            for k in range(0,len(verboseMatrix2)):
                outputWriter3.writerow(verboseMatrix2[k])
            rel=reliability(verboseMatrix, verboseMatrix2)
            outputWriter4 = csv.writer(open(prefix+str(sNum)+'_'+str(sID)+'_'+str(today.month)+str(today.day)+str(today.year)+'_Stats.csv','w'), lineterminator ='\n')
            headers3=['WeightedPercentageAgreement', 'CohensKappa','AverageObserverAgreement','PearsonsR']
            outputWriter4.writerow(headers3)
            outputWriter4.writerow(rel)
    core.wait(.3)
    win2.close()
    core.quit()

def reliability(verboseMatrix, verboseMatrix2):
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
    for i in dataMatrix:
        if i[6]!=0:
            trialA.append(i[9])
            trialB.append(i[13])
            avA+=i[9]
            avB+=i[13]
    avA=avA/dataMatrix[-1][5]
    avB=avB/dataMatrix[-1][5]
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
    for i in range(0, dataMatrix[-1][5]):
        a=0
        d=0
        for (m, l) in zip(timewarp, timewarp2):
            if m[0]==i+1 and l[0]==i+1:
                if m[1]==l[1]:
                    a+=1
                else:
                    d+=1
        tg=tg + float(a)/(a+d)
    aoagreement=str(float(tg)/dataMatrix[-1][5])
    stats.append(aoagreement)
    stats.append(r)
    return stats

startDlg = gui.Dlg(title=prefix + ' Movie Presentation Experiment')
startDlg.addText('Subject info')
startDlg.addField('Subject Number: ')
startDlg.addField('Subject ID: ')
startDlg.addField('sex: ')
startDlg.addField('DOB(month): ')
startDlg.addField('DOB(day): ')
startDlg.addField('DOB(year): ')
if randPres:
    startDlg.addField('Cond: ', choices=condList)
else:
    startDlg.addField('Cond: ')
startDlg.addField('Verbose data/multiple coders? ', choices=['Y','N'])
startDlg.show()
if startDlg.OK:
    win = visual.Window((1280.0,800.0),fullscr=False, screen=1,allowGUI=False, units='pix', rgb=[-1,-1,-1])
    win2 = visual.Window((400,400),fullscr=False,screen=0,allowGUI=False,units='pix',waitBlanking=False, rgb=[-1,-1,-1])
    thisInfo = startDlg.data
    sNum = thisInfo[0]
    sID = thisInfo[1]
    sex = thisInfo[2]
    #now for the exciting bit: converting DOB into months/days.
    today = date.today()
    DOB = date(2000+int(thisInfo[5]), int(thisInfo[3]), int(thisInfo[4]))
    DOT = today
    #The simplest solution (which is not ideal) is to just get the built-in timedelta in days and divide by 30, and get the remainder.
    #The problem with that is that it's not likely to be neat or accurate.
    #The more complicated solution involves checking if the days line up, then the months, then years.
    if DOT.day < DOB.day:
        dayCount = DOT.day + 30
        if DOT.month<DOB.month:
            monthCount = DOT.month + 11
        elif DOT.month>1:
            monthCount = DOT.month-1
        else:
            monthCount = 12
    else:
        dayCount = today.day
        if DOT.month < DOB.month:
            monthCount = DOT.month + 12
        else:
            monthCount = DOT.month
    if DOB.year < DOT.year-1:
        monthCount += 12*(DOT.year-DOB.year)
    ageMo = monthCount - DOB.month
    ageDay = dayCount - DOB.day 
    #here is where we set the condition from a separate file that no human gets to see, disabled in demo mode
    if habituationDesign:
        testReader=csv.reader(open(condPath+condFile, 'rU')) #if running from a cond list file, in format [1,2] hab,test
        testStuff=[]
        for row in testReader:
            testStuff.append(row)
        testDict = dict(testStuff)
        cond = testDict[thisInfo[6]] 
        cond=eval(cond)
        #cond=thisInfo[6] #demo mode
        if len(introMovieNames) > 0:
            introMovies=[]
            for k in range(0, len(introMovieNames)):
                tempMovie = visual.MovieStim3(win, moviePath+introMovieNames[k]+movieExt, flipHoriz=False, flipVert=False, loop=False)
                introMovies.append(tempMovie)
                print 'duration=%.2fs' %(tempMovie.duration)
        habMovies = [] #array of moviestim objects for the hab trials
        for i in range(0, len(habMovieNames)): #preload all the hab movies
            tempMovie = visual.MovieStim3(win, moviePath+habMovieNames[i]+movieExt, flipHoriz=False, flipVert=False, loop=False)
            habMovies.append(tempMovie)
            print 'duration=%.2fs' %(tempMovie.duration)
        testMovies = []
        for j in range(0, len(testMovieNames)): #preload all the test movies
            tempMovie = visual.MovieStim3(win, moviePath+testMovieNames[j]+movieExt, flipHoriz=False, flipVert=False, loop=False)
            testMovies.append(tempMovie)
    else: #familiarization design: build trial order
        actualTrialOrder=[]
        lastFam = 0
        lastTest = 0
        lastIntro = 0
        if randPres:
            testReader=csv.reader(open(condFile,'rU'))
            testStuff=[]
            for row in testReader:
                testStuff.append(row)
            testDict = dict(testStuff)
            cond = testDict[thisInfo[6]]  #this will read as order of indeces in three groups, intro, fam, test, in a 2-dim array (hopefully)
            #type conversion required. Eval will read the string into a list.
            cond=eval(cond)
            #now to rearrange the lists of each trial type
            if len(introMovieNames) > 0:
                newIntroTrials=[]
                for q in range(0, len(introMovieNames)):
                    newIntroTrials.append(introMovieNames[cond[0][q]-1])
                introMovieNames = newIntroTrials
            if len(habMovieNames) > 0:
                newFamTrials=[]
                for r in range(0, len(habMovieNames)):
                    newFamTrials.append(habMovieNames[cond[1][r]-1])
                habMovieNames = newFamTrials        
            #you must have at least one test trial
            newTestTrials=[]
            for s in range(0, len(testMovieNames)):
                newTestTrials.append(testMovieNames[cond[2][s]-1])
            testMovieNames=newTestTrials
        else:
            cond=thisInfo[6]
        if len(introMovieNames) > 0:
            introMovies=[]
            for k in range(0, len(introMovieNames)):
                tempMovie = visual.MovieStim3(win, moviePath+introMovieNames[k]+movieExt, flipHoriz=False, flipVert=False, loop=False)
                introMovies.append(tempMovie)
                print 'duration=%.2fs' %(tempMovie.duration)
        habMovies = [] #array of moviestim objects for the hab trials
        for i in range(0, len(habMovieNames)): #preload all the hab movies
            tempMovie = visual.MovieStim3(win, moviePath+habMovieNames[i]+movieExt, flipHoriz=False, flipVert=False, loop=False)
            habMovies.append(tempMovie)
            print 'duration=%.2fs' %(tempMovie.duration)
        testMovies = []
        for j in range(0, len(testMovieNames)): #preload all the test movies
            tempMovie = visual.MovieStim3(win, moviePath+testMovieNames[j]+movieExt, flipHoriz=False, flipVert=False, loop=False)
            testMovies.append(tempMovie)
        for i in range(0, len(trialOrder)): #now that we've configured the internal order as needed, we can build our actual trials
            if trialOrder[i] == 1: #intro trial
                actualTrialOrder.append(introMovies[lastIntro])
                lastIntro += 1
                if lastIntro >= len(introMovies):
                    lastIntro = 0
            elif trialOrder[i] == 2: #familiarization trial
                actualTrialOrder.append(habMovies[lastFam])
                lastFam += 1
                if lastFam >= len(habMovies):
                    lastFam = 0
            elif trialOrder[i] == 3: #test trial
                actualTrialOrder.append(testMovies[lastTest])
                lastTest += 1
                if lastTest >= len(testMovies):
                    lastTest = 0
    verbose = thisInfo[7]
    #notably, using pygame here breaks visual.TextStim, so your text need to be in some other format if you are
    #presenting text-based stimuli (which you almost never will be)
    key=pyglet.window.key
    keyboard = key.KeyStateHandler()
    win.winHandle.push_handlers(keyboard)
    win2.winHandle.push_handlers(keyboard)
    attnGetterSquare = visual.Rect(win, height=40, width=40, pos=[testOffset+0,0], fillColor='black')
    #testSquareA=visual.Rect(win, height=80, width=80, pos=[testOffset-560,0], fillColor='red', lineColor='red')
    #testSquareB=visual.Rect(win, height=80, width=80, pos=[testOffset+0,0], fillColor='green', lineColor='green')
    statusSquareA=visual.Rect(win2, height=80, width=80, pos=[statusOffset-60, statusOffsetY+0], fillColor='black')# These two appear on the status screen window.
    statusSquareB=visual.Rect(win2, height=80, width=80, pos=[statusOffset+60, statusOffsetY+0], fillColor='black') 
    statusTextA = visual.TextStim(win2, text="", pos=[statusOffset-60, statusOffsetY+0], color='white', bold=True, height=30)
    statusTextB = visual.TextStim(win2, text="", pos=[statusOffset+60, statusOffsetY+0],color='white', bold=True, height=30)
    trialText = visual.TextStim(win2, text="Trial no: ", pos = [-150,150], color='white')
    readyText = visual.TextStim(win2, text="Trial not active", pos=[-25,100], color='white')
    doExperiment() #Get this show on the road!
    
