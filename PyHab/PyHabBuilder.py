from psychopy import visual, event, core, gui, monitors, tools, sound,__version__
import wx, random, csv, shutil, os
from math import *
from datetime import *

# This program designed to *create* PyHab files using a relatively straightforward GUI. Hoo boy.
# Outputs a folder. Folder contains a launcher script that allows PyHab to either run or edit.
# The class takes the settings dict, failing that it has a blank to fill in.
#To fix: A better way of removing movies from a trial type.

class pyHabBuilder():
    def __init__(self, loadedSaved=False, settingsDict={}):
        self.loadSave = loadedSaved #For easy reference elsewhere
        if os.name is 'posix': #glorious simplicity of unix filesystem
            self.dirMarker = '/'
        elif os.name is 'nt': #Nonsensical Windows-based contrarianism
            self.dirMarker='\\'
        #The base window
        width = 1080
        height = 600
        self.win = visual.Window((width,height),fullscr=False, allowGUI=True, rgb=[-1,-1,-1], units='norm') #Using normalized units.
        self.flowArea = [-1,.75,1,0] #norm units go from -1 to +1. To cover the top half of the screen would be -1 to 1, and 1 to 0. X,X,Y,Y
        self.flowRect = visual.Rect(self.win, width=self.flowArea[1]-self.flowArea[0],height=self.flowArea[3]-self.flowArea[2], fillColor='grey',
                pos=[self.flowArea[0]+float(abs(self.flowArea[1]-self.flowArea[0]))/2,self.flowArea[2]-float(abs(self.flowArea[3]-self.flowArea[2]))/2])
        self.paletteArea = [.75,float(1),float(1),0] #a trial type pallette, bottom right for now.
        self.paletteRect = visual.Rect(self.win, width=self.paletteArea[1]-self.paletteArea[0],height=self.paletteArea[3]-self.paletteArea[2], fillColor='white',
                pos=[self.paletteArea[0]+float(abs(self.paletteArea[1]-self.paletteArea[0]))/2,self.paletteArea[2]-float(abs(self.paletteArea[3]-self.paletteArea[2]))/2])
        self.aspect = float(height)/float(width) #Determine aspect ratio width/height. Impt. for using norm.
        #A bunch of useful stuff for drawing the interface
        self.colorsArray= ['red','blue','green','purple','brown','LightSeaGreen','gold','Magenta'] #colors for dif trial types. Will eventually need an arbitrary number...
        self.flowWidthObj = .06*float(abs(self.flowArea[1]-self.flowArea[0])) #Width of one item in the flow, though this will possibly have to change...
        self.flowHeightObj = (self.flowWidthObj/self.aspect)*.8
        self.typeWidthObj = .4*float(abs(self.paletteArea[1]-self.paletteArea[0])) #Width of one item in the flow, though this will possibly have to change...
        self.typeHeightObj = (self.typeWidthObj/self.aspect)*.6
        self.typeLocs =[]
        self.flowLocs =[]
        self.condDict = {} #For creating conditions
        self.mouse = event.Mouse()
        for x in [.25,.75]: #Two columns of trial types
            for z in range(1,5):
                self.typeLocs.append([self.paletteArea[0]+x*(self.paletteArea[1]-self.paletteArea[0]), self.paletteArea[2]+.2*(self.paletteArea[3]-self.paletteArea[2])+z*.15*(self.paletteArea[3]-self.paletteArea[2])])
        for y in [.25,.75]: #two rows for the study flow.
            for z in range(1,11):
                    self.flowLocs.append([self.flowArea[0]+z*(self.flowArea[1]-self.flowArea[0])*.09, self.flowArea[2]+y*(self.flowArea[3]-self.flowArea[2])])
        #loadedSaved is "is this a new experiment or are we operating inside an existing experiment's folder?"
        if not loadedSaved: #A new blank experiment
            #Load some defaults to start with.
            self.settings={'dataColumns': ['sNum', 'months', 'days', 'sex', 'cond','condLabel', 'trial','GNG','trialType','stimName','habCrit','sumOnA','numOnA','sumOffA','numOffA','sumOnB','numOnB','sumOffB','numOffB'], 
                                                        'prefix': 'PyHab', 
                                                        'dataloc':'data'+self.dirMarker,
                                                        'maxDur': { }, 
                                                        'playThrough': [], 
                                                        'maxOff': '2', 
                                                        'minOn': '1', 
                                                        'blindPres': '0', 
                                                        'autoAdvance': '0', 
                                                        'randPres': '0', 
                                                        'condPath': '', 
                                                        'condFile': '', 
                                                        'condList': [ ],
                                                        'trialOrder': [], 
                                                        'maxHabTrials': '14',
                                                        'setCritWindow': '3', 
                                                        'setCritDivisor': '2', 
                                                        'metCritWindow': '3', 
                                                        'metCritDivisor': '1', 
                                                        'stimPres': 0,  #Will be set on each run anyways.
                                                        'moviePath': 'stimuli'+self.dirMarker, 
                                                        'movieNames':{}, 
                                                        'movieExt': '', 
                                                        'screenWidth': 1080, 
                                                        'screenHeight': 700, 
                                                        'movieWidth': 800, 
                                                        'movieHeight': 600, 
                                                        'screenIndex': '1', 
                                                        'ISI': '0',
                                                        'freezeFrame': '0.2',
                                                        'playAttnGetter': '1',
                                                        'folderPath':'',
                                                        'trialTypes':[],
                                                        'prefLook':'0'}
            self.studyFlowArray={'lines':[],'shapes':[],'text':[],'labels':[]} # an array of objects for the study flow.
            self.trialTypesArray={'shapes':[],'text':[],'labels':[]}
        else:
            self.settings = settingsDict
            evalList = ['dataColumns','maxDur','condList','playThrough','trialOrder','movieNames','trialTypes'] #eval all the things that need eval.
            for i in evalList:
                self.settings[i] = eval(self.settings[i])
            self.trialTypesArray = self.loadTypes()
            self.studyFlowArray=self.loadFlow()
            #Get conditions!
            if self.settings['randPres'] in [1,'1'] or len(self.settings['condFile'])>0: #If there is a random presentation file...
                testReader=csv.reader(open(self.settings['condFile'],'rU'))
                testStuff=[]
                for row in testReader:
                    testStuff.append(row)
                testDict = dict(testStuff) 
                for i in testDict.keys():
                    testDict[i] = eval(testDict[i]) 
                self.condDict = testDict
            self.settings['folderPath'] = os.getcwd()+self.dirMarker #On load, reset the folder path to wherever you are now.
        self.folderPath = self.settings['folderPath'] #The location where all the pieces are saved.
        self.allDataColumns=['sNum', 'months', 'days', 'sex', 'cond','condLabel', 'trial','GNG','trialType','stimName','habCrit','sumOnA','numOnA','sumOffA','numOffA','sumOnB','numOnB','sumOffB','numOffB']
        self.allDataColumnsPL =['sNum', 'months', 'days', 'sex', 'cond','condLabel','trial','GNG','trialType','stimName','habCrit', 'sumOnL','numOnL','sumOnR','numOnR','sumOff','numOff']
        self.stimSource={} #A list of the source folder(s) for each stimulus file, a dict where each key is the filename in movienames?
        self.allDone=False
        #Various main UI buttons, put into a dict of lists for easy looping through.
        self.buttonList={'shapes':[],'text':[],'functions':[]}#Yes, python means we can put the functions in there too.
        if len(self.folderPath) > 0:
            #Make a "save" button, not just a "save as" button, but only if there is a place to save to!
            saveButton = visual.Rect(self.win,width=.15, height=.67*(.15/self.aspect), pos=[-.52,-.9],fillColor="green")
            saveText = visual.TextStim(self.win, text="SAVE",color="black",height=saveButton.height*.5, pos=saveButton.pos)
            self.buttonList['shapes'].append(saveButton)
            self.buttonList['text'].append(saveText)
            self.buttonList['functions'].append(self.saveEverything)
        saveAsButton = visual.Rect(self.win,width=.15, height=.67*(.15/self.aspect), pos=[-.22,-.9],fillColor="green")
        saveAsText = visual.TextStim(self.win, text="Save as",color="black",height=saveAsButton.height*.3, pos=saveAsButton.pos)
        self.buttonList['shapes'].append(saveAsButton)
        self.buttonList['text'].append(saveAsText)
        self.buttonList['functions'].append(self.saveDlg)
        newTrialTypeButton = visual.Rect(self.win, width=.9*(self.paletteArea[1]-self.paletteArea[0]),height=abs(self.paletteArea[3]-self.paletteArea[2])*.10, fillColor="yellow", lineColor="black",
                pos=[self.paletteArea[0]+float(abs(self.paletteArea[1]-self.paletteArea[0]))/2,self.paletteArea[2]-float(abs(self.paletteArea[3]-self.paletteArea[2])/12)])
        newTrialTypeText=visual.TextStim(self.win, alignHoriz='center', alignVert='center', text = "New Trial Type",height=.55*newTrialTypeButton.height, pos=newTrialTypeButton.pos,color="black")
        self.buttonList['shapes'].append(newTrialTypeButton)
        self.buttonList['text'].append(newTrialTypeText)
        self.buttonList['functions'].append(self.trialTypeDlg)
        delTrialTypeButton = visual.Rect(self.win, width=.9*(self.paletteArea[1]-self.paletteArea[0]),height=abs(self.paletteArea[3]-self.paletteArea[2])*.10, fillColor="red", lineColor = "black",
                pos=[self.paletteArea[0]+float(abs(self.paletteArea[1]-self.paletteArea[0]))/2,self.paletteArea[3]+float(abs(self.paletteArea[3]-self.paletteArea[2])/12)])
        delTrialTypeText=visual.TextStim(self.win, alignHoriz='center', alignVert='center', text = "Delete a trial type",height=.45*delTrialTypeButton.height, pos=delTrialTypeButton.pos,color="black")
        self.buttonList['shapes'].append(delTrialTypeButton)
        self.buttonList['text'].append(delTrialTypeText)
        self.buttonList['functions'].append(self.delTrialTypeDlg)
        addHabButton = visual.Rect(self.win, width=.9*(self.paletteArea[1]-self.paletteArea[0]),height=abs(self.paletteArea[3]-self.paletteArea[2])*.10, fillColor="yellow", lineColor="black",
                pos=[self.paletteArea[0]+float(abs(self.paletteArea[1]-self.paletteArea[0]))/2,self.paletteArea[2]-float(abs(self.paletteArea[3]-self.paletteArea[2])*.2)])
        addHabText=visual.TextStim(self.win, alignHoriz='center', alignVert='center', text = "Add Hab Block",height=.55*addHabButton.height, pos=addHabButton.pos,color="black")
        self.buttonList['shapes'].append(addHabButton)
        self.buttonList['text'].append(addHabText)
        self.buttonList['functions'].append(self.addHabBlock)
        quitButton = visual.Rect(self.win,width=.15, height=.67*(.15/self.aspect), pos=[-.82,-.9],fillColor="red")
        quitText = visual.TextStim(self.win, text="QUIT",color="black",height=quitButton.height*.5, pos=quitButton.pos)
        self.buttonList['shapes'].append(quitButton)
        self.buttonList['text'].append(quitText)
        self.buttonList['functions'].append(self.quitFunc)
        USetButton = visual.Rect(self.win, width=.4, height=.5*(.2/self.aspect),pos=[-.57,-.2], fillColor="white")
        USetText = visual.TextStim(self.win, text="Universal \nsettings",color="black",height=USetButton.height*.3, alignHoriz='center', pos=USetButton.pos)
        self.buttonList['shapes'].append(USetButton)
        self.buttonList['text'].append(USetText)
        self.buttonList['functions'].append(self.univSettingsDlg)
        dataSetButton = visual.Rect(self.win, width=.4, height=.5*(.2/self.aspect),pos=[-.57,-.6], fillColor="white")
        dataSetText = visual.TextStim(self.win, text="Data \nsettings",color="black",height=dataSetButton.height*.3, alignHoriz='center', pos=dataSetButton.pos)
        self.buttonList['shapes'].append(dataSetButton)
        self.buttonList['text'].append(dataSetText)
        self.buttonList['functions'].append(self.dataSettingsDlg)
        stimSetButton = visual.Rect(self.win, width=.4, height=.5*(.2/self.aspect),pos=[-.02,-.2], fillColor="white")
        stimSetText = visual.TextStim(self.win, text="Stimuli \nsettings",color="black",height=stimSetButton.height*.3, alignHoriz='center', pos=stimSetButton.pos)
        self.buttonList['shapes'].append(stimSetButton)
        self.buttonList['text'].append(stimSetText)
        self.buttonList['functions'].append(self.stimSettingsDlg)
        condSetButton = visual.Rect(self.win, width=.4, height=.5*(.2/self.aspect),pos=[-.02,-.6], fillColor="white")
        condSetText = visual.TextStim(self.win, text="Condition \nsettings",color="black",height=condSetButton.height*.3, alignHoriz='center', pos=condSetButton.pos)
        self.buttonList['shapes'].append(condSetButton)
        self.buttonList['text'].append(condSetText)
        self.buttonList['functions'].append(self.condSettingsDlg)
        habSetButton = visual.Rect(self.win, width=.4, height=.5*(.2/self.aspect),pos=[.55,-.2], fillColor="white")
        habSetText = visual.TextStim(self.win, text="Habituation \nsettings",color="black",height=habSetButton.height*.3, alignHoriz='center', pos=habSetButton.pos)
        self.buttonList['shapes'].append(habSetButton)
        self.buttonList['text'].append(habSetText)
        self.buttonList['functions'].append(self.habSettingsDlg)
        addMovButton = visual.Rect(self.win, width=.4, height=.5*(.2/self.aspect),pos=[.55,-.6], fillColor="white")
        addMovText = visual.TextStim(self.win, text="Add movie files \nto trial types",color="black",height=addMovButton.height*.3, alignHoriz='center', pos=addMovButton.pos)
        self.buttonList['shapes'].append(addMovButton)
        self.buttonList['text'].append(addMovText)
        self.buttonList['functions'].append(self.addMoviesToTypesDlg)
        
        self.workingRect = visual.Rect(self.win, width=1, height=.5, pos=[0,0], fillColor = 'green') #Because there are certain things that take a while.
        self.workingText = visual.TextStim(self.win, text="Working...", height= .3, bold=True, alignHoriz='center', pos=[0,0])
        
        #Begin
        self.mainLoop()
       
    
    def mainLoop(self):
        '''
        Main loop of the whole program.
        :return:
        :rtype:
        '''
        while self.allDone==False:        
            self.showMainUI()
            self.win.flip()
            #Check all the stand-alone buttons
            for i in range(0, len(self.buttonList['shapes'])):
                if self.mouse.isPressedIn(self.buttonList['shapes'][i],buttons=[0]): #left-click only
                    self.showMainUI()
                    self.workingRect.draw()
                    self.workingText.draw()
                    self.win.flip()
                    if os.name is not 'posix':
                        while self.mouse.getPressed()[0] == 1:
                            pass
                        self.win.winHandle.set_visible(visible=False)
                    self.buttonList['functions'][i]() #It should not be this easy, BUT IT IS. Python is great.
                    if os.name is not 'posix':
                        self.win.winHandle.set_visible(visible=True)
            #Check all the trial type elements.
            for j in range(0,len(self.trialTypesArray['shapes'])):
                if self.mouse.isPressedIn(self.trialTypesArray['shapes'][j],buttons=[0]): #Left-click, add to study flow, at end.
                    self.settings['trialOrder'].append(self.trialTypesArray['labels'][j])
                    self.studyFlowArray=self.loadFlow() #Reloads the study flow with the new thing added.
                    while self.mouse.isPressedIn(self.trialTypesArray['shapes'][j],buttons=[0]): #waits until the mouse is released before continuing.
                        pass
                elif self.mouse.isPressedIn(self.trialTypesArray['shapes'][j],buttons=[1,2]): #Right-click, modify trial type info.
                    self.showMainUI()
                    self.workingRect.draw()
                    self.workingText.draw()
                    self.win.flip()
                    if os.name is not 'posix': #There's an issue with windows and dialog boxes, don't ask.
                        while 1 in self.mouse.getPressed():
                            pass
                        self.win.winHandle.set_visible(visible=False)
                    self.trialTypeDlg(trialType = self.trialTypesArray['labels'][j],makeNew = False)
                    if os.name is not 'posix':
                        self.win.winHandle.set_visible(visible=True)
            for k in range(0, len(self.studyFlowArray['shapes'])):
                if self.mouse.isPressedIn(self.studyFlowArray['shapes'][k]):
                    self.moveTrialInFlow(k)
                    break
        self.win.close()
        
            
    def showMainUI(self):
        '''
        Main draw loop of the primary builder interface
        :return:
        :rtype:
        '''
        self.flowRect.draw()        #Draw flow area and study flow
        for i in range(0, len(self.studyFlowArray['lines'])):
            self.studyFlowArray['lines'][i].draw()
        for j in range(0,len(self.studyFlowArray['labels'])):
            self.studyFlowArray['shapes'][j].draw()
            self.studyFlowArray['text'][j].draw()
        #Buttons for trial types, etc.
        self.paletteRect.draw() #Palette of trial types.
        for i in range(0, len(self.trialTypesArray['labels'])):
            self.trialTypesArray['shapes'][i].draw()
            self.trialTypesArray['text'][i].draw()
        #General buttons
        for i in range(0, len(self.buttonList['shapes'])):
            self.buttonList['shapes'][i].draw()
            self.buttonList['text'][i].draw()
    
    def trialTypeDlg(self,trialType="TrialTypeNew", makeNew=True,prevInfo=[]):
        '''
        Dialog for creating OR modifying a trial type. Allows you to set
        the maximum duration of that trial type as well as remove movies
        from it, and also set whether the trial type is gaze contingent.

        :param trialType: Name of the trial type
        :type trialType: str
        :param makeNew: Making a new trial type or modifying an existing one?
        :type makeNew: bool
        :param prevInfo: If user attempts to create an invalid trial type, the dialog is re-opened with the previously entered information stored and restored
        :type prevInfo: list
        :return:
        :rtype:
        '''
        self.showMainUI()
        self.workingRect.draw()
        self.workingText.draw()
        self.win.flip()
        #For when a trial is right-clicked, or a new one created, open a dialog with info about it.
        skip = False
        if len(self.trialTypesArray['labels']) == 8:
            errDlg = gui.Dlg(title="Max trial types reached!")
            errDlg.addText("PyHab's builder currently supports a maximum of 8 trial types.")
            errDlg.show()
        else:
            typeDlg = gui.Dlg(title="Trial Type " + trialType)
            typeDlg.addField("Trial type name: ", trialType)
            if not makeNew: #if this modifying an existing trial type, pre-fill the existing info.
                if len(prevInfo) == 0: #Changing how movienames.
                    typeDlg.addField("Max duration", self.settings['maxDur'][trialType])
                    if len(self.settings['movieNames'][trialType]) > 0:
                        typeDlg.addText("Current movie files in trial type (uncheck to remove)")
                        for i in range(0,len(self.settings['movieNames'][trialType])):
                            typeDlg.addField(self.settings['movieNames'][trialType][i], initial=True)
                else:
                    typeDlg.addField("Max duration", prevInfo[1])
                    if len(prevInfo) > 3: #If there were no movies to start with, this will have a length of 3.
                        typeDlg.addText("Current movie files in trial type (uncheck to remove)")
                        for i in range(0,len(self.settings['movieNames'][trialType])):
                            typeDlg.addField(self.settings['movieNames'][trialType][i], initial=prevInfo[i+2])
                #find the index of the existing trial type in the study flow and type pane.
                flowIndexes=[]
                for i in range(0,len(self.studyFlowArray['labels'])):
                    if self.studyFlowArray['labels'][i] == trialType:
                        flowIndexes.append(i) 
                typeIndex =self.trialTypesArray['labels'].index(trialType)
            elif len(prevInfo) > 0:
                typeDlg.addField("Max duration", prevInfo[1])
            else: #if there is no existing indeces to refer to
                typeDlg.addField("Max duration",60)
            if trialType in self.settings['playThrough']:
                chz = ["No","Yes"]
            else:
                chz=["Yes","No"]
            typeDlg.addField("Gaze-contingent trial type", choices = chz)
            typeInfo = typeDlg.show()
            if typeDlg.OK:
                #Update all the things, or create them.
                typeInfo[0] = str(typeInfo[0])#Ditch PyQT BS I hope.
                if typeInfo[0] is not trialType: #First, do we need to change the trial type label for an existing type?
                    if not makeNew and typeInfo[0] not in self.trialTypesArray['labels']:
                        #change all the dicts and everything.
                        self.settings['movieNames'][typeInfo[0]] = self.settings['movieNames'].pop(trialType)
                        self.settings['maxDur'][typeInfo[0]]=self.settings['maxDur'].pop(trialType)
                        if trialType in self.settings['playThrough']:
                            for i in range(0,len(self.settings['playThrough'])):
                                if self.settings['playThrough'][i]==trialType:
                                    self.settings['playThrough'][i] = typeInfo[0] #replace.
                        #update trial type and study flow too
                        numChar = len(typeInfo[0])
                        if numChar <= 3:
                            numChar = 4 #Maximum height
                        for i in flowIndexes:
                            self.studyFlowArray['labels'][i] = typeInfo[0]
                            self.studyFlowArray['text'][i].text=typeInfo[0]
                            self.studyFlowArray['text'][i].height=self.flowHeightObj/(.42*numChar) #Update text height for new length
                        self.trialTypesArray['labels'][typeIndex]=typeInfo[0]
                        self.trialTypesArray['text'][typeIndex].text = typeInfo[0]
                        self.trialTypesArray['text'][typeIndex].height=self.typeHeightObj/(.33*numChar)
                        self.settings['trialTypes'] = [typeInfo[0] if x == trialType else x for x in self.settings['trialTypes']]
                        self.settings['trialOrder'] = [typeInfo[0] if x == trialType else x for x in self.settings['trialOrder']]
                    elif typeInfo[0] in self.trialTypesArray['labels']:
                        #warning dialog, start over with all info entered so far.
                        warnDlg = gui.dlg(title="Warning!")
                        warnDlg.addText("New trial type label matches an existing trial type! Please choose a different name for this trial type.")
                        warnDlg.show()
                        skip = True
                        self.trialTypeDlg(typeInfo[0], makeNew,typeInfo)
                    trialType = typeInfo[0]
                if not skip:
                    self.settings['maxDur'][trialType] = typeInfo[1] #Update maxDur
                    if typeInfo[len(typeInfo)-1] == "Yes" and trialType in self.settings['playThrough']: #gaze-contingent trial type, not already tagged as such.
                        self.settings['playThrough'].remove(trialType)
                    elif typeInfo[len(typeInfo)-1] == "No" and not trialType in self.settings['playThrough']: #not gaze-contingent, add to playThrough
                        self.settings['playThrough'].append(trialType)
                    if len(typeInfo) > 3: #Again, if there were movies to list.
                        tempMovies = [] #This will just replace the movienames list
                        for i in range(0,len(self.settings['movieNames'][trialType])):
                            if typeInfo[i+2]:
                                tempMovies.append(self.settings['movieNames'][trialType][i])
                        self.settings['movieNames'][trialType] = tempMovies
                    #if we need to update the flow pane, it's taken care of above. Here we update the type pallette.
                    if makeNew:
                        i = len(self.trialTypesArray['labels']) #Grab length before adding, conveniently the index we need for position info etc.
                        self.trialTypesArray['labels'].append(typeInfo[0])
                        tempObj = visual.Rect(self.win,width=self.typeWidthObj, height=self.typeHeightObj, fillColor=self.colorsArray[i], pos=self.typeLocs[i])
                        numChar = len(typeInfo[0])
                        if numChar <= 3:
                            numChar = 4 #Maximum height
                        tempTxt = visual.TextStim(self.win, alignHoriz='center', alignVert='center', bold=True, height=self.typeHeightObj/(.38*numChar), text=typeInfo[0], pos=self.typeLocs[i])
                        self.trialTypesArray['shapes'].append(tempObj)
                        self.trialTypesArray['text'].append(tempTxt)
                        self.settings['trialTypes'].append(typeInfo[0])
                        self.settings['movieNames'][typeInfo[0]] = []
    
    def addHabBlock(self):
        self.trialTypeDlg(trialType="Hab")
    
    def delTrialTypeDlg(self):
        '''
        Dialog for deleting a trial type, and all instances of that trial type in the study flow
        :return:
        :rtype:
        '''
        self.showMainUI()
        self.workingRect.draw()
        self.workingText.draw()
        self.win.flip()
        delTypeDlg = gui.Dlg(title="Choose trial type to delete.")
        delTypeDlg.addText("Warning: Cannot be undone. All instances of this trial type in study flow will also be removed!")
        delTypeDlg.addField("Choose trial type to delete, then hit OK.", choices=self.trialTypesArray['labels'])
        delInfo=delTypeDlg.show()
        if delTypeDlg.OK:
            dType=delInfo[0]
            self.settings['trialTypes'].remove(dType) #remove the type from the list of trial types.
            del self.settings['movieNames'][dType] #remove from movienames
            del self.settings['maxDur'][dType]# remove from maxdur
            if dType in self.settings['playThrough']: #if it was in playThrough, remove it from there too.
                self.settings['playThrough'].remove(dType)
            self.trialTypesArray=self.loadTypes() #easiest to just reload the trial types.
            #For the study flow, it's easiest just to remove it from the trial order and reload the study flow.
            if dType in self.settings['trialOrder']:
                while dType in self.settings['trialOrder']:
                    self.settings['trialOrder'].remove(dType)
                self.studyFlowArray=self.loadFlow()

    def moveTrialInFlow(self,flowIndex):
        '''
        A function for when a trial is clicked in the study flow, allowing you to either swap it or remove it.

        :param flowIndex: The index in the flowArray of the trial being modified
        :type flowIndex: int
        :return:
        :rtype:
        '''
        #Display a text tooltip at the bottom of the flow area.
        instrText = visual.TextStim(self.win, text="Click another trial to swap positions, or click the remove button to delete from the study flow, click anywhere else to cancel.", bold=True,
                    height = abs(self.flowArea[3]-self.flowArea[2])*.05, pos=[-.5, self.flowArea[3]+.12*float(abs(self.flowArea[3]-self.flowArea[2]))],alignHoriz='center',alignVert='center')
        #highlight the selected object.
        removeTrialShape = visual.Rect(self.win, fillColor='red', width=.1*float(abs(self.flowArea[1]-self.flowArea[0])), height=.1*float(abs(self.flowArea[3]-self.flowArea[2])), 
                    pos=[self.flowArea[0]+float(abs(self.flowArea[1]-self.flowArea[0]))*.85,self.flowArea[3]+float(abs(self.flowArea[3]-self.flowArea[2]))/9])
        removeTrialText = visual.TextStim(self.win, text = "REMOVE", bold=True, height=removeTrialShape.height*.7,pos=removeTrialShape.pos)
        self.studyFlowArray['shapes'][flowIndex].lineColor="yellow"
        self.studyFlowArray['shapes'][flowIndex].lineWidth=5
        core.wait(.1) #Short delay to clear any old mouse press.
        #loop until mouse press
        while 1 not in self.mouse.getPressed():
            self.showMainUI()
            instrText.draw()
            removeTrialShape.draw()
            removeTrialText.draw()
            self.win.flip()
        for i in range(0, len(self.studyFlowArray['shapes'])):
            if self.mouse.isPressedIn(self.studyFlowArray['shapes'][i]) and not i == flowIndex: #clicked a different thing in the study flow
                #Swap the selected trial and the clicked trial, reload study flow.
                tempTrial=self.settings['trialOrder'][i]
                self.settings['trialOrder'][i] = self.settings['trialOrder'][flowIndex]
                self.settings['trialOrder'][flowIndex] = tempTrial
                self.studyFlowArray = self.loadFlow()
        if self.mouse.isPressedIn(removeTrialShape):
            #pop that trial out of trial order, reload flow.
            del self.settings['trialOrder'][flowIndex]
            self.studyFlowArray=self.loadFlow()
        else:
            self.studyFlowArray['shapes'][flowIndex].lineColor="white"
            self.studyFlowArray['shapes'][flowIndex].lineWidth=1.5
        core.wait(.1)

    
    def loadFlow(self):
        '''
        This creates the array of objects in the study flow display

        :return:
        :rtype:
        '''
        tOrd = self.settings['trialOrder']
        numItems = len(tOrd)
        tTypes = self.settings['trialTypes']
        for i in range(0,len(tOrd)):
            if tOrd[i] == 'Hab':
                numItems += 1 #Double-size for habs
        outputDict = {'lines':[],'shapes':[],'text':[],'labels':[]}  #Labels allows us to index the others while still keeping order.
        j = 0 #This serves a purpose, trust me.
        for i in range(0, len(tOrd)):
            #Now, actually build the list of objects to render.
            c=tTypes.index(tOrd[i])#find the trial type, get color index
            if tOrd[i] == 'Hab': #The special category
                if  j == 10:
                    j += 1 #Just in case we're at the point where it would loop around to the second row. We don't want that.
                lx1 = self.flowLocs[j][0]
                j += 1
                lx2 = self.flowLocs[j][0]
                lx = (lx2+lx1)/2 #Ideally putting it square in between the two places.
                loc = [lx,self.flowLocs[j][1]]
                tempObj = visual.Rect(self.win,width=self.flowWidthObj*2, height=self.flowHeightObj, fillColor=self.colorsArray[c], pos=loc)
            else:
                tempObj = visual.Rect(self.win,width=self.flowWidthObj, height=self.flowHeightObj, fillColor=self.colorsArray[c], pos=self.flowLocs[j])
            numChar = len(tOrd[i])
            if numChar <= 3:
                numChar = 4 #Maximum height
            tempTxt = visual.TextStim(self.win, alignHoriz='center', bold=True, alignVert='center',height=self.flowHeightObj/(.42*numChar), text=tOrd[i], pos=tempObj.pos)
            j += 1
            outputDict['shapes'].append(tempObj) 
            outputDict['text'].append(tempTxt)
            outputDict['labels'].append(tOrd[i])
        if numItems == 0:
            pass #So we do not add a line if there is no line to draw!
        elif numItems < 11:
            tempLine = visual.Line(self.win, start=self.flowLocs[0], end=self.flowLocs[numItems-1])
            outputDict['lines'].append(tempLine)
        elif numItems < 21:
            tempLine = visual.Line(self.win, start=self.flowLocs[0], end=self.flowLocs[9])
            tempLine2 = visual.Line(self.win, start=self.flowLocs[10], end=self.flowLocs[len(tOrd)-1])
            outputDict['lines'].append(tempLine)
            outputDict['lines'].append(tempLine2)
        return outputDict
    
    def loadTypes(self): #A "pallette" of trial types on one side, only needed when loading from save.
        '''
        This function creates the trial types palette
        :return:
        :rtype:
        '''
        if len(self.settings['trialTypes']) == 0:#if working w/ an old settings file or one that for w/e reason has no ttypes.
            tOrd = self.settings['trialOrder']
            tTypes = []#list of trial types
            for i in range(0,len(tOrd)):
                if tOrd[i] not in tTypes:
                    tTypes.append(tOrd[i]) #creating a  list of unique trial types
        else:
            tTypes = self.settings['trialTypes'] 
        outputDict=  {'shapes':[],'text':[],'labels':[]} #Dicts ain't ordered but lists within dicts sure are!
        #Create the same trial type squares we see in the flow, but wholly independent objects for drawing purposes (allowing one to change w/out the other)
        for i in range(0, len(tTypes)):
            #Now, actually build the list of objects to render.
            tempObj = visual.Rect(self.win,width=self.typeWidthObj, height=self.typeHeightObj, fillColor=self.colorsArray[i], pos=self.typeLocs[i])
            numChar = len(tTypes[i])
            if numChar <= 3:
                numChar = 4 #Maximum height
            tempTxt = visual.TextStim(self.win, alignHoriz='center', alignVert='center',bold=True,height=self.typeHeightObj/(.32*numChar),text=tTypes[i], pos=self.typeLocs[i])
            outputDict['shapes'].append(tempObj) #Might need to change this to be a dict of shapes and text, to make click-in-shape easier to manage later.
            outputDict['text'].append(tempTxt)
            outputDict['labels'].append(tTypes[i])
        return(outputDict)
    
    def quitFunc(self):
        '''
        Simple function for quitting, checks if you want to save first (if there's anything to save).
        :return:
        :rtype:
        '''
        self.allDone=True
        if len(self.trialTypesArray['labels']) > 0: #Don't save if no trial types have been created
            saveDlg = gui.Dlg(title="Save?",labelButtonOK='Yes', labelButtonCancel='No')
            saveDlg.addText("Save before quitting?")
            s = saveDlg.show()
            if saveDlg.OK:
                if len(self.folderPath) == 0:
                    self.saveDlg()
                else:
                    self.saveEverything()
    
    def univSettingsDlg(self): #The universal settings button.
        '''
        Settings that apply to every PyHab study regardless of anything else.

        prefix: The prefix of the launcher and all data files.
        maxOff: Max consecutive seconds looking away needed to end gaze-contingent trials
        minOn: Minimum gaze-on time before maxOff is used to determine end of trial.
        ISI: Minimum time between loops of stimuli.
        autoAdvance: Whether the attention-getter needs to be manually triggered or
            is triggered automatically after each trial
        blindPres: Level of experimenter blinding, 0 (none), 1 (no trial type info), or
            2 (only info is whether a trial is currently active.
        prefLook: Whether the study is preferential-looking or single-target.
        :return:
        :rtype:
        '''
        self.showMainUI()
        self.workingRect.draw()
        self.workingText.draw()
        self.win.flip()
        uDlg = gui.Dlg(title="Universal settings")
        #maxOff, minOn, [default] blindpres, autoadvance, ISI, 
        uDlg.addField("Experiment name",self.settings['prefix'])
        uDlg.addField("Number of continuous seconds looking away to end trial", self.settings['maxOff'])
        uDlg.addField("Minimum time looking at screen before stimuli can be ended (not consecutive)",self.settings['minOn'])
        uDlg.addField("Minimum ISI between loops, in seconds", self.settings['ISI'])
        if self.settings['autoAdvance'] in [0,'0','False',False]:
            setBox = False
        else:
            setBox = True
        uDlg.addField("Auto-advance from one trial to the next? (If checked, attention getter will play automatically after end of trial when ITI has passed)",initial=setBox)
        ch = []
        if self.settings['blindPres'] == '1' or self.settings['blindPres'] == 1:
            ch=[1,0,2]
        elif self.settings['blindPres'] == '2' or self.settings['blindPres'] == 2:
            ch=[2,0,1]
        else:
            ch=[0,1,2]
        uDlg.addField("Experimenter blinding: 0 = no blinding, 1 = Trial number and gaze on/off only, 2 = Trial active/not active only", choices=ch)
        ch2 = []
        if self.settings['prefLook'] in ['1',1]:# so it does not reset everytime you load this dialog.
            ch2 = ["Preferential looking","Single-target"]
        else:
            ch2=["Single-target", "Preferential looking"]
        uDlg.addField("Single-target or preferential looking?",choices=ch2)
        uInfo = uDlg.show()
        if uDlg.OK:
            self.settings['prefix'] = uInfo[0]
            self.settings['maxOff'] = uInfo[1]
            self.settings['minOn'] = uInfo[2]
            self.settings['ISI'] = uInfo[3]
            self.settings['autoAdvance'] = uInfo[4]
            self.settings['blindPres'] = uInfo[5]
            if uInfo[6] == "Preferential looking" and self.settings['prefLook'] in [0,'0','False',False]: #specifically switching, reactivate all data cols.
                self.settings['prefLook'] = 1
                self.settings['dataColumns'] = self.allDataColumnsPL
            elif uInfo[6] == "Single-target" and self.settings['prefLook'] in [1,'1','True',True]:
                self.settings['prefLook'] = 0
                self.settings['dataColumns'] = self.allDataColumns
        
    def dataSettingsDlg(self):
        '''
        Which columns of data are recorded.
        Resets if the experiment type is switched to or from preferential looking.

        :return:
        :rtype:
        '''
        self.showMainUI()
        self.workingRect.draw()
        self.workingText.draw()
        self.win.flip()
        dDlg = gui.Dlg(title="Data settings")
        dDlg.addText("Check all columns you would like to be recorded in your data files. ")
        dDlg.addText("ANYTHING UNCHECKED WILL NOT BE STORED IN ANY WAY!")
        if self.settings['prefLook'] in [1,'1',True,'True']:
            tempDataCols = self.allDataColumnsPL
        else:
            tempDataCols = self.allDataColumns
        for i in range(0, len(tempDataCols)):
            if tempDataCols[i] in self.settings['dataColumns']:
                dDlg.addField(tempDataCols[i],initial=True)
            else:
                dDlg.addField(tempDataCols[i],initial=False)
        datInfo = dDlg.show()
        if dDlg.OK:
            tempCols = []
            for j in range(1, len(datInfo)):
                if datInfo[j]:
                    tempCols.append(self.allDataColumns[j]) 
            self.settings['dataColumns'] = tempCols
        
    def stimSettingsDlg(self):
        '''
        Settings relating to stimulus presentation

        screenWidth: Width of stim window
        screenHeight: Height of stim window
        movieWidth: Width of movieStim3 object inside stim window. Future: Allows for movie default resolution?
        movieWidth: Height of movieStim3 object inside stim window
        screenIndex: Which screen to display the stim window on.
        playAttnGetter: Whether to use PyHab's built-in attention-getter or not.
            Also affects study flow, in that the movie now starts playing on "A" press.
        freezeFrame: If playAttnGetter == True, this is the minimum time the first frame
            of the movie will be displayed after the attention-getter finishes.
        :return:
        :rtype:
        '''
        self.showMainUI()
        self.workingRect.draw()
        self.workingText.draw()
        self.win.flip()
        sDlg = gui.Dlg(title="Movie stimuli settings")
        sDlg.addField("Stimulus display width in pixels", self.settings['screenWidth'])
        sDlg.addField("Stimulus display height in pixels", self.settings['screenHeight'])
        sDlg.addField("Width of movie stimuli in pixels", self.settings['movieWidth'])
        sDlg.addField("Height of movie stimuli in pixels", self.settings['movieHeight'])
        sDlg.addField("Screen index of presentation screen (0 = primary display, 1 = secondary screen)", self.settings['screenIndex'])
        if self.settings['playAttnGetter'] in [1,'1','True',True]:
            attCh = ['Yes','No']
        else:
            attCh=['No','Yes']
        sDlg.addField("Use built-in attention-getter? ", choices=attCh)
        sDlg.addField("Freeze first frame for how many seconds after attention-getter?", self.settings['freezeFrame'])
        stimfo = sDlg.show()
        if sDlg.OK:
            self.settings['screenWidth'] = stimfo[0]
            self.settings['screenHeight'] = stimfo[1]
            self.settings['movieWidth'] = stimfo[2]
            self.settings['movieHeight'] = stimfo[3]
            self.settings['screenIndex'] = stimfo[4]
            if stimfo[5] == 'Yes':
                self.settings['playAttnGetter']=1
            else:
                self.settings['playAttnGetter'] = 0
            self.settings['freezeFrame'] = stimfo[6]
        
    def addMoviesToTypesDlg(self):
        '''
        A series dialog boxes, the first selecting a trial type and the number of movies to add,
        then one file open dialog for each movie, which is in turn added to the movieNames list
        for that trial type.
        :return:
        :rtype:
        '''
        self.showMainUI()
        self.workingRect.draw()
        self.workingText.draw()
        self.win.flip()
        #Two-stage, select type then movies? Or "add movie to trial type". Annoying repetition....but for now maybe best?
        if len(self.trialTypesArray['labels']) > 0:
            d1 = gui.Dlg(title="Select trial type to add movies to")
            d1.addField("Trial type to add stimulus file to", choices=self.trialTypesArray['labels'])
            d1.addField("Number of movies to add (you will add them one at a time)",1)
            d = d1.show()
            if d1.OK:
                self.showMainUI()
                self.workingRect.draw()
                self.workingText.draw()
                self.win.flip()
                tType = d[0]
                numAdd = d[1]
                NoneType = type(None)
                for i in range(0, numAdd):
                    stimDlg = gui.fileOpenDlg(prompt="Select stimulus file (only one)")
                    if type(stimDlg) is not NoneType:
                        fileIndex = stimDlg[0].rfind(self.dirMarker) + 1 #Finds last instance of / or \
                        movName = stimDlg[0][fileIndex:] #*SHOULD* return the movie name in isolation.
                        self.stimSource[movName] = stimDlg[0] #Creates a "Find this movie" path for the save function.
                        self.settings['movieNames'][tType].append(movName)
        else:
            errDlg = gui.Dlg(title="No trial types!")
            errDlg.addText("No trial types to add movies to! Please create trial types first.")
            e = errDlg.show()
        
    def condSettingsDlg(self): #Settings relating to conditions and randomization
        '''
        The dialog window for "condition settings", not to be confused with the
        condition interface created by self.condMaker(). This determines whether
        condition randomization is used at all, a separate interface is used to
        define the conditions themselves.
        :return:
        :rtype:
        '''
        cDlg = gui.Dlg(title="Conditions settings")
        #Welcome to waterloo. The simple version is just "make a list of conditions and set them after saving". 
        #The ideal is that it reads off movienames (or # movies) and all and lets you specify for each order...
        chkBox = False
        if self.settings['randPres'] in [1,'1',True,'True']:
            chkBox = True
        cDlg.addField("Use random presentation? If yes, a new interface will open",initial=chkBox)
        cDlg.addField("Pre-existing condition file (optional, leave blank to make new file called conditions.csv)", self.settings['condFile'])
        #cDlg.addField("List of condition labels (each one in quotes, separated by commas, all inside square brackets)", self.settings['condList'])
        condInfo = cDlg.show()
        if cDlg.OK:
            self.settings['randPres'] = condInfo[0]
            if condInfo[0]:
                #A new dialog that allows you to re-order things...somehow
                if len(condInfo[1]) > 0:
                    self.settings['condFile'] = condInfo[1]
                else:
                    self.settings['condFile'] = "conditions.csv"
                #Check if there are movies to re-order.
                allReady = True
                if len(self.trialTypesArray['labels']) == 0:
                    allReady = False
                for i in range(0,len(self.trialTypesArray['labels'])):
                    if self.trialTypesArray['labels'][i] not in self.settings['movieNames'].keys():
                        allReady = False
                    elif len(self.settings['movieNames'][self.trialTypesArray['labels'][i]]) == 0:
                        allReady = False
                if allReady:
                    if os.name is not 'posix':
                        self.win.winHandle.set_visible(visible=True)
                    self.condMaker()
                else:
                    #Create err dlg.
                    errDlg = gui.Dlg(title="No stimuli!")
                    errDlg.addText("Not all trial types have stimuli!")
                    errDlg.addText("Please add stimuli to all trial types first and then set conditions for randomized presentation.")
                    errDlg.addField("For studies without stimuli, enter list of condition labels here, each one in quotes, separated by commas, all inside the square brackets",self.settings['condList'])
                    e = errDlg.show()
                    if errDlg.OK:
                        self.settings['condList'] = e[0]
            else:
                self.settings['condFile'] = '' #Erases one if it existed.

    def condMaker(self, rep=False): #For dealing with conditions.
        '''
        A whole separate interface for managing condition creation.
        :param rep: Basically whether we are recursing while editing conditions
        :type rep: bool
        :return:
        :rtype:
        '''
        condHeader = visual.TextStim(self.win, text="Conditions",height=.1, bold=True,pos=[-.83,.9])
        divLinesV = [] #Vertical dividing lines (actually very thin rects)
        divLinesH = [] #Horizontal dividing lines
        tTypeHeaders=[] #Heads of each column for trial types.
        condLabels = [] #Labels
        condContent=[] #The content of each condition (a list of dicts). This is nogood.
        drawConds=[] #The text things for drawing.
        if os.path.exists(self.settings['condFile']) and not rep: #If we already have a pre-existing cond file and aren't in the process of looping.
            testReader=csv.reader(open(self.settings['condFile'],'rU'))
            testStuff=[]
            for row in testReader:
                testStuff.append(row)
            for i in range(0, len(testStuff)):
                condLabels.append(testStuff[i][0])
                condContent.append(eval(testStuff[i][1]))
            testDict = dict(testStuff) 
            for i in testDict.keys():
                testDict[i]=eval(testDict[i])
            self.condDict=testDict 
            self.settings['condList'] = condLabels
            
        elif len(self.condDict) > 0: #If we already have something to build on
            for i in range(0, len(self.settings['condList'])):
                if self.settings['condList'][i] in self.condDict.keys():
                    condContent.append(self.condDict[self.settings['condList'][i]])
                else:
                    condContent.append({ })
        doneButton = visual.Rect(self.win, width=.25, height=.67*(.15/self.aspect),fillColor="green",pos=[.82,-.85])
        doneText = visual.TextStim(self.win, text="DONE", bold=True, pos=doneButton.pos)
        addCondButton = visual.Rect(self.win, width=.3, height=.67*(.15/self.aspect),fillColor="blue",pos=[-.82,-.85])
        addCondText = visual.TextStim(self.win, text="Add condition", bold=True, height=addCondButton.height*.3, pos=addCondButton.pos)
        deleteCondButton = visual.Rect(self.win, width=.3, height=.67*(.15/self.aspect),fillColor="red",pos=[-.5,-.85])
        deleteCondText = visual.TextStim(self.win, text="Delete condition", bold=True, height=deleteCondButton.height*.3, pos=deleteCondButton.pos)
        instrText = visual.TextStim(self.win, text="Click a condition row to modify it", pos=[0,-.9])
        intervalHoriz = 1.5/(len(self.trialTypesArray['labels'])+1)
        intervalVert = 1.5/(len(self.settings['condList'])+1)
        startH = -.5
        startV = .8
        tempLineH = visual.Line(self.win, start=[-.99,.82], end=[.99,.82])
        divLinesH.append(tempLineH)
        tempLineV = visual.Rect(self.win, width=.01, height=2, fillColor="white", pos=[-.65,.3])
        divLinesV.append(tempLineV)
        clickRanges=[] #For making it easier ot detect if a line was clicked in. Y only (horizontal doesn't matter)
        for i in range(0,len(self.trialTypesArray['labels'])):
            #populate column headers and lines.
            hpos = (i)*intervalHoriz + startH+intervalHoriz/3
            movText = visual.TextStim(self.win, alignHoriz='center', text=self.settings['movieNames'][self.trialTypesArray['labels'][i]],height=(1-startV)*.2,pos=[hpos,.87])
            tempText = visual.TextStim(self.win, alignHoriz='center', text=self.trialTypesArray['labels'][i],height=(1-startV)*.3, pos=[hpos, .94])
            tTypeHeaders.append(movText)
            tTypeHeaders.append(tempText)
            tempLineV = visual.Line(self.win, start=[hpos+intervalHoriz/2,.99], end=[hpos+intervalHoriz/2,-.7])
            divLinesV.append(tempLineV)
        for j in range(0, len(self.settings['condList'])): #condition labels. Here's where rubber meets road!
            vpos = startV - (j+1) * intervalVert + intervalVert/1.5
            tempText = visual.TextStim(self.win, text=self.settings['condList'][j], alignHoriz='center',height=intervalVert*.35, pos=[condHeader.pos[0],vpos])
            drawConds.append(tempText)
            tempLineH = visual.Line(self.win, start=[-.99,vpos-intervalVert/2], end=[.99,vpos-intervalVert/2])
            divLinesH.append(tempLineH)
            #And now, finally, we have to populate each of those damn things.
            for q in range(0,len(self.trialTypesArray['labels'])):
                if self.trialTypesArray['labels'][q] in condContent[j].keys():
                    tempTxt = condContent[j][self.trialTypesArray['labels'][q]]
                else:
                    tempTxt = []
                tempText = visual.TextStim(self.win, text=tempTxt, height=intervalVert*.35,pos=[tTypeHeaders[q*2].pos[0],vpos], alignHoriz='center')
                drawConds.append(tempText)
            tempRange = [vpos+intervalVert/2,vpos-intervalVert/2]
            clickRanges.append(tempRange)
        #Finally the main loop  of this new display.
        done = False
        while 1 in self.mouse.getPressed():
            pass
        while not done:
            condHeader.draw()
            doneButton.draw()
            doneText.draw()
            addCondButton.draw()
            addCondText.draw()
            deleteCondButton.draw()
            deleteCondText.draw()
            for i in range(0, len(divLinesV)):
                divLinesV[i].draw()
            for j in range(0, len(divLinesH)):
                divLinesH[j].draw()
            for k in range(0, len(tTypeHeaders)):
                tTypeHeaders[k].draw()
            for l in range(0, len(drawConds)):
                drawConds[l].draw()
            self.win.flip()
            if 1 in self.mouse.getPressed():
                for i in range(0, len(clickRanges)):
                    p=self.mouse.getPos()
                    if p[1] <= clickRanges[i][0] and p[1] >= clickRanges[i][1]:
                        if os.name is not 'posix':
                            while 1 in self.mouse.getPressed():
                                pass
                            self.win.winHandle.set_visible(visible = False)
                        self.condSetter(cond=self.settings['condList'][i],ex=True)
                        if os.name is not 'posix':
                            self.win.winHandle.set_visible(visible=True)
                        while 1 in self.mouse.getPressed():
                            pass
                        done = True
                        #Start this over...
                        self.condMaker(rep=True)
                if self.mouse.isPressedIn(addCondButton):
                    if os.name is not 'posix':
                        while 1 in self.mouse.getPressed():
                            pass
                        self.win.winHandle.set_visible(visible = False)
                    self.condSetter(ex=False)
                    if os.name is not 'posix':
                        self.win.winHandle.set_visible(visible = True)
                    while 1 in self.mouse.getPressed():
                        pass
                    done = True
                    #Start this over...
                    self.condMaker(rep=True)
                if self.mouse.isPressedIn(deleteCondButton) and len(self.settings['condList'])>0:
                    if os.name is not 'posix':
                        while 1 in self.mouse.getPressed():
                            pass
                        self.win.winHandle.set_visible(visible = False)
                    self.delCond()
                    if os.name is not 'posix':
                        self.win.winHandle.set_visible(visible = True)
                    while len(self.mouse.getPressed()) < 0:
                        pass
                    done = True
                    #Start this over...
                    self.condMaker(rep=True)
                if self.mouse.isPressedIn(doneButton):
                    done = True
                    while 1 in self.mouse.getPressed():
                        pass #Just to make it not auto-click something on return to the main window
                
    
    def condSetter(self, cond='NEW', ex=False): #Modifying or making new condition information.
        '''
        One dialog per trial type. Each dialog has a list of all the movies in that type
        This is not intuitive under the hood. The output of this is a dict with an array like this for each trial type: [1, 2, 3]
        Those numbers refer to the index of the movie in that trial's movieNames array.
        But, in this dialog, users are inputting the point in the order in which they would like each one to appear.
        So if the third movie in the names gets the number 1 in this dialog, the output array starts [3, ]
        Also yes the ouput is using the index plus one. This is because originally you had to hand-code this condition file, and it makes it
        more intelligible to non-programmer users.
        :param cond: Condition name
        :type cond: str
        :param ex: Whether the condition already exists
        :type ex: bool
        :return:
        :rtype:
        '''
        condDlg2=gui.Dlg(title="Define condition")
        condDlg2.addField("Condition label:", cond)
        condDlg2.addText("You will have separate dialogs to set the order of movies in each trial type. Press OK to begin")
        condDinfo = condDlg2.show()
        if condDlg2.OK:
            condDinfo[0] = str(condDinfo[0])
            if ex and condDinfo[0] != cond: #Renamed existing condition
                self.settings['condList'][self.settings['condList'].index(cond)] = condDinfo[0] 
                if cond in self.condDict.keys():
                    self.condDict[condDinfo[0]] = self.condDict.pop(cond)
            cond = condDinfo[0]
            outputDict = {}
            i = 0
            while i < len(self.trialTypesArray['labels']):
                tempType =  self.trialTypesArray['labels'][i]
                condTyDlg = gui.Dlg(title="Trial type " + tempType)
                condTyDlg.addText("Enter order in which you want movies to appear. If you do not want a movie to appear in this condition, leave blank or put 0.")
                if ex: #If there is an existing trial that we are modifying.
                    try:
                        movieOrder = self.condDict[cond][tempType]
                    except:
                        movieOrder = []
                        for k in range(0, len(self.settings['movieNames'][tempType])):
                            movieOrder.append(k+1) #default order.
                else:
                    movieOrder = []
                    for k in range(0, len(self.settings['movieNames'][tempType])):
                        movieOrder.append(k+1) #default order.
                for x in range(0, len(self.settings['movieNames'][tempType])): #Yeah we gotta loop it again.
                    thisMov = self.settings['movieNames'][tempType][x]
                    if x+1 in movieOrder: #If that movie appears in the movie order.
                        condTyDlg.addField(thisMov, movieOrder.index(x+1)+1)
                    else:
                        condTyDlg.addField(thisMov)
                condTyInfo = condTyDlg.show()
                if condTyDlg.OK:
                    i += 1
                    #Now we need to reinterpret all that input ot make the output.
                    #First, code all non-numbers or invalid numbers as 0
                    condTyInfo = [0 if type(x) is not int or x <= 0 else x for x in condTyInfo] 
                    #Identify any doubles other than 0s, if so error msg and redo
                    maxNum = max(condTyInfo)
                    stop = False
                    for q in range(1, maxNum+1):
                        if condTyInfo.count(q) > 1:
                            errDlg = gui.Dlg(title="Warning, invalid order!")
                            errDlg.addText("Order has a repeat of the same number. Please re-enter.")
                            i -= 1 #This is why our for is now a while.
                            y=errDlg.show()
                            stop = True
                    if maxNum == 0:
                        errDlg = gui.Dlg(title="Warning, invalid order!")
                        errDlg.addText("No trials selected. Please re-enter")
                        i -= 1
                        y=errDlg.show()
                        stop = True
                    if not stop:
                        #Go through and construct the new trial order.
                        tempOrder = []
                        for q in range(1, maxNum+1):
                            try:
                                tMov = condTyInfo.index(q) #Adds the movie indeces (+1) to the order
                                tempOrder.append(tMov+1)
                            except ValueError:
                                errDlg = gui.Dlg(title="Warning, invalid order!")
                                errDlg.addText("Non-consecutive numbering (e.g. 1,2,5). Please re-enter with consecutive numbering!")
                                i -= 1
                                y=errDlg.show()
                                stop = True
                                break
                        outputDict[tempType] = tempOrder
           #Finally, rewrite everything that needs rewriting.
            self.condDict[cond] = outputDict
            if not ex:
                self.settings['condList'].append(str(cond))
        
    def delCond(self):
        '''
        Present list of existing conditions. Choose one to remove.
        '''
        dCondDlg = gui.Dlg(title="Delete a condition")
        dCondDlg.addField('Choose a condition to delete', choices = self.settings['condList'])
        delCond = dCondDlg.show()
        if dCondDlg.OK:
            self.settings['condList'].remove(str(delCond[0]))
            del self.condDict[delCond[0]]          
            
   
   
    def habSettingsDlg(self): #Habituation criteria
        '''
        Dialog for settings relating to habituation criteria:
        maxHabTrials (maximum possible hab trials if criterion not met)
        setCritWindow (# trials summed over when creating criterion)
        setCritDivisor (denominator of criterion calculation . e.g., sum of first 3 trials
            divided by 2 would have 3 for setCritWindow and 2 for this.)
        metCritWindow (# trials summed over when evaluating whether criterion has been met)
        metCritDivisor (denominator of sum calculated when determining if criterion has been met)
        :return:
        :rtype:
        '''
        hDlg = gui.Dlg(title="Habituation block settings")
        hDlg.addField("Max number of habituation trials (if criterion not met)", self.settings['maxHabTrials'])
        hDlg.addField("Number of trials to sum looking time over when making hab criterion", self.settings['setCritWindow'])
        hDlg.addField("Number to divide sum of looking time by when computing criterion", self.settings['setCritDivisor'])
        hDlg.addField("Number of trials to sum looking time over when determining whether criterion has been met", self.settings['metCritWindow'])
        hDlg.addField("Number to divide sum of looking time by when determining whether criterion has been met", self.settings['metCritDivisor'])
        habDat=hDlg.show()
        if hDlg.OK:
            self.settings['maxHabTrials'] = habDat[0]
            self.settings['setCritWindow'] = habDat[1]
            self.settings['setCritDivisor'] = habDat[2]
            self.settings['metCritWindow'] = habDat[3]
            self.settings['metCritDivisor'] = habDat[4]
    
    def saveDlg(self):
        '''
        Opens a save dialog allowing you to choose where to save your project.
        Essentially sets self.folderPath
        :return:
        :rtype:
        '''
        NoneType = type(None)
        sDlg = gui.fileSaveDlg(prompt="Name a folder to save study into")  #We would put prefix as a default but it makes the system fail.
        if type(sDlg) is not NoneType:
            self.settings['folderPath'] = sDlg+self.dirMarker #Makes a folder of w/e they entered
            self.folderPath=self.settings['folderPath']
            #Add save button if it does not exist.
            if self.saveEverything not in self.buttonList['functions']:
                saveButton = visual.Rect(self.win,width=.15, height=.67*(.15/self.aspect), pos=[-.52,-.9],fillColor="green")
                saveText = visual.TextStim(self.win, text="SAVE",color="black",height=saveButton.height*.5, pos=saveButton.pos)
                self.buttonList['shapes'].append(saveButton)
                self.buttonList['text'].append(saveText)
                self.buttonList['functions'].append(self.saveEverything)
            self.saveEverything()
    
    def saveEverything(self):
        '''
        Saves a PyHab project to a set of folders dictated by self.folderPath
        :return:
        :rtype:
        '''
        if not os.path.exists(self.folderPath):
            os.makedirs(self.folderPath) #creates the initial folder if it did not exist.
        success=True #Assume it's going to work.
        #Structure: Top-level folder contains script, then you have data and stimuli.
        dataPath = self.folderPath+'data'+self.dirMarker
        if not os.path.exists(dataPath):
            os.makedirs(dataPath)
        stimPath = self.folderPath+'stimuli'+self.dirMarker
        if not os.path.exists(stimPath):
            os.makedirs(stimPath)
        codePath = self.folderPath+'PyHab'+self.dirMarker
        if not os.path.exists(codePath):
            os.makedirs(codePath)
        srcDir = 'PyHab'+self.dirMarker
        #Condition file!
        if len(self.condDict)>0:
            tempArray = []
            for j in range(0, len(self.settings['condList'])):
                tempArray.append([self.settings['condList'][j],self.condDict[self.settings['condList'][j]]])
            secretWriter = csv.writer(open(self.folderPath+self.settings['condFile'],'wb'))
            for k in range(0, len(tempArray)):
                secretWriter.writerow(tempArray[k]) #hope that closes too...
        #copy stimuli if there are stimuli. Also pulls upchime1.wav
        if len(self.stimSource)>0:
            upchimePath='PyHab' + self.dirMarker + 'upchime1.wav' #need upchime1.wav or it won't work!
            newchimePath = self.folderPath + 'upchime1.wav'
            if not os.path.exists(newchimePath):
                shutil.copyfile(upchimePath,newchimePath)
            for i, j in self.stimSource.iteritems(): #Find each file, WILL NOT WORK IN PY3
                try:
                    targPath = stimPath + i + self.settings['movieExt']
                    shutil.copyfile(j, targPath)
                except:
                    success = False
                    print('Could not copy file ' + j + '. Make sure it exists!')
        if not success:
            errDlg = gui.Dlg(title="Could not copy stimuli!")
            errDlg.addText("Some stimuli could not be copied successfully. See the output of the coder window for details.")
            errDlg.show()
        #create/overwrite the settings csv.
        settingsPath = self.folderPath+self.settings['prefix']+'Settings.csv'
        settingsOutput = csv.writer(open(settingsPath,'w'), lineterminator='\n')
        for i, j in self.settings.iteritems():#this is how you write key/value pairs
            settingsOutput.writerow([i, j])
        #Copy over the class and such. Since these aren't modiied, make sure they don't exist first.
        classPath = 'PyHabClass.py'
        classTarg = codePath+classPath
        classPLPath = 'PyHabClassPL.py'
        classPLTarg = codePath+classPLPath
        buildPath = 'PyHabBuilder.py'
        buildTarg = codePath+buildPath
        initPath = '__init__.py'
        initTarg = codePath+initPath
        try:
            if not os.path.exists(classTarg):
                shutil.copyfile(srcDir+classPath, classTarg)
            if not os.path.exists(classPLTarg):
                shutil.copyfile(srcDir+classPLPath,classPLTarg)
            if not os.path.exists(buildTarg):
                shutil.copyfile(srcDir+buildPath,buildTarg)
            if not os.path.exists(initTarg):
                shutil.copyfile(srcDir+initPath,initTarg)
        except:
            #error dialog?
            errDlg = gui.Dlg(title="Could not copy PyHab and builder!")
            errDlg.addText("Failed to copy PyHab class scripts and builder script. These can be copied manually from the PyHab folder and will be needed!")
            errDlg.show()
            success=False
            print("Could not copy PyHab and builder!")
        #copy/create the launcher script
        launcherPath = self.folderPath+self.settings['prefix']+'Launcher.py'
        if not os.path.exists(launcherPath):
            try:
                # the location of the pyHabLauncher template file
                launcherSource = srcDir+'PyHab Launcher.py'
                #Open file and find line 5, aka the path to the settings file, replace it appropriately
                with open(launcherSource,'r') as file:
                    launcherFile = file.readlines()
                newLine = 'setName = \"' + self.settings['prefix']+'Settings.csv\"\r\n' #Simplified, so it always runs the settings file in that folder.
                launcherFile[6] = newLine
                launcherFile[7] = "#Created in PsychoPy version " + __version__ + "\r\n"
                #now write the new file!
                with open (launcherPath, 'w') as t:
                    t.writelines(launcherFile)
            except:
                errDlg = gui.Dlg(title="Could not save!")
                errDlg.addText("Launcher script failed to save! Please try again or manually copy the launcher script and change the settings line.")
                errDlg.show()
                success=False
                print('creating launcher script failed!')
        if success:
            saveSuccessDlg = gui.Dlg(title="Experiment saved!")
            saveSuccessDlg.addText("Experiment saved successfully to" + self.folderPath)
            saveSuccessDlg.show()

        
        
