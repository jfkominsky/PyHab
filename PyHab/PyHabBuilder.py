from psychopy import visual, event, core, gui, monitors, tools, sound,__version__
from psychopy.app import coder
import wx, random, csv, shutil, os, sys, threading, itertools
from math import *
from copy import deepcopy
import pyglet


class PyHabBuilder:
    """
    Graphical interface for constructing PyHab experiments. Runs mostly on a Pyglet window and qtGUI dialogs.
    Saves a settings file in .csv form which can then be read by PyHab Launcher, PyHabClass, and PyHabClassPL.

    """
    def __init__(self, loadedSaved=False, settingsDict={}):
        """

        :param loadedSaved: Are we loading from a saved settings file?
        :type loadedSaved: bool
        :param settingsDict: If we are loading from a saved file, this is the content of that file passed by the launcher
        :type settingsDict: dict
        """

        self.loadSave = loadedSaved #For easy reference elsewhere
        self.dirMarker = os.sep
        if os.name is 'posix': #glorious simplicity of unix filesystem
            otherOS = '\\'
        elif os.name is 'nt': #Nonsensical Windows-based contrarianism
            otherOS = '/'
        # loadedSaved is "is this a new experiment or are we operating inside an existing experiment's folder?"
        if not loadedSaved:  # A new blank experiment
            # Load some defaults to start with.
            self.settings = {'dataColumns': ['sNum', 'sID', 'months', 'days', 'sex', 'cond','condLabel', 'trial','GNG','trialType','stimName','habCrit','habTrialNo','sumOnA','numOnA','sumOffA','numOffA','sumOnB','numOnB','sumOffB','numOffB'],
                                                        'prefix': 'PyHabExperiment',
                                                        'dataloc':'data'+self.dirMarker,
                                                        'maxDur': {},
                                                        'playThrough': {},
                                                        'movieEnd': [],
                                                        'maxOff': {},
                                                        'minOn': {},
                                                        'blindPres': '0', 
                                                        'autoAdvance': [],
                                                        'randPres': '0', 
                                                        'condPath': '', 
                                                        'condFile': '', 
                                                        'condList': [],
                                                        'baseCondFile': '',
                                                        'baseCondList': [],  # 0.8 New, for remembering pre-counterbalancing
                                                        'trialTypes': [],
                                                        'trialOrder': [],
                                                        'blockList': {},  # 0.8, create blocks of trials (hab remains special)
                                                        'blockDataList':[],
                                                        'maxHabTrials': '14',
                                                        'setCritWindow': '3', 
                                                        'setCritDivisor': '2.0',
                                                        'setCritType': 'First',
                                                        'habThresh': '5.0',
                                                        'metCritWindow': '3', 
                                                        'metCritDivisor': '1.0',
                                                        'metCritStatic': 'Moving',
                                                        'habTrialList': [],
                                                        'calcHabOver': [],
                                                        'stimPres': 0,  # Will be set on each run anyways.
                                                        'stimPath': 'stimuli'+self.dirMarker,
                                                        'stimNames': {},
                                                        'stimList': {},
                                                        'screenWidth': 1080, 
                                                        'screenHeight': 700,
                                                        'screenColor': 'black',
                                                        'movieWidth': 800, 
                                                        'movieHeight': 600, 
                                                        'screenIndex': '1',
                                                        'expScreenIndex': '0',
                                                        'ISI': {},
                                                        'freezeFrame': '0.0',
                                                        'playAttnGetter': {},
                                                        'attnGetterList': {'PyHabDefault':{'stimType':'Audio',
                                                                                          'stimName':'upchime1.wav',
                                                                                          'stimDur':2,
                                                                                          'stimLoc':'PyHab' + self.dirMarker + 'upchime1.wav',
                                                                                          'shape':'Rectangle',
                                                                                          'color':'yellow'}},
                                                        'folderPath': '',
                                                        'prefLook': '0',
                                                        'startImage': '',
                                                        'endImage': '',
                                                        'nextFlash': '0'}
            self.condDict = {}
            self.baseCondDict = {}
        else:
            self.settings = settingsDict
            if 'nextFlash' not in self.settings.keys():
                self.settings['nextFlash'] = '0'
            if 'baseCondList' not in self.settings.keys():
                self.settings['baseCondList'] = '[]'
                self.settings['baseCondFile'] = ''
            if 'blockList' not in self.settings.keys():
                self.settings['blockList'] = '{}'
            if 'calcHabOver' not in self.settings.keys():
                if len(self.settings['habTrialList'])>0:
                    self.settings['calcHabOver'] = "['Hab']"  # Default to old behavior.
                else:
                    self.settings['calcHabOver'] = "[]"
            if 'blockDataList' not in self.settings.keys():
                self.settings['blockDataList'] = "[]"
            # Settings requiring evaluation to get sensible values. Mostly dicts.
            evalList = ['dataColumns','maxDur','condList','baseCondList','movieEnd','playThrough','trialOrder',
                        'stimNames', 'stimList', 'ISI', 'maxOff','minOn','autoAdvance','playAttnGetter','attnGetterList',
                        'trialTypes','habTrialList', 'calcHabOver', 'nextFlash', 'blockList']
            for i in evalList:
                self.settings[i] = eval(self.settings[i])
                if i in ['stimList','attnGetterList']:
                    for [q,j] in self.settings[i].items():
                        try:
                            j['stimLoc'] = ''.join([self.dirMarker if x == otherOS else x for x in j['stimLoc']])
                        except KeyError: # For image/audio pairs
                            j['audioLoc'] = ''.join([self.dirMarker if x == otherOS else x for x in j['audioLoc']])
                            j['imageLoc'] = ''.join([self.dirMarker if x == otherOS else x for x in j['imageLoc']])
            # Backwards compatibility for ISI
            if type(self.settings['ISI']) is not dict:
                tempISI = {}
                for q in range(0,len(self.settings['trialTypes'])):
                    tempISI[self.settings['trialTypes'][q]] = str(self.settings['ISI'])
                self.settings['ISI'] = tempISI
            # Backwards compatibility for startImage and endImage
            if 'startImage' not in self.settings.keys():
                self.settings['startImage'] = ''
                self.settings['endImage'] = ''
            if 'habThresh' not in self.settings.keys():
                self.settings['habThresh'] = '1.0'
            self.settings['dataloc'] = ''.join([self.dirMarker if x == otherOS else x for x in self.settings['dataloc']])
            self.settings['stimPath'] = ''.join([self.dirMarker if x == otherOS else x for x in self.settings['stimPath']])
            self.settings['folderPath'] = os.getcwd()+self.dirMarker  # On load, reset the folder path to wherever you are now.
            # Get conditions!
            if self.settings['randPres'] in [1,'1','True',True] and len(self.settings['condFile'])>0:  # If there is a condition file
                if os.path.exists(self.settings['folderPath'] + self.settings['condFile']):
                    testReader=csv.reader(open(self.settings['condFile'],'rU'))
                    testStuff=[]
                    for row in testReader:
                        testStuff.append(row)
                    testDict = dict(testStuff)
                    for i in testDict.keys():
                        testDict[i] = eval(testDict[i])
                    self.condDict = testDict
                else:
                    self.condDict = {}
                    self.settings['condList'] = []
                if len(self.settings['baseCondFile'])>0 and os.path.exists(self.settings['folderPath'] + self.settings['baseCondFile']):
                    testReader2 = csv.reader(open(self.settings['baseCondFile'],'rU'))
                    testStuff2 = []
                    for row in testReader2:
                        testStuff2.append(row)
                    newDict = dict(testStuff2)
                    for i in newDict.keys():
                        newDict[i] = eval(newDict[i])
                    self.baseCondDict = newDict
                else:
                    self.baseCondDict = {}
                    self.settings['baseCondList'] = []
            else:
                self.condDict = {}
                self.baseCondDict = {}
        self.folderPath = self.settings['folderPath']  # The location where all the pieces are saved.
        self.allDataColumns = ['sNum', 'sID', 'months', 'days', 'sex', 'cond','condLabel', 'trial','GNG','trialType','stimName','habCrit','habTrialNo','sumOnA','numOnA','sumOffA','numOffA','sumOnB','numOnB','sumOffB','numOffB']
        self.allDataColumnsPL = ['sNum', 'sID', 'months', 'days', 'sex', 'cond','condLabel', 'trial','GNG','trialType','stimName','habCrit','habTrialNo', 'sumOnL','numOnL','sumOnR','numOnR','sumOff','numOff']
        self.stimSource={}  # A list of the source folder(s) for each stimulus file, a dict where each key is the filename in stimNames?
        self.delList=[] # A list of stimuli to delete if they are removed from the experiment library.
        self.allDone=False

        # BEGIN UI CONSTRUCTION
        # The base window
        width = 1080
        height = 600
        self.win = visual.Window((width, height), fullscr=False, allowGUI=True, rgb=[-1, -1, -1],
                                 units='norm')  # Using normalized units.
        self.flowArea = [float(-1), .75, float(1), -.15]  # norm units go from -1 to +1. To cover the top half of the screen would be -1 to 1, and 1 to 0. X,X,Y,Y
        self.flowRect = visual.Rect(self.win, width=self.flowArea[1] - self.flowArea[0],
                                    height=self.flowArea[3] - self.flowArea[2], fillColor='grey',
                                    pos=[self.flowArea[0] + float(abs(self.flowArea[1] - self.flowArea[0])) / 2,
                                         self.flowArea[2] - float(abs(self.flowArea[3] - self.flowArea[2])) / 2])
        self.paletteArea = [.75, float(1), float(1), -.30]  # a trial type pallette, top right
        self.standardPaletteHeight = 1.15  # For certain text elements.
        self.paletteRect = visual.Rect(self.win, width=self.paletteArea[1] - self.paletteArea[0],
                                       height=self.paletteArea[3] - self.paletteArea[2], fillColor='white',
                                       pos=[self.paletteArea[0] + float(abs(self.paletteArea[1] - self.paletteArea[0])) / 2,
                                            self.paletteArea[2] - float(abs(self.paletteArea[3] - self.paletteArea[2])) / 2])
        self.aspect = float(height) / float(width)  # Determine aspect ratio width/height. Impt. for using norm.
        # A bunch of useful stuff for drawing the interface
        self.colorsArray = ['red', 'blue', 'green', 'purple', 'brown', 'LightSeaGreen', 'darkgoldenrod',
                            'Magenta','orange','cornflowerblue','aquamarine','plum','tomato','deepskyblue','lime',
                            'orchid','hotpink','mediumslateblue','lawngreen','fuchsia']  # colors for dif trial types. Will eventually need an arbitrary number...
        self.flowWidMult = .07
        self.flowWidthObj = self.flowWidMult * float(abs(self.flowArea[1] - self.flowArea[0]))  # Width of one item in the flow, though this will possibly have to change...
        self.flowHeightObj = (self.flowWidthObj / self.aspect) * .8
        self.typeWidthObj = .4 * float(abs(self.paletteArea[1] - self.paletteArea[0]))  # Width of one item in the palette, though this will possibly have to change...
        self.typeHeightObj = (self.typeWidthObj / self.aspect) * .6
        self.typeLocs = []
        self.flowLocs = []
        self.overFlowLocs = []  # For >20 trials, go up to 40
        self.flowGap = .09  # A easy reference for the horizontal spacing of items in the flow
        self.mouse = event.Mouse()
        self.trialPalettePage = 1  # A page tracker for the trial type palette. Much like one that exists for conditions.
        self.totalPalettePages = 1  # The maximum number of pages.
        for x in [.25, .75]:  # Two columns of trial types, on one page.
            for z in range(1, 5):  # Trying to leave space for buttons...
                self.typeLocs.append([self.paletteArea[0] + x * (self.paletteArea[1] - self.paletteArea[0]),
                                      self.paletteArea[2] + .3 * -self.standardPaletteHeight + z * .12 * -self.standardPaletteHeight])
        for y in [.25, .75]:  # two rows for the study flow.
            for z in range(1, 11):
                self.flowLocs.append([self.flowArea[0] + z * (self.flowArea[1] - self.flowArea[0]) * self.flowGap,
                                      self.flowArea[2] + y * (self.flowArea[3] - self.flowArea[2])])
        for y in [.2, .4, .6, .8]:  # four rows for the longer study flows.
            for z in range(1, 11):
                self.overFlowLocs.append([self.flowArea[0] + z * (self.flowArea[1] - self.flowArea[0]) * self.flowGap,
                                          self.flowArea[2] + y * (self.flowArea[3] - self.flowArea[2])])
        # Various main UI buttons, put into a dict of lists for easy looping through.
        self.buttonList={'shapes':[],'text':[],'functions':[]}  # Yes, python means we can put the functions in there too.
        if len(self.folderPath) > 0:
            #Make a "save" button, not just a "save as" button, but only if there is a place to save to!
            saveButton = visual.Rect(self.win,width=.15, height=.67*(.15/self.aspect), pos=[-.52,-.9],fillColor="springgreen")
            saveText = visual.TextStim(self.win, text="SAVE",color="black",height=saveButton.height*.5, pos=saveButton.pos)
            self.buttonList['shapes'].append(saveButton)
            self.buttonList['text'].append(saveText)
            self.buttonList['functions'].append(self.saveEverything)
        saveAsButton = visual.Rect(self.win,width=.15, height=.67*(.15/self.aspect), pos=[-.22,-.9],fillColor="springgreen")
        saveAsText = visual.TextStim(self.win, text="Save as",color="black",height=saveAsButton.height*.3, pos=saveAsButton.pos)
        self.buttonList['shapes'].append(saveAsButton)
        self.buttonList['text'].append(saveAsText)
        self.buttonList['functions'].append(self.saveDlg)
        newTrialTypeButton = visual.Rect(self.win, width=.9*(self.paletteArea[1]-self.paletteArea[0]), height=self.standardPaletteHeight*.10, fillColor="yellow", lineColor="black",
                pos=[self.paletteArea[0]+float(abs(self.paletteArea[1]-self.paletteArea[0]))/2, self.paletteArea[2]-self.standardPaletteHeight*.07])
        newTrialTypeText=visual.TextStim(self.win, alignHoriz='center', alignVert='center', text = "New Trial Type",height=.5*newTrialTypeButton.height, pos=newTrialTypeButton.pos,color="black")
        self.buttonList['shapes'].append(newTrialTypeButton)
        self.buttonList['text'].append(newTrialTypeText)
        self.buttonList['functions'].append(self.trialTypeDlg)
        delTrialTypeButton = visual.Rect(self.win, width=.9*(self.paletteArea[1]-self.paletteArea[0]),height=self.standardPaletteHeight*.10, fillColor="lightcoral", lineColor = "black",
                pos=[self.paletteArea[0]+float(abs(self.paletteArea[1]-self.paletteArea[0]))/2,self.paletteArea[3]+self.standardPaletteHeight*.07])
        delTrialTypeText=visual.TextStim(self.win, alignHoriz='center', alignVert='center', text="Delete trial/block",height=.45*delTrialTypeButton.height, pos=delTrialTypeButton.pos,color="black")
        self.buttonList['shapes'].append(delTrialTypeButton)
        self.buttonList['text'].append(delTrialTypeText)
        self.buttonList['functions'].append(self.delTrialTypeDlg)
        rightArrowVerts = [(-.25, 0.05), (-.15, 0.05), (-0.15, 0.15), (0, 0), (-0.15, -0.15), (-0.15, -0.05),(-0.25,-0.05)]
        self.nextPaletteArrow = visual.ShapeStim(self.win, vertices=rightArrowVerts, size=.25, lineColor='black',
                                         fillColor='black', pos=[self.paletteArea[0]+float(abs(self.paletteArea[1]-self.paletteArea[0]))*.9,self.paletteArea[3]+self.standardPaletteHeight*.2])
        self.nextPaletteText = visual.TextStim(self.win, text='', pos=self.nextPaletteArrow.pos)
        leftArrowVerts = [(.25, 0.05), (.15, 0.05), (0.15, 0.15), (0, 0), (0.15, -0.15), (0.15, -0.05),(0.25,-0.05)]
        self.lastPaletteArrow = visual.ShapeStim(self.win, vertices=leftArrowVerts, size=.25, lineColor='black', fillColor='black',
                                         pos=[self.paletteArea[0]+float(abs(self.paletteArea[1]-self.paletteArea[0]))*.05,self.paletteArea[3]+self.standardPaletteHeight*.2])
        self.lastPaletteText = visual.TextStim(self.win, text='', pos=self.lastPaletteArrow.pos)
        self.palettePageText = visual.TextStim(self.win, height=self.standardPaletteHeight*.045, text=str(self.trialPalettePage)+'/'+str(self.totalPalettePages), color='black',
                                               pos=[self.paletteArea[0]+float(abs(self.paletteArea[1]-self.paletteArea[0]))*.5,self.paletteArea[3]+self.standardPaletteHeight*.2])
        self.buttonList['shapes'].append(self.nextPaletteArrow)
        self.buttonList['text'].append(self.palettePageText)
        self.buttonList['functions'].append(self.nextPalettePage)
        self.buttonList['shapes'].append(self.lastPaletteArrow)
        self.buttonList['text'].append(self.lastPaletteText)
        self.buttonList['functions'].append(self.lastPalettePage)
        self.trialTypesArray = self.loadTypes(self.typeLocs, self.trialPalettePage)
        self.studyFlowArray = self.loadFlow(self.settings['trialOrder'], self.flowArea, self.flowLocs,self.overFlowLocs)

        addHabButton = visual.Rect(self.win, width=.9*(self.paletteArea[1]-self.paletteArea[0]),height=self.standardPaletteHeight*.10, fillColor="yellow", lineColor="black",
                pos=[self.paletteArea[0]+float(abs(self.paletteArea[1]-self.paletteArea[0]))/2,self.paletteArea[2]-self.standardPaletteHeight*.18])
        if 'Hab' in self.settings['trialTypes'] or len(self.settings['habTrialList']) > 0:
            txt = 'Mod Hab Block'
        else:
            txt = 'Add Habituation'
        addHabText = visual.TextStim(self.win, alignHoriz='center', alignVert='center', text = txt,height=.5*addHabButton.height, pos=addHabButton.pos,color="black")
        self.buttonList['shapes'].append(addHabButton)
        self.buttonList['text'].append(addHabText)
        self.buttonList['functions'].append(self.addHabBlock)
        addBlockButton = visual.Rect(self.win, width=.9*(self.paletteArea[1]-self.paletteArea[0]),height=self.standardPaletteHeight*.10, fillColor="yellow", lineColor="black",
                pos=[self.paletteArea[0]+float(abs(self.paletteArea[1]-self.paletteArea[0]))/2,self.paletteArea[2]-self.standardPaletteHeight*.29])
        addBlockText = visual.TextStim(self.win, alignHoriz='center', alignVert='center', text="Create Block", height=.5*addBlockButton.height, pos=addBlockButton.pos,color="black")
        self.buttonList['shapes'].append(addBlockButton)
        self.buttonList['text'].append(addBlockText)
        self.buttonList['functions'].append(self.makeBlockDlg)
        quitButton = visual.Rect(self.win,width=.15, height=.67*(.15/self.aspect), pos=[-.82,-.9],fillColor="red")
        quitText = visual.TextStim(self.win, text="QUIT",color="black",height=quitButton.height*.5, pos=quitButton.pos)
        self.buttonList['shapes'].append(quitButton)
        self.buttonList['text'].append(quitText)
        self.buttonList['functions'].append(self.quitFunc)
        # The eight "main" buttons
        USetButton = visual.Rect(self.win, width=.3, height=.5*(.2/self.aspect),pos=[-.8,-.3], fillColor="white")
        USetText = visual.TextStim(self.win, text="Universal \nsettings",color="black",height=USetButton.height*.3, alignHoriz='center', pos=USetButton.pos)
        self.buttonList['shapes'].append(USetButton)
        self.buttonList['text'].append(USetText)
        self.buttonList['functions'].append(self.univSettingsDlg)
        dataSetButton = visual.Rect(self.win, width=.3, height=.5*(.2/self.aspect),pos=[-.8,-.65], fillColor="white")
        dataSetText = visual.TextStim(self.win, text="Data \nsettings",color="black",height=dataSetButton.height*.3, alignHoriz='center', pos=dataSetButton.pos)
        self.buttonList['shapes'].append(dataSetButton)
        self.buttonList['text'].append(dataSetText)
        self.buttonList['functions'].append(self.dataSettingsDlg)
        stimSetButton = visual.Rect(self.win, width=.3, height=.5*(.2/self.aspect),pos=[-.4,-.3], fillColor="white")
        stimSetText = visual.TextStim(self.win, text="Stimuli \nsettings",color="black",height=stimSetButton.height*.3, alignHoriz='center', pos=stimSetButton.pos)
        self.buttonList['shapes'].append(stimSetButton)
        self.buttonList['text'].append(stimSetText)
        self.buttonList['functions'].append(self.stimSettingsDlg)
        condSetButton = visual.Rect(self.win, width=.3, height=.5*(.2/self.aspect),pos=[-.4,-.65], fillColor="white")
        condSetText = visual.TextStim(self.win, text="Condition \nsettings",color="black",height=condSetButton.height*.3, alignHoriz='center', pos=condSetButton.pos)
        self.buttonList['shapes'].append(condSetButton)
        self.buttonList['text'].append(condSetText)
        self.buttonList['functions'].append(self.condSettingsDlg)
        habSetButton = visual.Rect(self.win, width=.3, height=.5*(.2/self.aspect),pos=[0,-.3], fillColor="white")
        habSetText = visual.TextStim(self.win, text="Habituation \nsettings",color="black",height=habSetButton.height*.3, alignHoriz='center', pos=habSetButton.pos)
        self.buttonList['shapes'].append(habSetButton)
        self.buttonList['text'].append(habSetText)
        self.buttonList['functions'].append(self.habSettingsDlg)

        attnGetterButton = visual.Rect(self.win, width=.3, height=.5*(.2/self.aspect), pos=[.4, -.3], fillColor = "white")
        attnGetterText = visual.TextStim(self.win, text="Customize \nattention-getters",color="black",height=attnGetterButton.height*.3,alignHoriz='center', pos=attnGetterButton.pos)
        self.buttonList['shapes'].append(attnGetterButton)
        self.buttonList['text'].append(attnGetterText)
        self.buttonList['functions'].append(self.attnGetterDlg)

        stimLibraryButton = visual.Rect(self.win, width=.3, height=.5*(.2/self.aspect), pos=[0, -.65], fillColor = "white")
        stimLibraryText = visual.TextStim(self.win, text="Add/remove stimuli \nto/from exp. library",color="black",height=stimLibraryButton.height*.3,alignHoriz='center', pos=stimLibraryButton.pos)
        self.buttonList['shapes'].append(stimLibraryButton)
        self.buttonList['text'].append(stimLibraryText)
        self.buttonList['functions'].append(self.addStimToLibraryDlg)

        if len(list(self.settings['stimList'].keys())) > 0:
            addMovButton = visual.Rect(self.win, width=.3, height=.5 * (.2 / self.aspect), pos=[.4, -.65],
                                       fillColor="white")
            addMovText = visual.TextStim(self.win, text="Add stimulus files \nto trial types", color="black",
                                         height=addMovButton.height * .3, alignHoriz='center', pos=addMovButton.pos)
            self.buttonList['shapes'].append(addMovButton)
            self.buttonList['text'].append(addMovText)
            self.buttonList['functions'].append(self.addStimToTypesDlg)

        if len(list(self.settings['blockList'].keys())) > 0:  # Add button for block data settings
            blockDataButton = visual.Rect(self.win, width=.3, height=.5*(.2/self.aspect), pos=[.8, -.65],
                                          fillColor="white")
            blockDataText = visual.TextStim(self.win, text="Save block summary \nfile?", color="black",
                                            height=blockDataButton.height*.3, alignHoriz='center',pos=blockDataButton.pos)
            self.buttonList['shapes'].append(blockDataButton)
            self.buttonList['text'].append(blockDataText)
            self.buttonList['functions'].append(self.blockDataDlg)

        self.workingRect = visual.Rect(self.win, width=1, height=.5, pos=[0,0], fillColor = 'green') #Because there are certain things that take a while.
        self.workingText = visual.TextStim(self.win, text="Working...", height= .3, bold=True, alignHoriz='center', pos=[0,0])

        self.UI = {'bg':[self.flowRect, self.paletteRect], 'buttons': self.buttonList}

    def run(self):
        """
        Exists exclusively to be called to start the main loop.

        :return:
        :rtype:
        """
        self.mainLoop()
    
    def mainLoop(self):
        """
        Main loop of the whole program.

        :return:
        :rtype:
        """
        while self.allDone==False:
            self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)
            self.win.flip()
            #Check all the stand-alone buttons
            for i in range(0, len(self.buttonList['shapes'])):
                if self.mouse.isPressedIn(self.buttonList['shapes'][i],buttons=[0]): #left-click only
                    self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)
                    self.workingRect.draw()
                    self.workingText.draw()
                    self.win.flip()
                    if os.name is not 'posix':
                        while self.mouse.getPressed()[0] == 1:
                            pass
                        self.win.winHandle.set_visible(visible=False)
                    if self.buttonList['functions'][i] == self.addHabBlock: #one special case
                        if self.buttonList['text'][i].text == "Mod Habituation":
                            self.addHabBlock(makeNew=False)
                        else:
                            self.addHabBlock()
                    else:
                        self.buttonList['functions'][i]() #It should not be this easy, BUT IT IS. Python is great.
                    if os.name is not 'posix':
                        self.win.winHandle.set_visible(visible=True)
            #Check all the trial type elements.
            for j in range(0,len(self.trialTypesArray['shapes'])):
                if self.mouse.isPressedIn(self.trialTypesArray['shapes'][j],buttons=[0]): #Left-click, add to study flow, at end.
                    self.settings['trialOrder'].append(self.trialTypesArray['labels'][j])
                    self.studyFlowArray=self.loadFlow(self.settings['trialOrder'], self.flowArea, self.flowLocs, self.overFlowLocs) #Reloads the study flow with the new thing added.
                    while self.mouse.isPressedIn(self.trialTypesArray['shapes'][j],buttons=[0]): #waits until the mouse is released before continuing.
                        pass
                elif self.mouse.isPressedIn(self.trialTypesArray['shapes'][j],buttons=[1,2]): #Right-click, modify trial type info.
                    self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)
                    self.workingRect.draw()
                    self.workingText.draw()
                    self.win.flip()
                    if os.name is not 'posix': #There's an issue with windows and dialog boxes, don't ask.
                        while 1 in self.mouse.getPressed():
                            pass
                        self.win.winHandle.set_visible(visible=False)
                    # Determine whether we're dealing with a trial or block, launch appropriate interface
                    if self.trialTypesArray['labels'][j] in self.settings['blockList'].keys():
                        self.makeBlockDlg(self.trialTypesArray['labels'][j], new=False)
                    elif self.trialTypesArray['labels'][j] == 'Hab' and len(self.settings['habTrialList']) > 0:
                        self.addHabBlock(makeNew=False)
                    elif self.trialTypesArray['labels'][j] == 'Hab':
                        self.makeHabTypeDlg(makeNew=False)
                    else:
                        self.trialTypeDlg(trialType=self.trialTypesArray['labels'][j], makeNew=False)
                    if os.name is not 'posix':
                        self.win.winHandle.set_visible(visible=True)
            for k in range(0, len(self.studyFlowArray['shapes'])):
                if self.mouse.isPressedIn(self.studyFlowArray['shapes'][k]):
                    # Move the trial within the study flow, reload the modified flow array
                    self.settings['trialOrder'] = self.moveTrialInFlow(k, self.settings['trialOrder'], self.flowArea,
                                                                       self.UI, self.studyFlowArray, self.trialTypesArray)
                    self.studyFlowArray = self.loadFlow(self.settings['trialOrder'], self.flowArea, self.flowLocs, self.overFlowLocs)
                    break
        self.win.close()
        
            
    def showMainUI(self, UI, flow, types):
        """
        A simple function that draws everything and flips the display. Generalized to work for block mode and general mode.

        :param UI: a dictionary of everything to be drawn in the new UI. Contains a list, 'bg' (background), and a dict,
        'buttons', that has itself 'shapes' and 'text' (and usually 'functions' but this doesn't need to know that)
        :type UI: dict
        :param flow: A dict of everything in the  block flow. Contains five lists, 'lines', 'shapes', 'text', 'labels', and 'extra'
        :type flow: dict
        :param types: A dict of the trial type buttons for this block. Contains three lists: 'shapes', 'text', and 'labels'
        :type types: dict
        :return:
        :rtype:
        """

        for i in range(0, len(UI['bg'])):
            UI['bg'][i].draw()
        for j in range(0, len(UI['buttons']['shapes'])):
            UI['buttons']['shapes'][j].draw()
            UI['buttons']['text'][j].draw()
        for k in range(0, len(flow['lines'])):
            flow['lines'][k].draw()
        for l in range(0, len(flow['labels'])):
            flow['shapes'][l].draw()
        for m in range(0, len(flow['extras'])):
            flow['extras'][m].draw()
        for n in range(0, len(flow['labels'])):
            flow['text'][n].draw()
        for o in range(0, len(types['labels'])):
            types['shapes'][o].draw()
            types['text'][o].draw()


    def trialTypeDlg(self, trialType="TrialTypeNew", makeNew=True, prevInfo=[]):
        """
        Dialog for creating OR modifying a trial type. Allows you to set
        the maximum duration of that trial type as well as remove movies
        from it, and also set whether the trial type is gaze contingent.
        Now also sets whether the study should auto-advance into this
        trial and whether the built-in attention-getter should be used.

        The dialog by default outputs a list with 8 items in it.
        0 = trial type name

        1 = Maximum duration of trials of this type

        [if movies assigned to trial type already, they occupy 2 - N]

        2/-7 = Gaze-contingent trial type?

        3/-6 = Maximum continuous looking-away to end trial of type

        4/-5 = Minimum on-time to enable off-time criterion (not continuous)

        5/-4 = Auto-advance into trial?

        6/-3 = Attention-getter selection

        7/-2 = End trial on movie end or mid-movie

        8/-1 = inter-stimulus interveral (ISI) for this trial type

        :param trialType: Name of the trial type
        :type trialType: str
        :param makeNew: Making a new trial type or modifying an existing one?
        :type makeNew: bool
        :param prevInfo: If user attempts to create an invalid trial type, the dialog is re-opened with the previously entered information stored and restored
        :type prevInfo: list
        :return:
        :rtype:
        """
        self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)
        self.workingRect.draw()
        self.workingText.draw()
        self.win.flip()
        #For when a trial is right-clicked, or a new one created, open a dialog with info about it.
        skip = False
        if len(self.settings['trialTypes']) == len(self.colorsArray):
            errDlg = gui.Dlg(title="Max trial types reached!")
            errDlg.addText("PyHab's builder currently supports a maximum of " + str(len(self.colorsArray)) + " trial or block types.")
            errDlg.show()
        else:
            typeDlg = gui.Dlg(title="Trial Type " + trialType)
            typeDlg.addField("Trial type name: ", trialType)
            if not makeNew:  # if this modifying an existing trial type, pre-fill the existing info.
                if len(prevInfo) == 0:  # allows for removal of movies from the trial type
                    typeDlg.addField("Max duration", self.settings['maxDur'][trialType])
                    maxOff = self.settings['maxOff'][trialType]
                    minOn = self.settings['minOn'][trialType]
                    ISI = self.settings['ISI'][trialType]
                    if len(self.settings['stimNames'][trialType]) > 0:
                        typeDlg.addText("Current movie files in trial type (uncheck to remove)")
                        for i in range(0,len(self.settings['stimNames'][trialType])):
                            typeDlg.addField(self.settings['stimNames'][trialType][i], initial=True)
                else:
                    typeDlg.addField("Max duration", prevInfo[1])
                    maxOff = prevInfo[-6]
                    minOn = prevInfo[-5]
                    ISI = prevInfo[-1]
                    if len(prevInfo) > 9:  # If there were no movies to start with, this will have a length of 9.
                        typeDlg.addText("Current stimuli in trial type (uncheck to remove)")
                        for i in range(0,len(self.settings['stimNames'][trialType])):
                            typeDlg.addField(self.settings['stimNames'][trialType][i], initial=prevInfo[i+2])
                # Find the index of the existing trial type in the study flow and type pane.
                flowIndexes=[]
                for i in range(0,len(self.studyFlowArray['labels'])):
                    if self.studyFlowArray['labels'][i] == trialType:
                        flowIndexes.append(i) 
                typeIndex = self.trialTypesArray['labels'].index(trialType)
                if self.settings['playThrough'][trialType] == 2:
                    chz = ["No", "OnOnly", "Yes"]
                elif self.settings['playThrough'][trialType] == 1:
                    chz = ["OnOnly", "Yes", "No"]
                else:
                    chz = ["Yes", "OnOnly", "No"]
            elif len(prevInfo) > 0:
                typeDlg.addField("Max duration", prevInfo[1])
                maxOff = prevInfo[-5]
                minOn = prevInfo[-4]
                ISI = prevInfo[-1]
                if prevInfo[4] == 2:
                    chz = ["No", "OnOnly", "Yes"]
                elif prevInfo[4] == 1:
                    chz = ["OnOnly", "Yes", "No"]
                else:
                    chz = ["Yes", "OnOnly", "No"]
            else:  # if there are no existing indexes to refer to
                typeDlg.addField("Max duration", 60.0)
                maxOff = 2.0
                minOn = 1.0
                ISI = 0.0
                chz = ["Yes", "OnOnly", "No"]
            typeDlg.addField("Gaze-contingent trial type (next two lines ignored otherwise)", choices=chz)
            typeDlg.addField("Number of continuous seconds looking away to end trial", maxOff)
            typeDlg.addField("Minimum time looking at screen before stimuli can be ended (not consecutive)", minOn)
            if trialType in self.settings['autoAdvance']:
                chz2 = True
            else:
                chz2 = False
            typeDlg.addField("Auto-advance INTO trial without waiting for expeirmenter?", initial=chz2)
            if trialType not in self.settings['playAttnGetter']:
                ags = list(self.settings['attnGetterList'].keys())
                chz3 = [x for x in ags if x is not 'PyHabDefault']
                if makeNew:
                    chz3.insert(0, 'None')
                    chz3.insert(0, 'PyHabDefault')  # Defaults to...well, the default
                else:
                    chz3.insert(0, 'PyHabDefault')
                    chz3.insert(0, 'None') # Only default to default if this is a new trial type, not if "none" was selected before.
            elif trialType in self.settings['playAttnGetter']:
                chz3 = [x for x in list(self.settings['attnGetterList'].keys()) if x != self.settings['playAttnGetter'][trialType]]
                chz3.insert(0, 'None')
                chz3.insert(0, self.settings['playAttnGetter'][trialType])
            typeDlg.addField("Attention-getter for this trial type (Stim presentation mode only)", choices = chz3)
            if trialType in self.settings['movieEnd']:
                chz4 = True
            else:
                chz4 = False
            typeDlg.addField("Only end trial on end of movie repetition? (Only works when presenting stimuli)", initial = chz4)
            typeDlg.addField("Inter-stimulus interval on loops (pause between end of one loop and start of next)", ISI)
            typeInfo = typeDlg.show()
            if typeDlg.OK:
                # Check if all the things that need to be numbers are actually numbers.
                for i in [1, len(typeInfo) - 5, len(typeInfo) - 4]:
                    if not isinstance(typeInfo[i], float) and not isinstance(typeInfo[i], int):
                        try:
                            typeInfo[i] = eval(typeInfo[i])
                        except:
                            warnDlg = gui.Dlg(title="Warning!")
                            warnDlg.addText(
                                "Number expected, got text instead. \nPlease make sure maximum duration, minimum on-time, and maximum off-time are all numbers!")
                            warnDlg.show()
                            skip = True
                            self.trialTypeDlg(str(typeInfo[0]), makeNew, typeInfo)
                # Update all the things, or create them.
                if not skip:
                    typeInfo[0] = str(typeInfo[0])  # Ditch PyQT mess I hope.
                    if typeInfo[0] is not trialType:  # First, do we need to change the trial type label for an existing type?
                        if not makeNew and typeInfo[0] not in self.trialTypesArray['labels']:
                            # change all the dicts and everything.
                            self.settings['stimNames'][typeInfo[0]] = self.settings['stimNames'].pop(trialType)
                            self.settings['maxDur'][typeInfo[0]]=self.settings['maxDur'].pop(trialType)
                            self.settings['playThrough'][typeInfo[0]] = self.settings['playThrough'].pop(trialType)
                            self.settings['maxOff'][typeInfo[0]] = self.settings['maxOff'].pop(trialType)
                            self.settings['minOn'][typeInfo[0]] = self.settings['minOn'].pop(trialType)
                            # update trial type and study flow too
                            numChar = len(typeInfo[0])
                            if numChar <= 3:
                                numChar = 4  # Maximum height
                            for i in flowIndexes:
                                self.studyFlowArray['labels'][i] = typeInfo[0]
                                self.studyFlowArray['text'][i].text = typeInfo[0]
                                self.studyFlowArray['text'][i].height = self.flowHeightObj/(.42*numChar) #Update text height for new length
                            self.settings['trialTypes'] = [typeInfo[0] if x == trialType else x for x in self.settings['trialTypes']]
                            self.settings['trialOrder'] = [typeInfo[0] if x == trialType else x for x in self.settings['trialOrder']]
                            self.trialTypesArray = self.loadTypes(self.typeLocs,self.trialPalettePage)
                            if len(self.settings['habTrialList']) > 0:
                                for z in range(0, len(self.settings['habTrialList'])):
                                    if self.settings['habTrialList'][z] == trialType:
                                        self.settings['habTrialList'][z] = typeInfo[0]
                            for a, b in self.settings['blockList'].items():
                                for c in range(0, len(b)):
                                    if b[c] == trialType:
                                        b[c] = typeInfo[0]

                        elif typeInfo[0] in self.trialTypesArray['labels']:
                            #warning dialog, start over with all info entered so far.
                            warnDlg = gui.Dlg(title="Warning!")
                            warnDlg.addText("New trial type label matches an existing trial type! Please choose a different name for this trial type.")
                            warnDlg.show()
                            skip = True
                            self.trialTypeDlg(typeInfo[0], makeNew, typeInfo)
                        elif '.' in typeInfo[0] or '^' in typeInfo[0]:
                            warnDlg = gui.Dlg(title="llegal character!")
                            warnDlg.addText("The '.' and '^' characters cannot be used as part of a trial type name. Please rename your trial type")
                            warnDlg.show()
                            skip = True
                            self.trialTypeDlg(typeInfo[0], makeNew, typeInfo)
                        trialType = typeInfo[0]
                    if not skip:

                        self.settings['maxDur'][trialType] = typeInfo[1] #Update maxDur
                        self.settings['maxOff'][trialType] = typeInfo[len(typeInfo)-6]
                        self.settings['minOn'][trialType] = typeInfo[len(typeInfo)-5]
                        self.settings['ISI'][trialType] = typeInfo[len(typeInfo)-1]

                        # Gaze-contingency settings
                        if trialType not in self.settings['playThrough'].keys(): #Initialize if needed.
                            self.settings['playThrough'][trialType] = 0
                        if typeInfo[len(typeInfo)-7] == "Yes" and self.settings['playThrough'][trialType] is not 0: #gaze-contingent trial type, not already tagged as such.
                            self.settings['playThrough'][trialType] = 0
                        elif typeInfo[len(typeInfo)-7] == "No" and self.settings['playThrough'][trialType] is not 2:
                            self.settings['playThrough'][trialType] = 2
                        elif typeInfo[len(typeInfo)-7] == "OnOnly" and self.settings['playThrough'][trialType] is not 1:
                            self.settings['playThrough'][trialType] = 1

                        # Auto-advance settings
                        if typeInfo[len(typeInfo)-4] in [False,0,'False','0'] and trialType in self.settings['autoAdvance']: #gaze-contingent trial type, not already tagged as such.
                            self.settings['autoAdvance'].remove(trialType)
                        elif typeInfo[len(typeInfo)-4] in [True, 1, 'True', '1'] and not trialType in self.settings['autoAdvance']:
                            self.settings['autoAdvance'].append(trialType)

                        # Attention-getter settings
                        if typeInfo[len(typeInfo)-3] == 'None':
                            if trialType in self.settings['playAttnGetter']:
                                del self.settings['playAttnGetter'][trialType]
                        else:
                            if trialType not in self.settings['playAttnGetter']:  # If it did not have an attngetter before.
                                agname = typeInfo[len(typeInfo)-3]
                                self.settings['playAttnGetter'][trialType] = agname
                            elif typeInfo[len(typeInfo) - 3] is not self.settings['playAttnGetter'][trialType]:
                                # If a different attention-getter has been selected
                                agname = typeInfo[len(typeInfo) - 3]
                                self.settings['playAttnGetter'][trialType] = agname

                        # End-trial-on-movie-end settings
                        if typeInfo[len(typeInfo)-2] in [False,0,'False','0'] and trialType in self.settings['movieEnd']:
                            self.settings['movieEnd'].remove(trialType)
                        elif typeInfo[len(typeInfo)-2] in [True, 1, 'True', '1'] and not trialType in self.settings['movieEnd']:
                            self.settings['movieEnd'].append(trialType)


                        # Remove stimuli if needed
                        if len(typeInfo) > 9: #Again, if there were movies to list.
                            tempMovies = [] #This will just replace the stimNames list
                            for i in range(0,len(self.settings['stimNames'][trialType])):
                                if typeInfo[i+2]:
                                    tempMovies.append(self.settings['stimNames'][trialType][i])
                            self.settings['stimNames'][trialType] = tempMovies

                        # If we need to update the flow pane, it's taken care of above. Here we update the type pallette.
                        if makeNew:
                            self.settings['trialTypes'].append(typeInfo[0])
                            self.settings['stimNames'][typeInfo[0]] = []
                            if len(self.settings['trialTypes']) in [9, 17]:
                                self.totalPalettePages += 1
                                self.trialPalettePage = deepcopy(self.totalPalettePages)
                            self.trialTypesArray = self.loadTypes(self.typeLocs, self.trialPalettePage)
                            # If there exists a condition file or condition settings, warn the user that they will need to be updated!
                            if self.settings['condFile'] is not '':
                                warnDlg = gui.Dlg(title="Update conditions")
                                warnDlg.addText("WARNING! UPDATE CONDITION SETTINGS AFTER ADDING STIMULI TO THIS TRIAL TYPE! \nIf you do not update conditions, the experiment will crash whenever it reaches this trial type.")
                                warnDlg.show()
                self.studyFlowArray = self.loadFlow(self.settings['trialOrder'], self.flowArea, self.flowLocs, self.overFlowLocs)
                self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)
                self.win.flip()

    def addHabBlock(self, makeNew = True):
        """
        Creates either a hab trial type, or a hab trial block.

        Trial type dialog:

        0 = Maximum duration

        1 = Maximum continuous off-time

        2 = Minimum on-time

        [If stimulus files associated with type, these occupy 3-N]

        3/-3 = Auto-advance into trial

        4/-2 = Select attention-getter

        5/-1 = Inter-stimulus interval (ISI)

        :param makeNew: Making a new  or modifying
        :return:
        :rtype:
        """
        # Type or block?
        habInitDlg = gui.Dlg("One trial type, or multi-trial block?")
        if len(self.settings['habTrialList']) > 0:
            initchz = ['Multi-trial block', 'Single trial type']
        else:
            initchz = ['Single trial type', 'Multi-trial block']
        habInitDlg.addField("Habituation trial type, or block?", choices=initchz)
        if len(self.settings['habTrialList']) > 0:
            habInitDlg.addText("NOTE: Changing to single trial type will delete block!")
        elif len(self.settings['habTrialList']) == 0 and 'Hab' in self.settings['trialTypes']:
            habInitDlg.addText("NOTE: Changing to block will delete Hab trial type!")
        habInitInfo = habInitDlg.show()
        if habInitDlg.OK:
            habInitInfo[0] = str(habInitInfo[0])  # Safety for PyQt malarky
            if habInitInfo[0] == 'Single trial type':
                self.makeHabTypeDlg(makeNew)
            elif habInitInfo[0] == 'Multi-trial block':
                if os.name is not 'posix':
                    self.win.winHandle.set_visible(visible=True)
                if makeNew or len(self.settings['habTrialList']) == 0:
                    # Neatly accounts for swapping in a block for a single trial type.
                    self.blockMaker('Hab', new=True, hab=True)
                else:
                    self.blockMaker('Hab', new=False, hab=True)

    def makeHabTypeDlg(self, makeNew, prevSet=[]):
        """
        A function for creating a habituation trial type, rather than multi-trial block.

        0: Maximum duration
        1: Maximum off-time
        2: Minimum on-time
        3-N: Stimuli added to trial type
        -3: Auto-advance
        -2: Attention-getter
        -1: ISI

        :param makeNew: Making a new trial or revising an existing one?
        :type makeNew: bool
        :return:
        :rtype:
        """
        if len(self.settings['habTrialList']) > 0:
            makeNew = True
        # Some stuff is predetermined, specifically name and gaze-contingency
        typeDlg = gui.Dlg(title="Hab trial type creator")
        typeDlg.addText("Hab trial type settings")
        if not makeNew:
            typeDlg.addField("Maximum duration", self.settings['maxDur']['Hab'])
            typeDlg.addField("Number of continuous seconds looking away to end trial", self.settings['maxOff']['Hab'])
            typeDlg.addField("Minimum time looking at screen before stimuli can be ended (not consecutive)",
                             self.settings['minOn']['Hab'])
            ISI = self.settings['ISI']['Hab']
            if len(self.settings['stimNames']['Hab']) > 0:
                typeDlg.addText("Current movie files in trial type (uncheck to remove)")
                for i in range(0, len(self.settings['stimNames']['Hab'])):
                    typeDlg.addField(self.settings['stimNames']['Hab'][i], initial=True)

        elif len(prevSet) > 0:
            typeDlg.addField("Maximum duration", prevSet[0])
            typeDlg.addField("Number of continuous seconds looking away to end trial", prevSet[1])
            typeDlg.addField("Minimum time looking at screen before stimuli can be ended (not consecutive)",
                             prevSet[2])
            ISI = prevSet[-1]
        else:
            typeDlg.addField("Maximum duration", 60.0)
            typeDlg.addField("Number of continuous seconds looking away to end trial", 2.0)
            typeDlg.addField("Minimum time looking at screen before stimuli can be ended (not consecutive)", 1.0)
            ISI = 0.0
        if 'Hab' in self.settings['autoAdvance']:
            chz2 = True
        elif len(prevSet) > 0:
            if prevSet[-3] in [1, '1', True, 'True']:
                chz2 = True
            else:
                chz2 = False
        else:
            chz2 = False
        typeDlg.addField("Auto-advance INTO trial without waiting for experimenter?", initial=chz2)
        if 'Hab' in self.settings['playAttnGetter']:
            chz3 = [x for x in list(self.settings['attnGetterList'].keys()) if
                    x is not self.settings['playAttnGetter']['Hab']]
            chz3.insert(0, 'None')
            chz3.insert(0, self.settings['playAttnGetter']['Hab'])
        elif len(prevSet) == 0:
            ags = list(self.settings['attnGetterList'].keys())
            chz3 = [x for x in ags if x is not 'PyHabDefault']
            chz3.insert(0, 'None')
            chz3.insert(0, 'PyHabDefault')  # Defaults to...well, the default
        else:
            chz3 = [x for x in list(self.settings['attnGetterList'].keys()) if
                    x is not prevSet[-2]]
            chz3.insert(0, 'None')
            chz3.insert(0, prevSet[-2])
        typeDlg.addField("Attention-getter for this trial type (Stim presentation mode only)", choices=chz3)
        typeDlg.addField("Inter-stimulus interval on loops (pause between end of one loop and start of next)", ISI)
        habInfo = typeDlg.show()

        if typeDlg.OK:
            if len(self.settings['habTrialList']) > 0:
                self.settings['habTrialList'] = []  # If the sub-block functionality was on and is now off
                self.settings['calcHabOver'] = []
                self.deleteType('Hab')
            skip = False
            # On OK, create a new ui with a drop-down from trialtypes that includes hab.
            for i in [0, 1, 2]:
                if not isinstance(habInfo[i], float) and not isinstance(habInfo[i], int):
                    try:
                        habInfo[i] = eval(habInfo[i])
                    except:
                        warnDlg = gui.Dlg(title="Warning!")
                        warnDlg.addText("Number expected, got text instead. \nPlease make sure maximum duration, minimum on-time, and maximum off-time are all numbers!")
                        warnDlg.show()
                        skip = True
                        self.makeHabTypeDlg(makeNew, prevSet=habInfo)
            if not skip:
                # Need to change text of hab button
                self.settings['playThrough']['Hab'] = 0  # This will always be the case
                x = self.buttonList['functions'].index(self.addHabBlock)  # gets index
                self.buttonList['text'][x].text = "Mod Habituation"  # Updates button text
                self.settings['maxDur']['Hab'] = habInfo[0]
                self.settings['maxOff']['Hab'] = habInfo[1]
                self.settings['minOn']['Hab'] = habInfo[2]
                self.settings['ISI']['Hab'] = habInfo[len(habInfo) - 1]
                if habInfo[len(habInfo) - 3] in [False, 0, 'False', '0'] and 'Hab' in self.settings['autoAdvance']:
                    self.settings['autoAdvance'].remove('Hab')
                elif habInfo[len(habInfo) - 3] in [True, 1, 'True', '1'] and not 'Hab' in self.settings['autoAdvance']:
                    self.settings['autoAdvance'].append('Hab')

                if habInfo[len(habInfo) - 2] == 'None':
                    if 'Hab' in self.settings['playAttnGetter']:
                        del self.settings['playAttnGetter']['Hab']
                else:
                    if 'Hab' not in self.settings['playAttnGetter']:  # If it did not have an attngetter before.
                        agname = habInfo[len(habInfo) - 2]
                        self.settings['playAttnGetter']['Hab'] = agname
                    elif habInfo[len(habInfo) - 2] is not self.settings['playAttnGetter']['Hab']:
                        # If a different attention-getter has been selected
                        agname = habInfo[len(habInfo) - 2]
                        self.settings['playAttnGetter']['Hab'] = agname

                if makeNew:
                    i = len(self.trialTypesArray['labels'])  # Conveniently the index we need for position info etc.
                    self.trialTypesArray['labels'].append('Hab')
                    tempObj = visual.Rect(self.win, width=self.typeWidthObj, height=self.typeHeightObj,
                                          fillColor=self.colorsArray[i], pos=self.typeLocs[i])
                    numChar = len('Hab')
                    if numChar <= 3:
                        numChar = 4  # Maximum height
                    tempTxt = visual.TextStim(self.win, alignHoriz='center', alignVert='center', bold=True,
                                              height=self.typeHeightObj / (.38 * numChar), text='Hab',
                                              pos=self.typeLocs[i])
                    self.trialTypesArray['shapes'].append(tempObj)
                    self.trialTypesArray['text'].append(tempTxt)
                    self.settings['trialTypes'].append('Hab')
                    self.settings['stimNames']['Hab'] = []
                # Check about movies.
                if len(habInfo) > 6:  # Again, if there were movies to list.
                    tempMovies = []  # This will just replace the stimNames list
                    for i in range(0, len(self.settings['stimNames']['Hab'])):
                        if habInfo[i + 3]:
                            tempMovies.append(self.settings['stimNames']['Hab'][i])
                    self.settings['stimNames']['Hab'] = tempMovies

    def makeBlockDlg(self, name='', new=True):
        """
        Creates a new 'block' structure, which basically masquerades as a trial type in most regards, but consists of
        several sub-trials, much like how habituation blocks work.

        :param name: Name of existing trial type. '' by default
        :type name: str
        :param new: Making a new block, or modifying an existing one?
        :type new: bool
        :return:
        :rtype:
        """
        if len(self.settings['trialTypes']) > 0:
            self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)
            self.workingRect.draw()
            self.workingText.draw()
            self.win.flip()
            newBlockDlg = gui.Dlg(title="Create new block")
            newBlockDlg.addField("Block name: ", initial=name)
            newBlockDlg.addText("Hit OK to select trials for this block")
            newBlock = newBlockDlg.show()
            if newBlockDlg.OK:
                newBlock[0] = str(newBlock[0])  # In case PyQT does something weird
                if newBlock[0] == '':
                    errDlg = gui.Dlg(title="Missing information!")
                    errDlg.addText("Name cannot be blank!")
                    irrel = errDlg.show()
                    self.makeBlockDlg(name, new)
                elif newBlock[0] == 'Hab' or '.' in newBlock[0] or '^' in newBlock[0]:
                    errDlg = gui.Dlg(title="Illegal block name!")
                    errDlg.addText("Name contains illegal character, or is reserved. Please rename!")
                    errDlg.addText("To create habituation blocks, please use the 'Add Habituation' button.")
                    irrel = errDlg.show()
                    self.makeBlockDlg(name, new)
                elif new and newBlock[0] in self.settings['trialTypes']:
                    errDlg = gui.Dlg(title="Name already in use!")
                    errDlg.addText("Name is already in use for another trial or block. Please rename!")
                    irrel = errDlg.show()
                    self.makeBlockDlg(name, new)
                else:
                    if not new and name != newBlock[0]:
                        # Change the name of the extant block.
                        blockIndex = self.trialTypesArray['labels'].index(name)
                        numChar = len(newBlock[0])
                        if numChar <= 3:
                            numChar = 4  # Maximum height
                        self.settings['blockList'][newBlock[0]] = self.settings['blockList'].pop(name)
                        flowIndexes = []
                        for i in range(0, len(self.studyFlowArray['labels'])):
                            if self.studyFlowArray['labels'][i] == name:
                                flowIndexes.append(i)
                        for i in flowIndexes:
                            self.studyFlowArray['labels'][i] = newBlock[0]
                            self.studyFlowArray['text'][i].text = newBlock[0]
                            self.studyFlowArray['text'][i].height = self.flowHeightObj / (
                                        .42 * numChar)  # Update text height for new length
                        self.trialTypesArray['labels'][blockIndex] = newBlock[0]
                        self.trialTypesArray['text'][blockIndex].text = newBlock[0]
                        self.trialTypesArray['text'][blockIndex].height = self.typeHeightObj / (.33 * numChar)
                        self.settings['trialTypes'] = [newBlock[0] if x == name else x for x in self.settings['trialTypes']]
                        self.settings['trialOrder'] = [newBlock[0] if x == name else x for x in self.settings['trialOrder']]
                        if len(self.settings['habTrialList']) > 0:
                            for z in range(0, len(self.settings['habTrialList'])):
                                if self.settings['habTrialList'][z] == name:
                                    self.settings['habTrialList'][z] = newBlock[0]
                        for a, b in self.settings['blockList'].items():
                            for c in range(0, len(b)):
                                if b[c] == name:
                                    b[c] = newBlock[0]
                if os.name is not 'posix':
                    # For Windows, because now we snap back to the regular window.
                    self.win.winHandle.set_visible(visible=True)
                self.blockMaker(newBlock[0], new)
        else:
            errDlg = gui.Dlg(title="No trials to make blocks with!")
            errDlg.addText("Make some trial types before trying to add them to a block.")
            irrel = errDlg.show()


    def blockMaker(self, blockName, new=True, hab=False):
        """
        For making multi-trial blocks. Or multi-block-blocks. You can make blocks of other blocks!
        Creates a kind of sub-UI that overlays over the main UI. Because it's just for blocks, we can ditch some things.
        We can actually completely overlay the regular UI. Problem is, if the regular UI continues to draw, the mouse
        detection will still work, even if a shape is behind another shape. So, like with conditions, we need a totally
        parallel UI

        :param blockName: Name of new block
        :type blockName: str
        :param new: Is this a new block or a modification of an existing one?
        :type new: bool
        :param hab: Is this for a habituation meta-trial?
        :type hab: bool
        :return:
        :rtype:
        """
        self.showMainUI(self.UI,self.studyFlowArray, self.trialTypesArray)  # Draw the usual UI under the new one...
        # Define new flow UI. We can reuse a lot of the base UI, happily.
        blockUI = {'bg':[],'buttons':{'shapes':[],'text':[],'functions':[]}}
        blockOrder = []  # This will be what contains the order for the block!
        end = False
        newFlowArea = [-.97, .75, .97, -.97]  # X,X,Y,Y
        newFlowRect = visual.Rect(self.win, width=newFlowArea[1] - newFlowArea[0],
                                    height=newFlowArea[3] - newFlowArea[2], fillColor='lightgrey', lineColor='black',
                                    pos=[newFlowArea[0] + float(abs(newFlowArea[1] - newFlowArea[0])) / 2,
                                         newFlowArea[2] - float(abs(newFlowArea[3] - newFlowArea[2])) / 2])

        doneButton = visual.Rect(self.win,width=.15, height=.67*(.15/self.aspect), pos=[-.72,-.8],fillColor="springgreen")
        doneText = visual.TextStim(self.win, text="Done", height=.5*doneButton.height, pos=doneButton.pos, color='black')
        cancelButton = visual.Rect(self.win, width=.15, height=.67 * (.15 / self.aspect), pos=[-.52, -.8],
                                 fillColor="red")
        cancelText = visual.TextStim(self.win, text="Cancel", height=.45 * doneButton.height, pos=cancelButton.pos,
                                   color='white')
        instrText = visual.TextStim(self.win, text="Construct block trial order", pos=[.1, -.9], color='black', height=.1)
        bigPaletteArea = [.7,.95,.97,-.97]  # temporary, bigger palette, without trial type maker buttons!
        bigPaletteRect = visual.Rect(self.win, width=bigPaletteArea[1] - bigPaletteArea[0],
                                       height=bigPaletteArea[3] - bigPaletteArea[2], fillColor='white', lineColor='black',
                                       pos=[bigPaletteArea[0] + float(abs(bigPaletteArea[1] - bigPaletteArea[0])) / 2,
                                            bigPaletteArea[2] - float(abs(bigPaletteArea[3] - bigPaletteArea[2])) / 2])
        blockUI['bg'].append(newFlowRect)
        blockUI['bg'].append(bigPaletteRect)
        blockUI['bg'].append(instrText)
        blockUI['buttons']['shapes'].append(doneButton)
        blockUI['buttons']['text'].append(doneText)
        blockUI['buttons']['shapes'].append(cancelButton)
        blockUI['buttons']['text'].append(cancelText)

        bigPaletteLocs = []
        newFlowLocs = []
        for x in [.27, .73]:  # Two columns of trial types
            for z in range(0, 10):
                bigPaletteLocs.append([bigPaletteArea[0] + x * (bigPaletteArea[1] - bigPaletteArea[0]),
                                      bigPaletteArea[2] + .05 * (bigPaletteArea[3] - bigPaletteArea[2]) + z * .09 * (bigPaletteArea[3] - bigPaletteArea[2])])
        for y in [.2, .4, .6, .8]:  # four rows for the block flow.
            for z in range(1,11):
                newFlowLocs.append([newFlowArea[0] + z * (newFlowArea[1] - newFlowArea[0]) * self.flowGap,
                                    newFlowArea[2] + y * (newFlowArea[3] - newFlowArea[2])])
        trialTypes = self.loadTypes(bigPaletteLocs)
        delIndex = []
        forbid = ['Hab', blockName]  # If we're using this to make hab blocks, we need to allow (indeed mandate) Hab trials.
        for q,z in self.settings['blockList'].items(): # Attempt to eliminate infinite loops
            if blockName in z and blockName != q:
                forbid.append(q)
        for i in range(0, len(trialTypes['labels'])):
            if trialTypes['labels'][i] in forbid:
                delIndex.insert(0,deepcopy(i))  # In reverse order, because it makes the next part way simpler
        for j in range(0, len(delIndex)):
            del trialTypes['labels'][delIndex[j]]
            del trialTypes['shapes'][delIndex[j]]
            del trialTypes['text'][delIndex[j]]
        # Go through and update positions
        for k in range(0, len(trialTypes['labels'])):
            trialTypes['shapes'][k].pos = bigPaletteLocs[k]
            trialTypes['text'][k].pos = bigPaletteLocs[k]
        if not new and not hab:
            blockOrder = deepcopy(self.settings['blockList'][blockName])
            blockFlow = self.loadFlow(tOrd=blockOrder, space=newFlowArea, locs=newFlowLocs, overflow=newFlowLocs)
        elif not new:  # Modifying existing hab meta-trials
            blockOrder = deepcopy(self.settings['habTrialList'])
            blockFlow = self.loadFlow(tOrd=blockOrder, space=newFlowArea, locs=newFlowLocs, overflow=newFlowLocs)
        else:
            blockFlow = {'lines': [], 'shapes': [], 'text': [], 'labels': [], 'extras': []}

        done = False
        while not done:  # A heavily pared-down version of mainLoop that only allows trial flow editing and 'done'/'cancel'
            self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)  # Draw the usual UI under the new one. Just aesthetic
            self.showMainUI(blockUI, blockFlow, trialTypes)
            self.win.flip()
            for i in range(0, len(blockUI['buttons']['shapes'])):
                if self.mouse.isPressedIn(blockUI['buttons']['shapes'][i]):
                    if blockUI['buttons']['text'][i].text == 'Done':
                        if len(blockFlow['labels']) == 0:
                            errDlg = gui.Dlg(title="Empty block!")
                            errDlg.addText("Block must contain at least one trial! Use cancel to stop block construction")
                            errDlg.show()
                        elif hab:  # Create or modify hab block. Special rules apply.
                            for z in range(0, len(blockOrder)):
                                if blockOrder[z] != 'Hab':
                                    blockOrder[z] = blockOrder[z]
                            if 'Hab' in self.settings['trialTypes'] and 'Hab' not in self.settings['blockList'].keys():
                                self.deleteType('Hab')  # It's that simple. It'll shuffle 'hab' to the end of the pallette, but it won't change the color or anything.
                            self.settings['habTrialList'] = blockOrder
                            self.settings['blockList']['Hab'] = blockOrder #TODO: Doubling up for now...
                            if new:
                                self.settings['calcHabOver'] = [blockOrder[-1]]  # Default to last trial.
                                self.settings['trialTypes'].append('Hab')
                                self.trialTypesArray = self.loadTypes(self.typeLocs, self.trialPalettePage)
                            done = True
                            self.habSettingsDlg()  # For setting which things to hab over.
                        else:  # Create our new block or modify existing
                            self.settings['blockList'][blockName] = blockOrder
                            if new:
                                self.settings['trialTypes'].append(blockName)
                                self.trialTypesArray = self.loadTypes(self.typeLocs, self.trialPalettePage)
                            else:
                                self.studyFlowArray=self.loadFlow(self.settings['trialOrder'], self.flowArea, self.flowLocs, self.overFlowLocs)
                            done = True
                            if self.blockDataDlg not in self.buttonList['functions']:
                                blockDataButton = visual.Rect(self.win, width=.3, height=.5 * (.2 / self.aspect),
                                                              pos=[.8, -.65],
                                                              fillColor="white")
                                blockDataText = visual.TextStim(self.win, text="Save block summary \nfile?",
                                                                color="black",
                                                                height=blockDataButton.height * .3, alignHoriz='center',
                                                                pos=blockDataButton.pos)
                                self.buttonList['shapes'].append(blockDataButton)
                                self.buttonList['text'].append(blockDataText)
                                self.buttonList['functions'].append(self.blockDataDlg)
                            while self.mouse.isPressedIn(blockUI['buttons']['shapes'][i], buttons=[0]):  # waits until the mouse is released before continuing.
                                pass
                    elif blockUI['buttons']['text'][i].text == 'Cancel':
                        done = True  # Just break the loop and that's that.
                        while self.mouse.isPressedIn(blockUI['buttons']['shapes'][i], buttons=[0]):  # waits until the mouse is released before continuing.
                            pass
            for j in range(0, len(trialTypes['shapes'])):  # Only need to worry about adding trials, no modding them from here!
                if self.mouse.isPressedIn(trialTypes['shapes'][j], buttons=[0]):
                    blockOrder.append(trialTypes['labels'][j])
                    blockFlow = self.loadFlow(tOrd=blockOrder, space=newFlowArea, locs=newFlowLocs, overflow=newFlowLocs)
                    while self.mouse.isPressedIn(trialTypes['shapes'][j],buttons=[0]):  # waits until the mouse is released before continuing.
                        pass
            for k in range(0, len(blockFlow['shapes'])):  # Rearrange or remove, as in the usual loop!
                if self.mouse.isPressedIn(blockFlow['shapes'][k], buttons=[0]):
                    blockOrder = self.moveTrialInFlow(k, blockOrder, newFlowArea, blockUI, blockFlow, trialTypes)
                    blockFlow = self.loadFlow(tOrd=blockOrder, space=newFlowArea, locs=newFlowLocs, overflow=newFlowLocs)
                    break


    def blockDataDlg(self):
        """
        A dialog for determining whether you save a block data file, and if so which blocks to compress.

        Procedurally constructs a set of options such that, for any nested blocks, they are mutually exclusive, but any
        blocks that are not part of other blocks and other blocks are not part of them are just check-boxes.

        Excludes hab because habituation data files are saved by default.

        :return:
        :rtype:
        """

        tempBlockList = list(self.settings['blockList'].keys())
        fieldList = []
        doneLoop = False
        iteration = 0

        while not doneLoop:
            # This complex, messy loop is identifying all nested blocks, and inserting them into the eventual
            # dialog as lists from which you can pick one, while leaving the stand-alone blocks as check boxes.
            blockName = tempBlockList[iteration]
            delIndex = []
            forbid = []
            for q in range(0, len(self.settings['blockList'][blockName])):
                if self.settings['blockList'][blockName][q] in self.settings['blockList'].keys():
                    # Identifies any nested blocks
                    forbid.append(self.settings['blockList'][blockName][q])
            if len(forbid) > 0:
                # This ultimately becomes the list that will appear in the dialog
                forbid.insert(0, blockName)
                forbid.insert(0, 'None')
                delIndex2=[]
                for i in range(0, len(tempBlockList)):
                    if tempBlockList[i] in forbid:
                        delIndex.insert(0, deepcopy(i))  # In reverse order, because it makes the next part way simpler
                for j in range(0, len(delIndex)):
                    del tempBlockList[delIndex[j]]
                    if delIndex[j] <= iteration:
                        # Rewind as far as you need to rewind.
                        iteration -= 1
                for k in range(0, len(fieldList)):
                    if isinstance(fieldList[k],list):
                        # Find any lists which already exists and incorporate them if needed.
                        addAll = False
                        for q in range(0, len(fieldList[k])):
                            if fieldList[k][q] in forbid:
                                delIndex2.insert(0, deepcopy(k))
                                addAll = True
                        if addAll:
                            for q in range(0, len(fieldList[k])):
                                forbid.append(fieldList[k][q])
                            forbid = list(dict.fromkeys(forbid)) # Removes all duplicate entries. It's a cute move.
                    elif fieldList[k] in forbid:
                        # Otherwise just get rid of any previous instance of the block in the list of fields.
                        delIndex2.insert(0, deepcopy(k))
                for l in range(0, len(delIndex2)):
                    del fieldList[delIndex2[l]]
                fieldList.append(forbid)
                if iteration < 0:
                    iteration = 0
            else:
                fieldList.append(blockName)
                iteration += 1
            print(fieldList)
            if iteration >= len(tempBlockList):
                doneLoop = True

        blockDataDlg = gui.Dlg("Pick blocks for block data summary file")
        blockDataDlg.addText("For nested blocks, pick which one you want to condense in the summary file (one line per instance of this block).")
        blockDataDlg.addText("Check all non-nested blocks you want to condense.")
        for a in range(0, len(fieldList)):
            if isinstance(fieldList[a], list):
                blockDataDlg.addField("Pick one of these nested blocks to record data for", choices=fieldList[a])
            else:
                blockDataDlg.addField(fieldList[a], initial=False)

        blockDataInfo = blockDataDlg.show()
        if blockDataDlg.OK:
            finalList = []
            for i in range(0, len(fieldList)):
                if isinstance(fieldList[i], list):
                    if blockDataInfo[i] is not 'None':
                        finalList.append(blockDataInfo[i])
                else:
                    if blockDataInfo[i]:
                        finalList.append(fieldList[i])
            self.settings['blockDataList'] = finalList


    def delTrialTypeDlg(self):
        """
        Dialog for deleting a trial type, and all instances of that trial type in the study flow

        :return:
        :rtype:
        """
        self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)
        self.workingRect.draw()
        self.workingText.draw()
        self.win.flip()
        delTypeDlg = gui.Dlg(title="Choose trial type or block to delete.")
        delTypeDlg.addText("Warning: Cannot be undone. All instances of this trial or block in study flow will also be removed!")
        delTypeDlg.addField("Choose trial type or block to delete, then hit OK.", choices=self.trialTypesArray['labels'])
        delInfo=delTypeDlg.show()
        if delTypeDlg.OK:
            dType=delInfo[0]
            self.deleteType(dType)


    def deleteType(self, dType):
        """
        Performs the actual deletion of a trial or block type.
        TODO: More sophisticated handling of conditions.

        :param dType: String indicating the name of the trial or block to be deleted
        :type dType: str
        :return:
        :rtype:
        """
        # Reassign colors if neccessary.
        if self.settings['trialTypes'].index(dType) < len(self.settings['trialTypes']):
            nowColor = self.colorsArray.pop(self.settings['trialTypes'].index(dType))
            self.colorsArray.insert(len(self.settings['trialTypes']) - 1, nowColor)
        self.settings['trialTypes'].remove(dType)  # remove the type from the list of trial types.
        if dType in self.settings['blockList'].keys():  # Block vs. trial
            del self.settings['blockList'][dType]
        else:
            keylist = ['stimNames','maxDur','minOn','maxOff','ISI']
            for j in range(0, len(keylist)):
                if dType in self.settings[keylist[j]].keys():
                    del self.settings[keylist[j]][dType]
            if dType in self.settings['playThrough']:  # if it was in playThrough, remove it from there too.
                self.settings['playThrough'].pop(dType, None)
        if dType in self.settings['habTrialList']:  # If it was in a hab meta-trial.
            while dType in self.settings['habTrialList']:
                self.settings['habTrialList'].remove(dType)
            if dType in self.settings['calcHabOver']:
                self.settings['calcHabOver'].remove(dType)
        for i, j in self.settings['blockList'].items():  # If it's part of a block
            while dType in j:
                j.remove(dType)
        self.trialTypesArray = self.loadTypes(self.typeLocs,self.trialPalettePage)  # easiest to just reload the trial types.
        # For the study flow, it's easiest just to remove it from the trial order and reload the study flow.
        if dType in self.settings['trialOrder']:
            while dType in self.settings['trialOrder']:
                self.settings['trialOrder'].remove(dType)
        self.studyFlowArray = self.loadFlow(self.settings['trialOrder'], self.flowArea, self.flowLocs, self.overFlowLocs)  # To update colors if needed.
        if self.settings['condFile'] is not '':
            warnDlg = gui.Dlg(title="Update conditions")
            warnDlg.addText(
                "WARNING! UPDATE CONDITION SETTINGS AFTER REMOVING THIS TRIAL TYPE! \nIf you do not update conditions, the experiment may crash when you try to run it.")
            warnDlg.show()

    def moveTrialInFlow(self, flowIndex, tOrd, flowSpace, UI, flow, types):
        """
        A function for when a trial is clicked in a trial flow, allowing you to either swap it or remove it.

        :param flowIndex: The index in the flowArray of the trial being modified
        :type flowIndex: int
        :param tOrd: The trial order being modified, either the main one or a block order
        :type tOrd: list
        :param flowSpace: The shape that makes up the flow UI, which varies from typical usage to block construction
        :type flowSpace: visual.Rect object
        :param UI: A dictionary containing the currently active UI
        :type UI: dict
        :param flow: A dictionary containing the currently active trial flow
        :type flow: dict
        :param types: A dictionary containing the currently active trial pallette (mostly for showMainUI)
        :type types: dict
        :return: The modified trial order
        :rtype: list
        """

        # Display a text tooltip at the top of the flow area. Not sensitive to size of flow area because bluntly it looked better to lock it to the default size
        instrText = visual.TextStim(self.win, text="Click another trial to swap positions, click a trial type to replace, or click the remove button to delete from the study flow, click anywhere else to cancel.", bold=True,
                    height=abs(self.flowArea[3]-self.flowArea[2])*.04, pos=[-.2, flowSpace[2]-.05*float(abs(flowSpace[3]-flowSpace[2]))], alignHoriz='center', alignVert='center')
        #highlight the selected object.
        removeTrialShape = visual.Rect(self.win, fillColor='red', width=.1*float(abs(self.flowArea[1]-self.flowArea[0])), height=.1*float(abs(self.flowArea[3]-self.flowArea[2])),
                    pos=[flowSpace[0]+float(abs(flowSpace[1]-flowSpace[0]))*.85,flowSpace[3]+float(abs(flowSpace[3]-flowSpace[2]))/9])
        removeTrialText = visual.TextStim(self.win, text="REMOVE", bold=True, height=removeTrialShape.height*.5,pos=removeTrialShape.pos)
        flow['shapes'][flowIndex].lineColor = "yellow"
        flow['shapes'][flowIndex].lineWidth = 5
        core.wait(.1) #Short delay to clear any old mouse press.
        #loop until mouse press
        while 1 not in self.mouse.getPressed():
            self.showMainUI(UI, flow, types)
            instrText.draw()
            removeTrialShape.draw()
            removeTrialText.draw()
            self.win.flip()
        for i in range(0, len(flow['shapes'])):
            if self.mouse.isPressedIn(flow['shapes'][i]) and not i == flowIndex:
                # Clicked a different thing in the study flow
                # Swap the selected trial and the clicked trial, reload study flow.
                tempTrial = deepcopy(tOrd[i])
                tOrd[i] = tOrd[flowIndex]
                tOrd[flowIndex] = tempTrial
        for j in range(0, len(types['shapes'])):
            # Clicked a different trial type from the palette, swapping it with the current trial
            if self.mouse.isPressedIn(types['shapes'][j]) and types['labels'][j] != tOrd[flowIndex]:
                tOrd[flowIndex] = types['labels'][j]
        if self.mouse.isPressedIn(removeTrialShape):
            # Pop that trial out of trial order
            del tOrd[flowIndex]
        else:
            flow['shapes'][flowIndex].lineColor="white"
            flow['shapes'][flowIndex].lineWidth=1.5
        core.wait(.1)
        return tOrd

    
    def loadFlow(self, tOrd, space, locs, overflow, specNumItems=0):
        """
        Creates the array of objects to be drawn for a study flow or block flow.

        Flow dictionary components:
        'lines': Lines that go between items in the flow, drawn first
        'shapes': visual.Rect objects
        'text': visual.textStim objects
        'labels': Strings that label each trial. Shapes and text are indexted to these, so you can do easy lookup.
        'extras': Special category for trial pips for blocks.

        :param tOrd: Extant order of trials, either the overall trial order or the block order
        :type tOrd: list
        :param space: The dimensions of the flow part of the UI, typically self.flowArea
        :type space: list
        :param locs: List of locations to draw the items in the flow, if less than 21 items to be drawn
        :type locs: list
        :param overflow: List of locations to use when there are more than 21 items, which compacts the rendering.
        :type overflow: list
        :param specNumItems: A special argument for cases where there are weird line overlaps that change the length of things. Defaults to 0, only used when calling recursively.
        :type specNumItems: int
        :return: A dictionary of all of the entities to draw into the block or study flow
        :rtype: dict
        """

        numItems = len(tOrd)
        tTypes = self.settings['trialTypes']
        for i in range(0,len(tOrd)):
            if tOrd[i] == 'Hab':
                numItems += 1 #Double-size for blocks
        outputDict = {'lines':[],'shapes':[],'text':[],'labels':[], 'extras':[]}  #Labels allows us to index the others while still keeping order.
        j = 0 # This serves a purpose, trust me. It's for rendering hab blocks.
        if specNumItems > 0:
            numItems = specNumItems  # Currently this deals with the edge of edge cases, a hab in position 20 looping into the second line.
        if numItems < 21:  # Past 20 we can't render it, but it won't crash.
            flowSpace = locs
        else:
            flowSpace = overflow
        for i in range(0, len(tOrd)):
            #Now, actually build the list of objects to render.
            if j < 39 or (j == 39 and numItems == 40):
                c = tTypes.index(tOrd[i])  # find the trial type, get color index
                if tOrd[i] == 'Hab': # The special category
                    if j % 10 == 9:
                        j += 1 # Just in case we're at the point where it would loop around to the second row. We don't want that.
                        if numItems == 20 or numItems == 39:  # Special case of breaking flowLocs limits.
                            #TODO: BF: if there are multiple hab blocks or if there are precisely 41 items when you have a line skip like this it doesn't count them correctly in the study flow interface.
                            #But, having more than one hab block breaks the whole program anyways. Will become an issue with generic blocks
                            return self.loadFlow(tOrd, space, locs, overflow, specNumItems=numItems+1)
                    lx1 = flowSpace[j][0]
                    j += 1
                    lx2 = flowSpace[j][0]
                    lx = (lx2+lx1)/2 # Ideally putting it square in between the two places.
                    loc = [lx,flowSpace[j][1]]
                    tempObj = visual.Rect(self.win,width=self.flowWidthObj*2, height=self.flowHeightObj, fillColor=self.colorsArray[c], pos=loc)
                    if tOrd[i] == 'Hab' and len(self.settings['habTrialList']) > 1:  # If there are hab sub-trials, add pips to the hab block object
                        for q in range(0, len(self.settings['habTrialList'])):
                            tempStr = self.settings['habTrialList'][q]
                            newwidth = self.flowWidthObj/len(self.settings['habTrialList'])
                            tempPip = visual.Rect(self.win, width=newwidth, height=self.flowHeightObj/2.5,
                                                  fillColor=self.colorsArray[tTypes.index(tempStr)],
                                                  pos=[lx+newwidth*(q-(len(self.settings['habTrialList'])-1)/2), flowSpace[j][1]-self.flowHeightObj/2.25])
                            outputDict['extras'].append(tempPip)
                elif tOrd[i] in self.settings['blockList'].keys():
                    tempObj = visual.Rect(self.win, width=self.flowWidthObj, height=self.flowHeightObj, fillColor=self.colorsArray[c], pos=flowSpace[j])
                    for q in range(0, len(self.settings['blockList'][tOrd[i]])):
                        tempStr = self.settings['blockList'][tOrd[i]][q]
                        newwidth = self.flowWidthObj/(2*len(self.settings['blockList'][tOrd[i]]))
                        tempPip = visual.Rect(self.win, width=newwidth, height=self.flowHeightObj / 2.5,
                                              fillColor=self.colorsArray[tTypes.index(tempStr)],
                                              pos=[flowSpace[j][0] + newwidth * (q - (len(self.settings['blockList'][tOrd[i]]) - 1) / 2),
                                                   flowSpace[j][1] - self.flowHeightObj / 2.25])
                        outputDict['extras'].append(tempPip)
                elif tOrd[i] in self.settings['autoAdvance'] and j not in [0, 10, 20, 30]:
                    # Make it adjacent to the last one, unless it would start a row, in which case leave it.
                    loc = [flowSpace[j][0]-abs(space[1]-space[0])*((self.flowGap-self.flowWidMult)/2), flowSpace[j][1]]
                    tempObj = visual.Rect(self.win, width=abs(space[1]-space[0])*(self.flowWidMult + (self.flowGap-self.flowWidMult)), height=self.flowHeightObj, fillColor=self.colorsArray[c], pos=loc)
                else:
                    tempObj = visual.Rect(self.win, width=self.flowWidthObj, height=self.flowHeightObj, fillColor=self.colorsArray[c], pos=flowSpace[j])
                numChar = len(tOrd[i])
                if numChar <= 3:
                    numChar = 4 #Maximum height
                tempTxt = visual.TextStim(self.win, alignHoriz='center', bold=True, alignVert='center',height=self.flowHeightObj/(.48*numChar), text=tOrd[i], pos=tempObj.pos)
                j += 1
                outputDict['shapes'].append(tempObj)
                outputDict['text'].append(tempTxt)
                outputDict['labels'].append(tOrd[i])
        if numItems == 0:
            pass #So we do not add a line if there is no line to draw!
        elif numItems < 11:
            tempLine = visual.Line(self.win, start=locs[0], end=outputDict['shapes'][-1].pos)
            outputDict['lines'].append(tempLine)
        elif numItems < 21:
            tempLine = visual.Line(self.win, start=locs[0], end=locs[9])
            tempLine2 = visual.Line(self.win, start=locs[10], end=outputDict['shapes'][-1].pos)
            outputDict['lines'].append(tempLine)
            outputDict['lines'].append(tempLine2)
        elif numItems < 31:
            tempLine = visual.Line(self.win, start=overflow[0], end=overflow[9])
            tempLine2 = visual.Line(self.win, start=overflow[10], end=overflow[19])
            tempLine3 = visual.Line(self.win, start=overflow[20], end=outputDict['shapes'][-1].pos)
            outputDict['lines'].append(tempLine)
            outputDict['lines'].append(tempLine2)
            outputDict['lines'].append(tempLine3)
        elif numItems < 41:
            tempLine = visual.Line(self.win, start=overflow[0], end=overflow[9])
            tempLine2 = visual.Line(self.win, start=overflow[10], end=overflow[19])
            tempLine3 = visual.Line(self.win, start=overflow[20], end=overflow[29])
            tempLine4 = visual.Line(self.win, start=overflow[30], end=outputDict['shapes'][-1].pos)
            outputDict['lines'].append(tempLine)
            outputDict['lines'].append(tempLine2)
            outputDict['lines'].append(tempLine3)
            outputDict['lines'].append(tempLine4)
        else:
            tempLine = visual.Line(self.win, start=overflow[0], end=self.overFlowLocs[9])
            tempLine2 = visual.Line(self.win, start=overflow[10], end=self.overFlowLocs[19])
            tempLine3 = visual.Line(self.win, start=overflow[20], end=overflow[29])
            tempLine4 = visual.Line(self.win, start=overflow[30], end=outputDict['shapes'][-1].pos)
            outputDict['lines'].append(tempLine)
            outputDict['lines'].append(tempLine2)
            outputDict['lines'].append(tempLine3)
            outputDict['lines'].append(tempLine4)
            tempText = visual.TextStim(self.win, text="+" + str(numItems-39) + " more", pos=overflow[39])
            outputDict['lines'].append(tempText)
        return outputDict

    def nextPalettePage(self):
        """
        Simple function for moving to the next page of the trial type palette.
        :return:
        :rtype:
        """

        if self.trialPalettePage < self.totalPalettePages:
            self.trialPalettePage += 1
        self.trialTypesArray = self.loadTypes(self.typeLocs, self.trialPalettePage)

    def lastPalettePage(self):
        """
        Simple function for moving to the previous page of the trial type palette
        :return:
        :rtype:
        """
        if self.trialPalettePage > 1:
            self.trialPalettePage -= 1
        self.trialTypesArray = self.loadTypes(self.typeLocs, self.trialPalettePage)

    def loadTypes(self, typeLocations, page=1):
        """
        This function creates the trial types palette.

        Type pallette dictionary components:
        'shapes': visual.Rect objects
        'text': visual.TextStim objects
        'labels': A sort of index for the other two, a plain string labeling the trial or block type.

        :param typeLocations: The array of coordinates on which buttons can be placed. Usually self.typeLocs
        :type typeLocations: list
        :return:
        :rtype:
        """
        if len(self.settings['trialTypes']) == 0:  # if working w/ an old settings file or one that for w/e reason has no ttypes.
            tOrd = self.settings['trialOrder']
            tTypes = []#list of trial types
            for i in range(0,len(tOrd)):
                if tOrd[i] not in tTypes:
                    tTypes.append(tOrd[i]) #creating a  list of unique trial types
        else:
            tTypes = self.settings['trialTypes'] 
        outputDict=  {'shapes':[],'text':[],'labels':[]} #Dicts ain't ordered but lists within dicts sure are!
        #Create the same trial type squares we see in the flow, but wholly independent objects for drawing purposes (allowing one to change w/out the other)
        for i in range(0+len(typeLocations)*(page-1), min(len(typeLocations)*page,len(tTypes))):
            #Now, actually build the list of objects to render.
            tempObj = visual.Rect(self.win,width=self.typeWidthObj, height=self.typeHeightObj, fillColor=self.colorsArray[i], pos=typeLocations[i%len(typeLocations)])
            numChar = len(tTypes[i])
            if numChar <= 3:
                numChar = 4 #Maximum height
            tempTxt = visual.TextStim(self.win, alignHoriz='center', alignVert='center',bold=True,height=self.typeHeightObj/(.34*numChar),text=tTypes[i], pos=typeLocations[i%len(typeLocations)])
            outputDict['shapes'].append(tempObj)
            outputDict['text'].append(tempTxt)
            outputDict['labels'].append(tTypes[i])
        x = self.buttonList['functions'].index(self.nextPalettePage)  # TODO: This is inelegant. Find a better fix later.
        self.buttonList['text'][x].text = str(self.trialPalettePage) + '/' + str(self.totalPalettePages)
        return(outputDict)
    
    def quitFunc(self):
        """
        Simple function for quitting, checks if you want to save first (if there's anything to save).

        :return:
        :rtype:
        """
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
            if not self.loadSave and len(self.folderPath)>0: #If this is the first time saving a new experiment, relaunch from launcher!
                self.win.close()
                launcherPath = self.folderPath+self.settings['prefix']+'Launcher.py'
                launcher = coder.ScriptThread(target=self._runLauncher(launcherPath), gui=self)
                launcher.start()
    
    def univSettingsDlg(self): #The universal settings button.
        """
        Settings that apply to every PyHab study regardless of anything else.

        0 = prefix: The prefix of the launcher and all data files.

        1 = blindPres: Level of experimenter blinding, 0 (none), 1 (no trial type info), or
            2 (only info is whether a trial is currently active.

        2 = prefLook: Whether the study is preferential-looking or single-target.

        3 = nextFlash: Whether to have the coder window flash to alert the experimenter they need to manually trigger
            the next trial

        :return:
        :rtype:
        """
        self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)
        self.workingRect.draw()
        self.workingText.draw()
        self.win.flip()
        uDlg = gui.Dlg(title="Universal settings")
        # [default] blindpres, autoadvance, ISI,
        uDlg.addField("Experiment name", self.settings['prefix'])
        ch = []
        if self.settings['blindPres'] == '1' or self.settings['blindPres'] == 1:
            ch=['do not display next trial type','none','only show trial active/inactive']
        elif self.settings['blindPres'] == '2' or self.settings['blindPres'] == 2:
            ch=['show trial active/not active only','none','do not display next trial type']
        else:
            ch=['none','do not display next trial type','show trial active/not active only']
        uDlg.addField("Experimenter blinding:", choices=ch)
        ch2 = []
        if self.settings['prefLook'] in ['1',1]:# so it does not reset everytime you load this dialog.
            ch2 = ["Preferential looking","Single-target"]
        else:
            ch2=["Single-target", "Preferential looking"]
        uDlg.addField("Single-target or preferential looking?",choices=ch2)
        if self.settings['nextFlash'] in ['1',1,'True',True]:
            ch3 = ["Yes","No"]
        else:
            ch3= ["No","Yes"]
        uDlg.addField("Flash to alert experimenter to manually start next trial?", choices=ch3)
        uInfo = uDlg.show()
        if uDlg.OK:
            tryAgain = False
            self.settings['prefix'] = uInfo[0]
            if uInfo[1] == 'none':
                self.settings['blindPres'] = 0
            elif uInfo[1] == 'do not display next trial type':
                self.settings['blindPres'] = 1
            else:
                self.settings['blindPres'] = 2
            if uInfo[2] == "Preferential looking" and self.settings['prefLook'] in [0,'0','False',False]: #specifically switching, reactivate all data cols.
                self.settings['prefLook'] = 1
                self.settings['dataColumns'] = self.allDataColumnsPL
            elif uInfo[2] == "Single-target" and self.settings['prefLook'] in [1,'1','True',True]:
                self.settings['prefLook'] = 0
                self.settings['dataColumns'] = self.allDataColumns
            if uInfo[3] == "Yes":
                self.settings['nextFlash'] = 1
            else:
                self.settings['nextFlash'] = 0
            if tryAgain:
                self.univSettingsDlg()
        
    def dataSettingsDlg(self):
        """
        Which columns of data are recorded.
        Resets if the experiment type is switched to or from preferential looking.

        :return:
        :rtype:
        """
        self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)
        self.workingRect.draw()
        self.workingText.draw()
        self.win.flip()
        dDlg = gui.Dlg(title="Data settings")
        dDlg.addText("Select which summary files to save.")
        dDlg.addText("Block-level means one line per block instance (e.g., each loop of a hab block),")
        dDlg.addText("trial-level means one line for each individual trial (the verbose file will always have this)")
        dDlg.addField("Block-level", initial=True)
        dDlg.addField("Trial-level", initial=True)
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
            for j in range(0, len(datInfo)):
                if datInfo[j]:
                    tempCols.append(tempDataCols[j])
            self.settings['dataColumns'] = tempCols
        
    def stimSettingsDlg(self, lastSet=[], redo=False):
        """

        Settings relating to stimulus presentation. Indexes from the dialog

        0 = screenWidth: Width of stim window

        1 = screenHeight: Height of stim window

        2 = Background color of stim window

        3 = movieWidth: Width of movieStim3 object inside stim window. Future: Allows for movie default resolution?

        4 = movieWidth: Height of movieStim3 object inside stim window

        5 = freezeFrame: If the attention-getter is used (for a given trial type), this is the minimum time the first frame
        of the movie will be displayed after the attention-getter finishes.

        6 = screenIndex: Which screen to display the stim window on.

        7 = expScreenIndex: Which screen to display the experimenter window on



        :param lastSet: Optional. Last entered settings, in case dialog needs to be presented again to fix bad entries.
        :type lastSet: list
        :param redo: Are we doing this again to fix bad entries?
        :type redo: boolean
        :return:
        :rtype:
        """

        self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)
        self.workingRect.draw()
        self.workingText.draw()
        self.win.flip()

        sDlg = gui.Dlg(title="Stimulus presentation settings")
        if not redo:
            lastSet=[]
            # This order maps on to the order of the dialog box. This allows for carrying over from previous entries
            # if there's a problem (e.g., text where numbers should be). Done as separate lines basically for ease of
            # correspondence to the field definitions and the saving at the end.
            lastSet.append(self.settings['screenWidth'])
            lastSet.append(self.settings['screenHeight'])
            lastSet.append(self.settings['screenColor'])
            lastSet.append(self.settings['movieWidth'])
            lastSet.append(self.settings['movieHeight'])
            lastSet.append(self.settings['freezeFrame'])
            lastSet.append(self.settings['screenIndex'])
            lastSet.append(self.settings['expScreenIndex'])
        colors = ['black', 'white', 'gray']
        colorchz = [x for x in colors if x != lastSet[2]]
        colorchz.insert(0, lastSet[2])
        sDlg.addField("Stimulus display width in pixels", lastSet[0])
        sDlg.addField("Stimulus display height in pixels", lastSet[1])
        sDlg.addField("Stimulus display background color", choices=colorchz)
        sDlg.addField("Width of movie stimuli in pixels", lastSet[3])
        sDlg.addField("Height of movie stimuli in pixels", lastSet[4])
        sDlg.addField("Freeze first frame for how many seconds after attention-getter?", lastSet[5])
        # Get a list of all screens. Requires us to import pyglet, assuming we are using pyglet displays (until glfw works)
        defDisp = pyglet.window.get_platform().get_default_display()
        allScrs = defDisp.get_screens()
        if len(allScrs) > 1:
            screenList = list(range(0, len(allScrs)))
        else:
            screenList = [0, 1]  # Because even if you don't have a second screen now, you presumably will later.
        if isinstance(lastSet[6],str):
            lastSet[6] = eval(lastSet[6])
        scrchz = [x for x in screenList if x != lastSet[6]]
        scrchz.insert(0, lastSet[6])
        sDlg.addField("Screen index of presentation window (0 = primary display, 1-N = secondary screens)", choices=scrchz)
        escrchz = [x for x in screenList if x != lastSet[7]]
        escrchz.insert(0, lastSet[7])
        sDlg.addField("Screen index of experimenter window", choices=escrchz)

        stimfo = sDlg.show()
        if sDlg.OK:
            problem = False
            for i in [0, 1, 3, 4, 5, 6, 7]:
                if not isinstance(stimfo[i], float) and not isinstance(stimfo[i], int):
                    try:
                        stimfo[i] = eval(stimfo[i])
                    except:
                        problem = True
            if not problem:
                self.settings['screenWidth'] = stimfo[0]
                self.settings['screenHeight'] = stimfo[1]
                self.settings['screenColor'] = stimfo[2]
                self.settings['movieWidth'] = stimfo[3]
                self.settings['movieHeight'] = stimfo[4]
                self.settings['freezeFrame'] = stimfo[5]
                self.settings['screenIndex'] = stimfo[6]
                self.settings['expScreenIndex'] = stimfo[7]
            else:
                warnDlg = gui.Dlg(title="Warning!")
                warnDlg.addText(
                    "Number expected, got text instead. \nPlease make sure window height/width, movie height/width, and freeze-frame duration are all numbers!")
                warnDlg.show()
                self.stimSettingsDlg(stimfo, redo=True)



    def addStimToLibraryDlg(self):
        """
        A series of dialog boxes which allows you to build a "library" of stimulus files for your experiment, which you
        can then assign to trial types in a separate dialog.

        Works a bit like the attention-getter construction dialogs, but different in that it allows audio or images alone.
        The image/audio pairs are complicated, but not worth splitting into their own function at this time.

        :return:
        :rtype:
        """
        add = 1
        if len(self.settings['stimList'].keys())>0:
            sDlg0 = gui.Dlg(title="Add/remove stimuli")
            sDlg0.addField("Add or remove stimuli?", choices=['Add','Remove'])
            sd0 = sDlg0.show()
            if sDlg0.OK and sd0[0] == 'Remove':
                add = -1
            elif sDlg0.OK:
                add = 1
            else:
                add = 0
        if add == 1:
            cz = ['Movie', 'Image', 'Audio', 'Image with audio']
            sDlg1 = gui.Dlg(title="Add stimuli to library, step 1")
            sDlg1.addField("What kind of stimuli would you like to add? (Please add each type separately)", choices=cz)
            sDlg1.addField("How many? (For image with audio, how many pairs?) You will select them one at a time.", 1)
            sd1 = sDlg1.show()
            allowedStrings = {'Audio': "Audio (*.aac, *.aiff, *.flac, *.m4a, *.mp3, *.ogg, *.raw, *.wav, *.m4b, *.m4p)",
                              'Movie': "Movies (*.mov, *.avi, *.ogv, *.mkv, *.mp4, *.mpeg, *.mpe, *.mpg, *.dv, *.wmv, *.3gp)",
                              'Image': "Images (*.jpg, *.jpeg, *.png, *.gif, *.bmp, *.tif, *.tiff)"}
            if sDlg1.OK and isinstance(sd1[1],int):
                stType = sd1[0]  # Type of stimuli (from drop-down).
                stNum = sd1[1]  # Number to add.
                NoneType = type(None)
                if stType != 'Image with audio':  # Image w/ audio is complicated, so we will take care of that separately.
                    for i in range(0, stNum):
                        stimDlg = gui.fileOpenDlg(prompt="Select stimulus file (only one!)")
                        if type(stimDlg) is not NoneType:
                            fileName = os.path.split(stimDlg[0])[1] # Gets the file name in isolation.
                            self.stimSource[fileName] = stimDlg[0]  # Creates a "Find this file" path for the save function.
                            self.settings['stimList'][fileName] = {'stimType': stType, 'stimLoc': stimDlg[0]}
                else:  # Creating image/audio pairs is more complicated.
                    for i in range(0, stNum):
                        stimDlg1 = gui.Dlg(title="Pair number " + str(i+1))
                        stimDlg1.addField("Unique name for this stimulus pair (you will use this to add it to trials later)", 'pairName')
                        stimDlg1.addText("Click OK to select the AUDIO file for this pair")
                        sd2 = stimDlg1.show()
                        if stimDlg1.OK:
                            a = True
                            if sd2[0] in list(self.settings['stimList'].keys()):  # If the pair name exists already
                                a = False
                                errDlg = gui.Dlg("Change existing pair?")
                                errDlg.addText("Warning: Pair name already in use! Press OK to overwrite existing pair, or cancel to skip to next pair.")
                                ea = errDlg.show()
                                if errDlg.OK:
                                    a = True
                            if a:
                                stimDlg = gui.fileOpenDlg(prompt="Select AUDIO file (only one!)")
                                if type(stimDlg) is not NoneType:
                                    fileName = os.path.split(stimDlg[0])[1] # Gets the file name in isolation.
                                    self.stimSource[fileName] = stimDlg[0]  # Creates a "Find this file" path for the save function.
                                    self.settings['stimList'][sd2[0]] = {'stimType': stType, 'audioLoc': stimDlg[0]}
                                    tempDlg = gui.Dlg(title="Now select image")
                                    tempDlg.addText("Now, select the IMAGE file for this pair (cancel to erase audio and skip pair)")
                                    t = tempDlg.show()
                                    if tempDlg.OK:
                                        stimDlg2 = gui.fileOpenDlg(prompt="Select IMAGE file (only one!)")
                                        if type(stimDlg2) is not NoneType:
                                            fileName2 = os.path.split(stimDlg2[0])[1] # Gets the file name in isolation.
                                            self.stimSource[fileName2] = stimDlg2[0]
                                            self.settings['stimList'][sd2[0]].update({'imageLoc': stimDlg2[0]})
                                    else:
                                        del self.settings['stimList'][sd2[0]]

            elif sDlg1.OK:
                errDlg = gui.Dlg(title="Warning, invalid value!")
                errDlg.addText("Number of files to add was not a whole number! Please try again.")
                e = errDlg.show()
            # When we are done with this dialog, if we have actually added anything, create the "add to types" dlg.
            if len(list(self.settings['stimList'].keys())) > 0 and self.addStimToTypesDlg not in self.buttonList['functions']:
                addMovButton = visual.Rect(self.win, width=.3, height=.5 * (.2 / self.aspect), pos=[.4, -.65],
                                           fillColor="white")
                addMovText = visual.TextStim(self.win, text="Add stimulus files \nto trial types", color="black",
                                             height=addMovButton.height * .3, alignHoriz='center', pos=addMovButton.pos)
                self.buttonList['shapes'].append(addMovButton)
                self.buttonList['text'].append(addMovText)
                self.buttonList['functions'].append(self.addStimToTypesDlg)

        elif add == -1: # Remove stimuli from library
            self.removeStimFromLibrary()

    def removeStimFromLibrary(self):
        """
        Presents a dialog listing every item of stimuli in the study library. Allows you to remove any number at once,
        removes from all trial types at same time. Deletes from stimuli folder on save if extant.


        :return:
        :rtype:
        """

        #Use self.folderpath to see if there's an extant save that needs to be updated.

        remDlg = gui.Dlg("Remove stimuli from library")
        orderList = []
        remDlg.addText("Uncheck any stimuli you want to remove. NOTE: This will remove stimuli from trial types as well.")
        for i in self.settings['stimList'].keys():
            remDlg.addField(i, initial=True)
            orderList.append(i) # Neccessary because dicts are un-ordered.

        remList=remDlg.show()

        if remDlg.OK:
            for j in range(0,len(remList)):
                if not remList[j]:
                    toRemove = orderList[j]
                    #Things to remove it from: stimlist, stimsource, stimNames(if assigned to trial types). Doesn't apply to attngetter, has its own system.
                    if self.settings['stimList'][toRemove]['stimType'] != 'Image with audio':
                        self.delList.append(toRemove)
                        if toRemove in self.stimSource.keys():
                            try:
                                del self.stimSource[toRemove]
                            except:
                                print("Could not remove from stimSource!")
                    else:
                        #If it's an image/audio pair, need to append both files.
                        tempAname = os.path.split(self.settings['stimList'][toRemove]['audioLoc'])[1]
                        tempIname = os.path.split(self.settings['stimList'][toRemove]['imageLoc'])[1]
                        self.delList.append(tempAname)
                        self.delList.append(tempIname)
                        if tempAname in self.stimSource.keys():
                            try:
                                del self.stimSource[tempAname]
                                del self.stimSource[tempIname]
                            except:
                                print("Could not remove from stimSource!")

                    try:
                        del self.settings['stimList'][toRemove]
                    except:
                        print("Could not remove from stimList!")
                    for q in self.settings['stimNames'].keys(): # Remove from trial types it has been assigned to.
                        self.settings['stimNames'][q] = [x for x in self.settings['stimNames'][q] if x != toRemove]





    def addStimToTypesDlg(self):
        """
        A series dialog boxes, the first selecting a trial type and the number of stimuli to add to it,
        a second allowing you to add stimuli from the stimulus library that is stimList in the settings.
        Also used for adding beginning and end of experiment images (?)

        :return:
        :rtype:
        """
        self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)
        self.workingRect.draw()
        self.workingText.draw()
        self.win.flip()

        if len(self.trialTypesArray['labels']) > 0:
            d1 = gui.Dlg(title="Select trial type to add stimuli to")
            choiceList = []
            for i in range(0, len(self.trialTypesArray['labels'])): # Not just copying list b/c it would add start/end to it
                if self.trialTypesArray['labels'][i] in self.settings['blockList'].keys():
                    pass
                elif self.trialTypesArray['labels'][i] == 'Hab' and len(self.settings['habTrialList'])>0:
                    pass
                else:
                    choiceList.append(self.trialTypesArray['labels'][i])
            choiceList.append('Start and end of experiment screens')
            d1.addField("Trial type to add stimulus file to", choices=choiceList)
            d1.addField("Number of stimuli to add (you will select them in the next window)",1)
            d1.addText("Note: You can only select stimuli you have already added to the experiment library")
            d1.addText("Note: You can only REMOVE stimuli from a trial type in the trial type's own settings, this will add to whatever is already there")
            d = d1.show()
            if d1.OK and isinstance(d[1], int):
                self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)
                self.workingRect.draw()
                self.workingText.draw()
                self.win.flip()
                tType = d[0]
                numAdd = d[1]
                if tType != 'Start and end of experiment screens':
                    d2 = gui.Dlg(title="Select stimuli")
                    stimKeyList = list(self.settings['stimList'].keys())
                    stimKeyList.sort()
                    for i in range(0, numAdd):
                        d2.addField("Stimulus no. " + str(i+1), choices=stimKeyList)
                    newList = d2.show()
                    if d2.OK:
                        for z in range(0, len(newList)):
                            self.settings['stimNames'][tType].append(newList[z])
                else:
                    d2 = gui.Dlg(title="Select image")
                    # Create a list of just image stim
                    startimgs = [x for x in list(self.settings['stimList'].keys()) if self.settings['stimList'][x]['stimType'] == 'Image']
                    startimgs.sort()
                    startimgs.insert(0,'None')
                    if self.settings['startImage'] != '':
                        startimgs = [x for x in startimgs if x != self.settings['startImage']]
                        startimgs.insert(0,self.settings['startImage'])
                    endimgs = [x for x in list(self.settings['stimList'].keys()) if self.settings['stimList'][x]['stimType'] == 'Image']
                    endimgs.sort()
                    endimgs.insert(0,'None')
                    if self.settings['endImage'] != '':
                        endimgs = [x for x in endimgs if x != self.settings['endImage']]
                        endimgs.insert(0, self.settings['endImage'])
                    d2.addField("Start of experiment image", choices=startimgs)
                    d2.addField("End of experiment image", choices=endimgs)

                    newList = d2.show()
                    if d2.OK:
                        if newList[0] is not 'None':
                            self.settings['startImage'] = newList[0]
                        else:
                            self.settings['startImage'] = ''
                        if newList[1] is not 'None':
                            self.settings['endImage'] = newList[1]
                        else:
                            self.settings['endImage'] = ''
            elif d1.OK:
                errDlg = gui.Dlg(title="Warning, invalid value!")
                errDlg.addText("Number of stimuli to add was not a whole number! Please try again.")
                e = errDlg.show()
        else:
            errDlg = gui.Dlg(title="No trial types!")
            errDlg.addText("No trial types to add movies to! Please create trial types first.")
            e = errDlg.show()


    def attnGetterAudioDlg(self):
        """
        A modular dialog for setting the options for an audio-based attention-getter

        :return: A dictionary containing all the info required for an audio attention-getter
        :rtype: dict
        """
        NoneType = type(None)
        aDlg3 = gui.Dlg(title="Audio attention-getter settings")
        aDlg3.addField("Looming shape type", choices=['Rectangle', 'Cross', 'Star'])
        aDlg3.addField("Looming shape color", choices=['yellow', 'green', 'red', 'blue', 'white', 'black'])
        ans3 = aDlg3.show()
        if aDlg3.OK:
            shape = ans3[0].split()  # Pulls out rectangle, cross, or star.
            fileSelectDlg = gui.fileOpenDlg(prompt="Select attention-getter audio file")
            if type(fileSelectDlg) is not NoneType:
                path, namething = os.path.split(fileSelectDlg[0])
                # Again an ugly but necessary solution for getting the duration.
                tempSound = sound.Sound(fileSelectDlg[0])
                tempGetter = {'stimLoc': fileSelectDlg[0], 'stimName': namething,
                                   'shape': shape[-1], 'color': ans3[1],
                                   'stimDur': tempSound.getDuration()}
                del tempSound
                return tempGetter
            else:
                return {}
        else:
            return {}

    def attnGetterVideoDlg(self):
        """
        A modular dialog for setting the options for a video-based attention-getter

        :return: A dictionary containing all the info required for a video attention-getter
        :rtype: dict
        """
        NoneType = type(None)
        fileSelectDlg = gui.fileOpenDlg(prompt="Select attention-getter movie file")
        if type(fileSelectDlg) is not NoneType:
            path, namething = os.path.split(fileSelectDlg[0])
            # Suboptimal solution for getting duration, but possibly only available.
            tempMovie = visual.MovieStim3(self.win, fileSelectDlg[0])
            tempGetter = {'stimLoc': fileSelectDlg[0], 'stimName': namething,
                               'stimDur': tempMovie.duration}
            del tempMovie
            return tempGetter
        else:
            return {}

    def attnGetterMovieAudioDlg(self):
        """
        A modular dialog for finding an audio file and a video file and titling them appropriately.

        :return: A dictionary containing all the info required for a video/audio attngetter.
        :rtype:
        """
        initialDlg = gui.Dlg("Instructions")
        initialDlg.addText("First select movie file, then select audio file.")
        iShow = initialDlg.show()
        if not initialDlg.OK:
            return {}
        NoneType = type(None)
        fileSelectDlg = gui.fileOpenDlg(prompt="Select attention-getter MOVIE file")
        if type(fileSelectDlg) is not NoneType:
            path, namething = os.path.split(fileSelectDlg[0])
            # Suboptimal solution for getting duration, but possibly only available.
            tempMovie = visual.MovieStim3(self.win, fileSelectDlg[0])
            tempDuration = tempMovie.duration
            soundSelectDlg = gui.fileOpenDlg(prompt="Select attention-getter AUDIO file")
            if type(soundSelectDlg) is not NoneType:
                apath, aname = os.path.split(soundSelectDlg[0])
                tempGetter = {'stimLoc': fileSelectDlg[0], 'stimName': namething, 'audioLoc': soundSelectDlg[0],
                              'audioName': aname, 'stimDur': tempDuration}
                del tempMovie
                return tempGetter
            else:
                del tempMovie
                return {}
        else:
            return {}


    def attnGetterDlg(self):
        """
        The dialog window for customizing the attention-getters available to use for different trials.
        Two-stage: Modify existing attngetter or make new, then what do you do with ether of those.
        Allows audio with PsychoPy-produced looming shape or just a video file.

        :return:
        :rtype:
        """
        self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)
        self.workingRect.draw()
        self.workingText.draw()
        self.win.flip()
        achz = list(self.settings['attnGetterList'].keys())
        # Remove default (which cannot be messed with).
        achz = [a for a in achz if a is not 'PyHabDefault']
        achz.insert(0, 'Make New')  # Top item will always be "make new"
        aDlg1 = gui.Dlg(title="Select attention-getter or make new")
        aDlg1.addField("Select attention-getter or 'Make New'", choices=achz)
        ans1 = aDlg1.show()
        NoneType = type(None)
        if aDlg1.OK:
            if ans1[0] is 'Make New':
                # New window to design an attention getter! Choose your own adventure a bit.
                aDlg2 = gui.Dlg(title="Make new attention-getter: step 1")
                aDlg2.addField("Attention-getter name: ", 'NewAttnGetter')
                aDlg2.addField("Audio (with built-in shape) or movie, or silent movie with sep. audio track?", choices=['Audio','Movie','Movie + Audio'])
                ans2 = aDlg2.show()
                if aDlg2.OK:
                    tempGetter={'stimType': ans2[1]}
                    if tempGetter['stimType'] is 'Movie':
                        newTempGet = self.attnGetterVideoDlg()
                    elif tempGetter['stimType'] is 'Audio':
                        newTempGet = self.attnGetterAudioDlg()
                    else:
                        newTempGet = self.attnGetterMovieAudioDlg()
                    if len(newTempGet) > 0:
                        tempGetter.update(newTempGet)
                        self.settings['attnGetterList'][ans2[0]] = tempGetter

            else: # Modifying an existing AG. Little complex.
                aDlg2b = gui.Dlg(title="Change attention-getter properties")
                currAG = self.settings['attnGetterList'][ans1[0]] #The current attention-getter.
                aDlg2b.addField("Attention-getter name: ", ans1[0])
                if currAG['stimType'] is 'Audio':
                    chz = ['Audio', 'Movie', 'Movie + Audio']
                elif currAG['stimType'] is 'Movie':
                    chz = ['Movie', 'Audio', 'Movie + Audio']
                else:
                    chz = ['Movie + Audio', 'Movie', 'Audio']
                aDlg2b.addField("Attention-getter type: ", choices=chz)
                aDlg2b.addField("Change current file (%s)?" % currAG['stimName'], choices=["No","Yes"])
                if currAG['stimType'] is 'Movie + Audio':
                    aDlg2b.addField("Change audio file (%s)?" % currAG['audioName'], choices=["No","Yes"])
                elif currAG['stimType'] is 'Audio':
                    allShapes = ['Rectangle','Cross','Star']
                    shapeChz = [x for x in allShapes if x is not currAG['shape']]
                    shapeChz.insert(0, currAG['shape'])
                    aDlg2b.addField("Looming shape type", choices=shapeChz)
                    allColors = ['yellow', 'green', 'red', 'blue', 'white', 'black']
                    colorChz = [x for x in allColors if x is not currAG['color']]
                    colorChz.insert(0, currAG['color']) # A more elegant shuffle because the words match
                    aDlg2b.addField("Looming shape color", choices=colorChz)
                ans2b = aDlg2b.show()
                if aDlg2b.OK:
                    if ans2b[0] is not ans1[0]:  # Did they change the name?
                        self.settings['attnGetterList'][ans2b[0]] = self.settings['attnGetterList'].pop(ans1[0])
                        currAG = self.settings['attnGetterList'][ans2b[0]]
                        for i, j in self.settings['playAttnGetter'].items():
                            if j == ans1[0]:
                                self.settings['playAttnGetter'][i] = ans2b[0]
                    if ans2b[1] is not currAG['stimType']:  # if they change it from audio to video or the reverse...
                        tempGetter = {'stimType': ans2b[1]}
                        # 1. If going to audio, select shape then new file.
                        if currAG['stimType'] is 'Movie':
                            newTempGet = self.attnGetterAudioDlg()
                        elif currAG['stimType'] is 'Audio':
                            newTempGet = self.attnGetterVideoDlg()
                        else:
                            newTempGet = self.attnGetterMovieAudioDlg()
                        if len(newTempGet) > 0:
                            tempGetter.update(newTempGet)
                            self.settings['attnGetterList'][ans2b[0]] = tempGetter # Overwrite existing.
                    else:
                        if ans2b[2] is "Yes":  # Same stim type, change file. Ignore shape settings for now
                            fileSelectDlg = gui.fileOpenDlg(prompt="Select attention-getter file")
                            if type(fileSelectDlg) is not NoneType:
                                path, namething = os.path.split(fileSelectDlg[0])
                                if ans2b[1] is 'Audio':
                                    tempStim = sound.Sound(fileSelectDlg[0])
                                else:
                                    tempStim = visual.MovieStim3(self.win, fileSelectDlg[0])
                                self.settings['attnGetterList'][ans2b[0]].update({'stimLoc': fileSelectDlg[0],
                                                                                  'stimName': namething,
                                                                                  'stimDur': tempStim.duration})
                                del tempStim
                        if currAG['stimType'] is 'Movie + Audio' and ans2b[3] is "Yes":
                            self.settings['attnGetterList'][ans2b[0]].update({'audioLoc': fileSelectDlg[0],
                                                                              'audioName': namething})
                    if len(ans2b) > 4:  # If we had shape/color settings
                        self.settings['attnGetterList'][ans2b[0]].update({'shape': ans2b[3], 'color': ans2b[4]})

    def condSettingsDlg(self): #Settings relating to conditions and randomization
        """
        The dialog window for "condition settings", not to be confused with the
        condition interface created by self.condMaker(). This determines whether
        condition randomization is used at all, a separate interface is used to
        define the conditions themselves.

        :return:
        :rtype:
        """
        cDlg = gui.Dlg(title="Conditions settings")
        # Welcome to waterloo. The simple version is just "make a list of conditions and set them after saving".
        # The ideal is that it reads off stimNames (or # movies) and all and lets you specify for each order...
        chkBox = False
        if self.settings['randPres'] in [1,'1',True,'True']:
            chkBox = True
        cDlg.addField("Use random presentation? If yes, a new interface will open",initial=chkBox)
        cDlg.addField("Pre-existing condition file (optional, leave blank to make new file called conditions.csv)", self.settings['condFile'])
        if len(self.baseCondDict) > 0:
            cDlg.addField("Reload base conditions instead of randomized conditions? (WARNING: You will need to re-randomize)", initial=False)
        condInfo = cDlg.show()
        if cDlg.OK:
            self.settings['randPres'] = condInfo[0]
            if condInfo[0]:
                # A new interface that allows you to re-order things
                # Check if there are movies to re-order.
                if len(condInfo) == 3 and condInfo[2] == True:
                    # Reload the 'base' conditions instead of randomized ones.
                    baseConds = True
                else:
                    baseConds = False
                allReady = True
                if len(self.settings['trialTypes']) == 0: # If there are no trial types
                    allReady = False
                for i in range(0,len(self.settings['trialTypes'])):
                    if self.settings['trialTypes'][i] not in self.settings['blockList'].keys(): # If a trial type has no movies associated with it
                        if self.settings['trialTypes'][i] == 'Hab' and len(self.settings['habTrialList']) > 0:
                            pass
                        elif self.settings['trialTypes'][i] not in self.settings['stimNames'].keys():
                            allReady = False
                        elif len(self.settings['stimNames'][self.trialTypesArray['labels'][i]]) == 0:  # Another way that it can have no movies associated with it.
                            allReady = False
                if allReady:
                    if len(condInfo[1]) > 0:
                        self.settings['condFile'] = condInfo[1]
                    else:
                        self.settings['condFile'] = "conditions.csv"
                    if os.name is not 'posix':
                        self.win.winHandle.set_visible(visible=True)
                    if baseConds:
                        self.condMaker(bc=baseConds, resetDict=deepcopy(self.baseCondDict))
                    else:
                        self.condMaker(resetDict=deepcopy(self.condDict))
                else:
                    #Create err dlg.
                    errDlg = gui.Dlg(title="No stimuli!")
                    errDlg.addText("Not all trial types have stimuli!")
                    errDlg.addText("Please add stimuli to all trial types first and then set conditions for randomized presentation.")
                    errDlg.addField("For studies without stimuli, enter list of arbitrary condition labels here, each one in quotes, separated by commas, all inside the square brackets",self.settings['condList'])
                    # This is non-ideal but a reasonable temporary patch.
                    e = errDlg.show()
                    if errDlg.OK:
                        self.settings['condList'] = e[0]
            else:
                self.settings['condFile'] = ''  # Erases one if it existed.
                self.settings['condList'] = []  # Gets rid of existing condition list to save trouble.
                self.condDict = {}  # Gets rid of conditions altogether.

    def condMaker(self, rep=False, currPage=1, bc=False, trialMode=True, resetDict={}):
        """
        A whole separate interface for managing condition creation.

        Outputs settings condList (labels of each condition), condFile (save conditions to this file)
        and makes new structure condDict (mapping of each label to actual condition it applies to)

        :param rep: Basically whether we are recursing while editing conditions
        :type rep: bool
        :param currPage: The current page number
        :type currPage: int
        :param bc: Are we displaying the raw conditions, or the 'base' (pre-randomization) conditions?
        :type bc: bool
        :param trialMode: A toggle between 'trial mode' (use conditions for order of stimuli in trial types) and 'block mode' (use conditions to change order of trials within blocks)
        :type trialMode: bool
        :return:
        :rtype:
        """
        condHeader = visual.TextStim(self.win, text="Conditions", height=.1, bold=True, pos=[-.83,.9])
        divLinesV = [] # Vertical dividing lines (actually very thin rects)
        divLinesH = [] # Horizontal dividing lines
        tTypeHeaders = [] # Heads of each column for trial types.
        condLabels = [] # Labels
        condContent = [] # The content of each condition (a list of dicts).
        drawConds = [] # The text things for drawing.
        numPages = 1
        if bc:
            condPath = self.settings['baseCondFile']
            condDict = self.baseCondDict
            condList = self.settings['baseCondList']
        else:
            condPath = self.settings['condFile']
            condDict = self.condDict
            condList = self.settings['condList']
        if os.path.exists(condPath) and not rep:  # If we already have a pre-existing cond file and aren't in the process of looping.
            testReader=csv.reader(open(condPath, 'rU'))
            testStuff=[]
            for row in testReader:
                testStuff.append(row)
            for i in range(0, len(testStuff)):
                condLabels.append(testStuff[i][0])
                condContent.append(eval(testStuff[i][1]))
            testDict = dict(testStuff) 
            for i in testDict.keys():
                testDict[i]=eval(testDict[i])
            if bc:
                self.baseCondDict = testDict
                condDict = self.baseCondDict
                self.settings['baseCondList'] = condLabels
                numPages = ceil(float(len(self.settings['baseCondList'])) / 4)
            else:
                self.condDict = testDict
                condDict = self.condDict
                self.settings['condList'] = condLabels # Problem: This creates a local copy.
                numPages = ceil(float(len(self.settings['condList'])) / 4)  # use math.ceil to round up.
        elif len(condDict) > 0:  # If we already have something to build on
            numPages = ceil(float(len(condDict.keys()))/4)  # use math.ceil to round up.
            for i in range(0, len(condList)):
                if condList[i] in condDict.keys():
                    condContent.append(condDict[condList[i]])
                else:
                    condContent.append({})
        doneButton = visual.Rect(self.win, width=.2, height=.67*(.15/self.aspect),fillColor="green",pos=[-.87,-.85])
        doneText = visual.TextStim(self.win, text="Done", bold=True, pos=doneButton.pos)
        cancelButton = visual.Rect(self.win, width=.2, height=.67*(.15/self.aspect), fillColor="red", pos=[-.62, -.85])
        cancelText = visual.TextStim(self.win, text="Cancel", bold=True, pos=cancelButton.pos)
        addCondButton = visual.Rect(self.win, width=.25, height=.65*(.15/self.aspect),fillColor="blue",pos=[.82,-.85])
        addCondText = visual.TextStim(self.win, text="Add condition", bold=True, height=addCondButton.height*.3, pos=addCondButton.pos)
        deleteCondButton = visual.Rect(self.win, width=.25, height=.65*(.15/self.aspect),fillColor="red",pos=[.56,-.85])
        deleteCondText = visual.TextStim(self.win, text="Delete condition", bold=True, height=deleteCondButton.height*.3, pos=deleteCondButton.pos)
        blockModeButton = visual.Rect(self.win, width=.25, height=.65*(.15/self.aspect),fillColor="darkorange",pos=[.3,-.85])
        if trialMode:
            txt = 'Block mode'
        else:
            txt = 'Trial mode'
        blockModeText = visual.TextStim(self.win, text=txt, bold=True, height=blockModeButton.height*.3, pos=blockModeButton.pos)
        randomCondsButton = visual.Rect(self.win, width=.25, height=.67*(.15/self.aspect),fillColor="purple",pos=[.04,-.85])
        if len(self.settings['condList']) > 0:
            txt2 = "Randomize\nover subjects"
        else:
            txt2 = "Auto-generate\nconditions"
        randomCondsText = visual.TextStim(self.win, text=txt2, bold=True, height=randomCondsButton.height*.3, pos=randomCondsButton.pos)

        if trialMode:
            typeList = [x for x in self.settings['trialTypes'] if x not in self.settings['blockList'].keys()]
        else:
            typeList = list(self.settings['blockList'].keys())

        instrText = visual.TextStim(self.win, text="Page: " + str(currPage) + "/"+str(numPages), height=.07, pos=[-.3,-.87])
        downArrowVerts = [(0.05,0.3),(-.05,0.3),(-0.05,0.15),(-0.1,0.15),(0,0),(0.1,0.15),(0.05,0.15)]
        nextPageArrow = visual.ShapeStim(self.win, vertices=downArrowVerts, size=.3, lineColor='white', fillColor='white', pos=[-.15,-.92])
        upArrowVerts = [(0.05,-0.3),(-.05,-0.3),(-0.05,-0.15),(-0.1,-0.15),(0,0),(0.1,-0.15),(0.05,-0.15)]
        lastPageArrow = visual.ShapeStim(self.win, vertices=upArrowVerts, size=.3, lineColor='white', fillColor='white', pos=[-.45,-.82])

        intervalHoriz = 1.5/len(typeList)
        intervalVert = 1.5/4  # Locked at this interval because pages of 4 conditions each.
        startH = -.5
        startV = .8
        tempLineH = visual.Line(self.win, start=[-.99,.82], end=[.99,.82]) # End lines slightly shy of the right edge.
        divLinesH.append(tempLineH)
        tempLineV = visual.Rect(self.win, width=.01, height=2, fillColor="white", pos=[-.65,.3])
        divLinesV.append(tempLineV)
        clickRanges=[] # For making it easier ot detect if a line was clicked in. Y only (horizontal doesn't matter)


        for i in range(0,len(typeList)):
            # populate column headers and lines.
            hpos = (i)*intervalHoriz + startH+intervalHoriz/3
            tempText = visual.TextStim(self.win, alignHoriz='center', text=typeList[i],height=(1-startV)*.3, pos=[hpos, .94])
            tTypeHeaders.append(tempText)
            tempLineV = visual.Line(self.win, start=[hpos+intervalHoriz/2,.99], end=[hpos+intervalHoriz/2,-.675])
            divLinesV.append(tempLineV)
        if len(condList) >= 4:
            q = 4
        else:
            q = len(condList)
        for i in range(0, q):
            vpos = startV - (i + 1) * intervalVert + intervalVert / 1.5
            tempLineH = visual.Line(self.win, start=[-.99, vpos - intervalVert / 2], end=[.99, vpos - intervalVert / 2])
            divLinesH.append(tempLineH)

        for j in range(0, len(condList)):  # condition labels. Here's where rubber meets road!
            block = (j+1)%4
            if block == 0:
                block = 4
            vpos = startV - block * intervalVert + intervalVert/1.5
            tempText = visual.TextStim(self.win, text=condList[j], alignHoriz='center',height=intervalVert*.35, pos=[condHeader.pos[0],vpos])
            drawConds.append(tempText)
            # And now, finally, we have to populate each of those conditions.
            for q in range(0,len(typeList)):
                if typeList[q] in condContent[j].keys():
                    txt = condContent[j][typeList[q]]
                else:
                    txt = []
                tempText = visual.TextStim(self.win, text=txt, height=sqrt(intervalVert)*.4*(1/(len(txt)+1))*(sqrt(2)/(sqrt(len(typeList)+1))), wrapWidth=intervalHoriz*.9,pos=[tTypeHeaders[q].pos[0],vpos], alignHoriz='center')
                drawConds.append(tempText)
            tempRange = [vpos+intervalVert/2,vpos-intervalVert/2]
            clickRanges.append(tempRange)
        # Finally the main loop  of this new display.
        done = False
        while 1 in self.mouse.getPressed():
            pass
        while not done:
            instrText.text = "Page: " + str(currPage) + "/" + str(numPages)
            condHeader.draw()
            doneButton.draw()
            doneText.draw()
            cancelButton.draw()
            cancelText.draw()
            addCondButton.draw()
            addCondText.draw()
            deleteCondButton.draw()
            deleteCondText.draw()
            blockModeButton.draw()
            blockModeText.draw()
            randomCondsButton.draw()
            randomCondsText.draw()
            instrText.draw()
            if numPages > 1:
                if currPage < numPages:
                    nextPageArrow.draw()
                if currPage > 1:
                    lastPageArrow.draw()
                while currPage > numPages:
                    currPage = currPage - 1  # BF: Deleting while looking at last page could yield empty page.
            for i in range(0, len(divLinesV)):
                divLinesV[i].draw()
            for j in range(0, len(divLinesH)):
                divLinesH[j].draw()
            for k in range(0, len(tTypeHeaders)):
                tTypeHeaders[k].draw()
            if len(drawConds) <= 4*(len(typeList)+1):  # Each row has one column for each trial type plus one for the label, so rows of n trial types + 1
                for l in range(0, len(drawConds)):
                    drawConds[l].draw()
            else:
                for l in range((currPage-1)*4*(len(typeList)+1), currPage*4*(len(typeList)+1)):
                    if l < len(drawConds):  # Easy safety cutoff for when we can't fill a page, so we don't go out of bounds
                        drawConds[l].draw()
            self.win.flip()
            if 1 in self.mouse.getPressed():
                for i in range((currPage-1)*4, currPage*4):
                    p = self.mouse.getPos()
                    if i < len(clickRanges) and p[1] <= clickRanges[i][0] and p[1] >= clickRanges[i][1]:
                        if os.name is not 'posix':
                            while 1 in self.mouse.getPressed():  # Work on mouseup, impt. for windows.
                                pass
                            self.win.winHandle.set_visible(visible=False)
                        if trialMode:
                            thisDict = self.settings['stimNames']
                        else:
                            thisDict = self.settings['blockList']
                        self.condSetter(thisDict, cond=condList[i],ex=True)
                        if os.name is not 'posix':
                            self.win.winHandle.set_visible(visible=True)
                        while 1 in self.mouse.getPressed():
                            # Making sure that clicking "OK" doesn't immediately trip a click inside the interface
                            pass
                        done = True
                        # Refresh the condition display
                        self.condMaker(rep=True, currPage=currPage, trialMode=trialMode, resetDict=resetDict)
                if self.mouse.isPressedIn(addCondButton):
                    if os.name is not 'posix':
                        while 1 in self.mouse.getPressed():
                            pass
                        self.win.winHandle.set_visible(visible=False)
                    if trialMode:
                        thisDict = self.settings['stimNames']
                    else:
                        thisDict = self.settings['blockList']
                    self.condSetter(thisDict, ex=False)
                    if os.name is not 'posix':
                        self.win.winHandle.set_visible(visible=True)
                    while 1 in self.mouse.getPressed():
                        pass
                    done = True
                    # Start this over...
                    self.condMaker(rep=True, currPage=currPage, bc=bc, trialMode=trialMode, resetDict=resetDict)
                if self.mouse.isPressedIn(blockModeButton):
                    while 1 in self.mouse.getPressed():
                        pass
                    done = True
                    self.condMaker(rep=True, currPage=currPage, bc=bc, trialMode=not trialMode, resetDict=resetDict)
                if self.mouse.isPressedIn(deleteCondButton) and len(condList)>0:
                    if os.name is not 'posix':
                        while 1 in self.mouse.getPressed():
                            pass
                        self.win.winHandle.set_visible(visible=False)
                    self.delCond()
                    if os.name is not 'posix':
                        self.win.winHandle.set_visible(visible=True)
                    while len(self.mouse.getPressed()) < 0:
                        pass
                    done = True
                    # Start this over...
                    self.condMaker(rep=True, currPage=currPage, bc=bc, trialMode=trialMode, resetDict=resetDict)
                if self.mouse.isPressedIn(randomCondsButton) and len(condList)>0:
                    if os.name is not 'posix':
                        while 1 in self.mouse.getPressed():
                            pass
                        self.win.winHandle.set_visible(visible=False)
                    self.condRandomizer()
                    if os.name is not 'posix':
                        self.win.winHandle.set_visible(visible=True)
                    while len(self.mouse.getPressed()) < 0:
                        pass
                    done = True
                elif self.mouse.isPressedIn(randomCondsButton) and len(condList) == 0:
                    if os.name is not 'posix':
                        while 1 in self.mouse.getPressed():
                            pass
                        self.win.winHandle.set_visible(visible=False)
                    self.autoCondSetup()
                    if os.name is not 'posix':
                        self.win.winHandle.set_visible(visible=True)
                    while len(self.mouse.getPressed()) < 0:
                        pass
                    done = True
                    self.condMaker(rep=True, currPage=currPage, bc=bc, trialMode=trialMode, resetDict=resetDict)
                if self.mouse.isPressedIn(nextPageArrow):
                    currPage = currPage + 1
                    if currPage > numPages:
                        currPage = numPages # Safety. Shouldn't be necessary.
                    while 1 in self.mouse.getPressed():
                        pass # so it doesn't jump pages
                if self.mouse.isPressedIn(lastPageArrow):
                    currPage = currPage - 1
                    if currPage < 1:
                        currPage = 1  # Safety. Shouldn't be necessary
                    while 1 in self.mouse.getPressed():
                        pass
                if self.mouse.isPressedIn(doneButton):
                    done = True
                    while 1 in self.mouse.getPressed():
                        pass  # Just to make it not auto-click something on return to the main window
                if self.mouse.isPressedIn(cancelButton):
                    self.condDict = resetDict
                    self.settings['condList']=list(self.condDict.keys()) # Note: Will get scrambled, in all likelihood.
                    done = True
                    while 1 in self.mouse.getPressed():
                        pass  # Just to make it not auto-click something on return to the main window
                
    
    def condSetter(self, shuffleList, cond='NEW', ex=False):
        """
        One dialog per trial type. Each dialog has a list of all the movies in that type
        This is not intuitive under the hood. The output of this is a dict with a list of movies, in order, for each
        trial type. This makes it slightly more human-intelligible than the previous system, which had a list of indexes


        :param shuffleList: Either the stimNames dict or the blockList dict. Defines which one we are modifying.
        :type shuffleList: dict
        :param cond: Condition name
        :type cond: str
        :param ex: Whether the condition already exists
        :type ex: bool
        :return:
        :rtype:
        """
        condDlg2=gui.Dlg(title="Define condition")
        condDlg2.addField("Condition label:", cond)
        condDlg2.addText("You will have separate dialogs to set the order of movies in each trial type. Press OK to begin")
        condDinfo = condDlg2.show()
        if condDlg2.OK:
            condDinfo[0] = str(condDinfo[0])
            if ex and condDinfo[0] != cond:  # Renamed existing condition
                self.settings['condList'][self.settings['condList'].index(cond)] = condDinfo[0] 
                if cond in self.condDict.keys():
                    self.condDict[condDinfo[0]] = self.condDict.pop(cond)
            cond = condDinfo[0]
            outputDict = {}
            i = 0
            labelList = list(shuffleList.keys())
            while i < len(labelList):
                tempType = labelList[i]
                condTyDlg = gui.Dlg(title="Order for " + tempType)
                condTyDlg.addText("Enter order in which you want items to appear. If you do not want an item to appear in this condition, leave blank or put 0.")
                if ex:  # If there is an existing condition that we are modifying.
                    try:
                        movieOrder = self.condDict[cond][tempType]
                        for z in range(0, len(movieOrder)):
                            if type(movieOrder[z]) is int:  # Convert old condition files
                                tempNum = movieOrder[z]
                                movieOrder[z] = shuffleList[tempType][tempNum-1]
                    except:
                        movieOrder = []
                        for k in range(0, len(shuffleList[tempType])):
                            movieOrder.append(shuffleList[tempType][k])  # default order.
                else:
                    movieOrder = []
                    for k in range(0, len(shuffleList[tempType])):
                        movieOrder.append(shuffleList[tempType][k])  # default order.
                movieOrder = deepcopy(movieOrder)
                for x in range(0, len(shuffleList[tempType])):  # Yeah we gotta loop it again.
                    thisMov = shuffleList[tempType][x]
                    if movieOrder.count(thisMov) >= 1:  # If that movie appears in the movie order already.
                        condTyDlg.addField(thisMov, movieOrder.index(thisMov)+1)
                        movieOrder[movieOrder.index(thisMov)] = ''
                    else:
                        condTyDlg.addField(thisMov)
                condTyInfo = condTyDlg.show()
                if condTyDlg.OK:
                    stop = False
                    i += 1
                    # Now we need to reinterpret all that input ot make the output.
                    # First, try converting everything to ints to make sure no foolishness is happening.
                    for x in range(0,len(condTyInfo)):
                        if type(condTyInfo[x]) is str and len(condTyInfo[x]) > 0:  # If they have put something where there was nothing
                            try:
                                condTyInfo[x] = int(condTyInfo[x])
                            except:
                                errDlg = gui.Dlg(title="Warning, invalid input!")
                                errDlg.addText("Non-number entered, please use only numbers or leave blank.")
                                i -= 1  # This is why our for loop became a while loop. So we could go back and fix things.
                                irrel = errDlg.show()
                                stop = True
                    condTyInfo = [0 if type(x) is not int or x <= 0 else x for x in condTyInfo]
                    # Identify any doubles other than 0s, if so error msg and redo
                    maxNum = max(condTyInfo)
                    for q in range(1, maxNum+1):
                        if condTyInfo.count(q) > 1 and not stop:
                            errDlg = gui.Dlg(title="Warning, invalid order!")
                            errDlg.addText("Order has a repeat of the same number. Please re-enter.")
                            i -= 1  # This is why our for loop became a while loop. So we could go back and fix things.
                            irrel = errDlg.show()
                            stop = True
                    if maxNum == 0 and not stop:
                        errDlg = gui.Dlg(title="Warning, invalid order!")
                        errDlg.addText("No stimuli selected. Please re-enter")
                        i -= 1
                        irrel = errDlg.show()
                        stop = True
                    if not stop:
                        # Go through and construct the new trial order.
                        tempOrder = []
                        for q in range(1, maxNum+1):
                            try:
                                tMov = condTyInfo.index(q) # Finds the movie index to add the movie to the order
                                tempOrder.append(shuffleList[tempType][tMov])
                            except ValueError:
                                errDlg = gui.Dlg(title="Warning, invalid order!")
                                errDlg.addText("Non-consecutive numbering (e.g. 1,2,5). Please re-enter with consecutive numbering!")
                                i -= 1
                                irrel = errDlg.show()
                                stop = True
                                break
                    if not stop: # Stops it from accidentally saving bad orders due to non-consecutive numbering.
                        outputDict[tempType] = tempOrder
            # Finally, rewrite everything that needs rewriting.
            # This includes making sure that blocks or trial types, whichever were left blank, are not left blank.
            listAll = list(self.settings['stimNames'].keys()) + list(self.settings['blockList'].keys())
            for q in listAll:
                if q not in outputDict.keys() and not ex:
                    if q in self.settings['blockList'].keys():
                        outputDict[q] = self.settings['blockList'][q]
                    elif q in self.settings['stimNames'].keys():
                        outputDict[q] = self.settings['stimNames'][q]
                elif q not in outputDict.keys():  # Implied: ex == True
                    outputDict[q] = self.condDict[cond][q]
            self.condDict[cond] = outputDict
            if not ex:
                self.settings['condList'].append(str(cond))
        
    def delCond(self):
        """
        Present list of existing conditions. Choose one to remove.
        """
        dCondDlg = gui.Dlg(title="Delete a condition")
        dCondDlg.addField('Choose a condition to delete', choices = self.settings['condList'])
        delCond = dCondDlg.show()
        if dCondDlg.OK:
            self.settings['condList'].remove(str(delCond[0]))
            del self.condDict[delCond[0]]          

    def autoCondSetup(self):
        """
        Function for getting the parameters for automatically generating conditions.
        A series of dialogs. The first one, whatGenDlg, determines whether we are doing stim within trials, trials
        within blocks, or both. It also determines whether we are keeping all items, which shortcuts the second dialog.
        whatGenDlg:
        0 (if blocks): Randomize order of stimuli in trials y/n
        1 (if blocks): Randomize order of trials in blocks y/n
        -1: Keep all items in all conditions y/n

        A second dialog then asks whether there are any trial/block types the user does not want to randomize.

        If not keeping all items in all conditions, another dialog is needed to determine size of subset for each
        trial/block. This produces a dictionary that tracks how many items will be in each condition.
        :return:
        :rtype:
        """
        abort = False
        # First, determine if we are doing autogeneration of random orders for trial types, blocks, or both.
        whatGenDlg = gui.Dlg("Automatic condition generation")
        if len(list(self.settings['blockList'].keys())) > 0:
            whatGenDlg.addText("Select whether to generate counterbalanced orders of stimuli within trial types, of trials within blocks, or both")
            whatGenDlg.addField("Order of stimuli in trials", initial=True)
            whatGenDlg.addField("Order of trials in blocks", initial=True)
        whatGenDlg.addText("Select whether to keep all items in all conditions, or control which items are shown at all by condition")
        whatGenDlg.addField("Keep all items in blocks/trials in all conditions?", initial=True)
        whatGenInfo = whatGenDlg.show()
        if whatGenDlg.OK:
            if len(list(self.settings['blockList'].keys())) > 0:
                trialGen = whatGenInfo[0]
                blockGen = whatGenInfo[1]
            else:
                trialGen = True
                blockGen = False
            if not trialGen and not blockGen:
                abort = True
                errDlg=gui.Dlg("Nothing to randomize!")
                errDlg.addText("Check at least one, trials or blocks, to randomize.")
                errDlg.show()
            keepAll = whatGenInfo[-1]
            counterDict = {}
            # This dict is how we track how many things should be in each condition.
            # Defaults to 'all items assigned to that block/trial'
            if trialGen:
                for i, j in self.settings['stimNames'].items():
                    counterDict[i] = len(j)
            if blockGen:  # This is only true if there are blocks to start with, so no risk of errors
                for k, l in self.settings['blockList'].items():
                    counterDict[k] = len(l)
            # Next step: Give the option to 'lock' some blocks and/or trials so they are constant across conditions
            if not abort:
                lockDlg = gui.Dlg("Select trials/blocks to generate conditions over")
                lockDlg.addText("Any UNCHECKED trial/block will be 'locked' and its order and content will be constant across conditions.")
                lockDlg.addText("Make sure there is a check next to every block/trial you want to vary by condition, then hit OK to generate conditions")
                tempList = list(counterDict.keys())
                for k in tempList:
                    lockDlg.addField(k, initial=True)
                lockInfo = lockDlg.show()
                if lockDlg.OK:
                    if lockInfo.count(True) == 0:
                        abort = True
                        errDlg = gui.Dlg("Error: No trials/blocks selected!")
                        errDlg.addText("Nothing to randomize! Check all trials/blocks to randomize.")
                        errDlg.show()
                    else:
                        for i in range(0, len(tempList)):
                            if not lockInfo[i]:
                                counterDict.pop(tempList[i])  # Remove any 'locked' trials or blocks.
                else:
                    abort = True
            if not keepAll and not abort:
                # Using the trial type palette order we can order this dictionary despite them typically being unordered
                # But first, we need to make sure that we only get the ones that we want.
                tempTypes = [x for x in self.settings['trialTypes'] if x in counterDict.keys()]
                howManyKeep = gui.DlgFromDict(counterDict, title="How many items for each trial/block type per condition?",
                                              order=tempTypes, copyDict=False)
                ctrInfo = howManyKeep.show()
                if not howManyKeep.OK:
                    abort = True
            # Finally, we should have all the information we need to start actually creating conditions.
            if not abort:
                self.autoCond(trialGen,blockGen,counterDict)

    def autoCond(self, genTrials, genBlocks, counters):
        """
        The function that actually creates conditions automatically, given what it is generating conditions for, and how
        many items from each trial/block it should have in each condition.
        Simply sets condDict and condList.

        :param genTrials: Are we generating conditions for movies within trial types?
        :type genTrials: bool
        :param genBlocks: Are we generating conditions for trials within blocks?
        :type genBlocks: bool
        :param counters: A dictionary of each block or trial type that needs to be randomized and the number of items
            that thing should have in each condition
        :type counters: dict
        :return:
        :rtype:
        """

        outputDict = {}
        template = {} # A base template for a condition
        permutates = [] # A list of every possible order of every permuted item.
        mutKeys = []
        for i in counters.keys():
            if i in self.settings['stimNames'].keys():
                template[i] = deepcopy(self.settings['stimNames'][i])
            elif i in self.settings['blockList'].keys():
                template[i] = deepcopy(self.settings['blockList'][i])
        # Python has this beautiful thing called itertools, which can permute automatically.
        for i, j in counters.items():
            permutates.append(list(itertools.permutations(template[i],j)))
            mutKeys.append(i)
            # This creates a list of lists of 'tuples' (which are a lot like lists in most regards). Each item in the
            # sub-list is a permutation with j items from the list of all possible items.
        # Then we just go through permutates and combine THOSE. The 'product' function is a godsend here, but we need
        # to do it to the entire permutation dictionary at once, which must be defined procedurally. Python is amazing.
        outputList = list(itertools.product(*permutates))  # The * makes it take a dynamic list of arguments.
        for i in range(0, len(outputList)):
            outputList[i] = list(outputList[i])
            tmpDict = {}
            for j in range(0, len(outputList[i])):
                outputList[i][j] = list(outputList[i][j])
                tmpDict[mutKeys[j]] = outputList[i][j]
            outputDict[str(i+1)] = tmpDict
        # Once that's done we need to fill in any 'gaps' from things that weren't auto-generated.
        excludes = [x for x in self.settings['trialTypes'] if x not in counters.keys()]
        for i, j in outputDict.items():
            for y in excludes:
                if y in self.settings['blockList'].keys():
                    j[y] = self.settings['blockList'][y]
                elif y in self.settings['stimNames'].keys():
                    j[y] = self.settings['stimNames'][y]

        self.condDict = deepcopy(outputDict)
        self.settings['condList'] = list(outputDict.keys())


    def condRandomizer(self):
        """
        This is based on other scripts I've made. Basically, say you have four conditions, and you want four participants
        to be assigned to each one, but you want to be totally blind to which condition a given participant is in. Here,
        once you have made your four conditions, you can tell it to create a condition list that it never shows you that
        has each condition X times, and that becomes the new condition file/list/etc.

        :return:
        :rtype:
        """

        rCondDlg = gui.Dlg(title="Create randomized condition list")
        rCondDlg.addField('How many repetitions of each condition? (Length of list will be this X # conditions)',1)
        rCondDlg.addField('Condition label prefix? (Will be followed by "01...N" in condition list)', self.settings['prefix'])
        randCond = rCondDlg.show()
        if rCondDlg.OK and isinstance(randCond[0],int):
            totalN = len(self.condDict.keys())*randCond[0]
            # First, save the old, un-randomized thing for later reference.
            self.baseCondDict = deepcopy(self.condDict)
            self.settings['baseCondList'] = deepcopy(self.settings['condList'])
            newCondList = [] # Will replace condlist.
            for i in range (1, totalN+1):
                if i < 10:
                    numStr = "0" + str(i)
                else:
                    numStr = str(i)
                newCondList.append(randCond[1]+numStr)
            listOfConds = [] # A list of the existing conditions that will be the items for the new condDict.
            for j, k in self.condDict.items():
                listOfConds.append(k)
            mixer = [] # The list with all repetitions, which we then shuffle.
            for q in range(0, len(listOfConds)):
                for r in range(0, randCond[0]):
                    mixer.append(listOfConds[q])
            random.shuffle(mixer)

            newCondDict={}
            for s in range(0, len(newCondList)):
                newCondDict[newCondList[s]] = mixer[s]

            self.condDict = newCondDict
            self.settings['condList'] = newCondList
        elif rCondDlg.OK:
            errDlg = gui.Dlg(title="Warning, invalid number!")
            errDlg.addText("Multiplier must be a whole number, no decimals. Please re-open condition settings and try again.")
            errDlg.show()
   
   
    def habSettingsDlg(self, lastSet=[],redo=False): #Habituation criteria
        """
        Dialog for settings relating to habituation criteria:

        0 = maxHabTrials (maximum possible hab trials if criterion not met)

        1 = setCritWindow (# trials summed over when creating criterion)

        2 = setCritDivisor (denominator of criterion calculation . e.g., sum of first 3 trials
            divided by 2 would have 3 for setCritWindow and 2 for this.)

        3 = setCritType (peak window, max trials, first N, or first N above threshold)

        4 = habThresh (threshold for N above threshold)

        5 = metCritWindow (# trials summed over when evaluating whether criterion has been met)

        6 = metCritDivisor (denominator of sum calculated when determining if criterion has been met)

        7 = metCritStatic (static or moving window?)

        8-N = Which trials to calculate hab over for multi-trial blocks. Hab selected by default, populated only if the
        block structure is used

        :param lastSet: If information entered is invalid and the dialog needs to be shown again, this allows it to remember what was previously entered.
        :type lastSet: list
        :param redo: Checking if redoing last setting
        :type redo: boolean
        :return:
        :rtype:
        """
        if not redo:
            lastSet = []
            lastSet.append(self.settings['maxHabTrials'])
            lastSet.append(self.settings['setCritWindow'])
            lastSet.append(self.settings['setCritDivisor'])
            lastSet.append(self.settings['setCritType'])
            lastSet.append(self.settings['habThresh'])
            lastSet.append(self.settings['metCritWindow'])
            lastSet.append(self.settings['metCritDivisor'])
            lastSet.append(self.settings['metCritStatic'])

        hDlg = gui.Dlg(title="Habituation block settings")
        windowtypes = ['First', 'Peak', 'Max', 'Threshold']
        winchz = [x for x in windowtypes if x != lastSet[3]]
        winchz.insert(0, lastSet[3])
        if lastSet[-1] == 'Fixed':
            evalChz = ['Fixed','Moving']
        else:
            evalChz = ['Moving', 'Fixed']

        hDlg.addField("Max number of habituation trials (if criterion not met)", self.settings['maxHabTrials'])
        hDlg.addField("Number of trials to sum looking time over when making hab criterion", self.settings['setCritWindow'])
        hDlg.addField("Number to divide sum of looking time by when computing criterion", self.settings['setCritDivisor'])
        hDlg.addField("Criterion window First trials, first trials above Threshold, dynamic Peak contiguous window, or the set of hab trials with Max looking time?", choices=winchz)
        hDlg.addField("Threshold value to use if 'Threshold' selected above (ignored otherwise)", self.settings['habThresh'])
        hDlg.addField("Number of trials to sum looking time over when determining whether criterion has been met", self.settings['metCritWindow'])
        hDlg.addField("Number to divide sum of looking time by when determining whether criterion has been met", self.settings['metCritDivisor'])
        hDlg.addField("Evaluate criterion over moving window or fixed windows?", choices=evalChz)
        if len(self.settings['habTrialList']) > 0:
            hDlg.addText("Check which trial types criteria should be computed over (both setting and checking)")
            expandedHabList = []
            for q in range(0, len(self.settings['habTrialList'])):
                if self.settings['habTrialList'][q] in self.settings['blockList'].keys():
                    doneBlock = False
                    listThings = []
                    listBlocks = [] # A list of all blocks that need to go into the thing.
                    blockType = self.settings['habTrialList'][q]
                    prfx = blockType + '.'
                    while not doneBlock:
                        for i in self.settings['blockList'][blockType]:
                            if i in self.settings['blockList'].keys():
                                listBlocks.append(i)
                            else:
                                listThings.append(prfx + i)
                        if len(listBlocks) == 0:
                            doneBlock = True
                        else:
                            blockType = listBlocks.pop(0) # Pull out the next block and repeat until empty.
                            prfx = prfx + blockType+'.'
                    for z in range(0,len(listThings)):
                        if listThings[z] in self.settings['calcHabOver']:
                            chk=True
                        else:
                            chk = False
                        hDlg.addField(listThings[z], initial=chk)
                        expandedHabList.append(listThings[z])
                else:
                    if self.settings['habTrialList'][q] == 'Hab' and len(self.settings['calcHabOver']) == 0:
                        chk = True
                    elif self.settings['habTrialList'][q] in self.settings['calcHabOver']:
                        chk = True
                    else:
                        chk = False
                    hDlg.addField(self.settings['habTrialList'][q], initial=chk)
                    expandedHabList.append(self.settings['habTrialList'][q])
        habDat=hDlg.show()
        if hDlg.OK:
            skip = False
            intevals = [0,1,5]
            fevals = [2,4,6] # These can be floats
            for i in intevals:
                if not isinstance(habDat[i], int):
                    if isinstance(habDat[i], str):
                        try:
                            habDat[i]=eval(habDat[i])
                        except:
                            skip = True
                        if not isinstance(habDat[i], int):
                            skip = True
                    else:
                        skip = True
            for i in fevals:
                if not isinstance(habDat[i], float):
                    try:
                        habDat[i]=float(habDat[i])
                    except:
                        skip = True
            lastSet = habDat
            if not skip:
                self.settings['maxHabTrials'] = habDat[0]
                self.settings['setCritWindow'] = habDat[1]
                self.settings['setCritDivisor'] = habDat[2]
                self.settings['setCritType'] = habDat[3]
                self.settings['habThresh'] = habDat[4]
                self.settings['metCritWindow'] = habDat[5]
                self.settings['metCritDivisor'] = habDat[6]
                self.settings['metCritStatic'] = habDat[7]
                if len(self.settings['habTrialList']) > 0:
                    tempArr = []
                    for i in range(0, len(expandedHabList)):
                        if habDat[i+8]:
                           tempArr.append(expandedHabList[i])
                    if len(tempArr) > 0:
                        self.settings['calcHabOver'] = tempArr
                    else:
                        errDlg = gui.Dlg(title="Warning, no trial types selected!")
                        errDlg.addText("You must select at least one trial to calculate habituation over!")
                        errDlg.show()
                        self.habSettingsDlg(habDat, redo=True)
            else:
                errDlg = gui.Dlg(title="Warning, invalid number!")
                errDlg.addText(
                    "Please make sure all values are valid numbers. Remember that any 'number of trials' field must be a whole number (no decimal).")
                errDlg.show()
                self.habSettingsDlg(habDat,redo=True)



    def saveDlg(self):
        """
        Opens a save dialog allowing you to choose where to save your project.
        Essentially sets self.folderPath

        :return:
        :rtype:
        """
        go = True
        if len(self.settings['trialOrder']) == 0:
            warnDlg = gui.Dlg("Warning: No trials in study flow!")
            warnDlg.addText("You haven't added any trials to the study flow yet! You won't be able to run this experiment.")
            warnDlg.addText("Hit 'OK' to save anyways (you can add trials later and save then) or cancel to go back.")
            warnDlg.show()
            if not warnDlg.OK:
                go = False
        if go:
            NoneType = type(None)
            if len(self.folderPath) > 0:
                for i,j in self.settings['stimList'].items():
                    if self.settings['stimList'][i]['stimType'] != 'Image with audio':
                       self.stimSource[i] = j['stimLoc'] # Re-initializes the stimSource dict to incorporate both existing and new stim.
                    else:
                        tempAname = os.path.split(j['audioLoc'])[1]
                        tempIname = os.path.split(j['imageLoc'])[1]
                        self.stimSource[tempAname] = j['audioLoc']
                        self.stimSource[tempIname] = j['imageLoc']
            sDlg = gui.fileSaveDlg(initFilePath=os.getcwd(), initFileName=self.settings['prefix'], prompt="Name a folder to save study into", allowed="")
            if type(sDlg) is not NoneType:
                self.settings['folderPath'] = sDlg + self.dirMarker #Makes a folder of w/e they entered
                #If there is no pre-selected prefix, make the prefix the folder name!
                if self.settings['prefix'] == "PyHabExperiment":
                    self.settings['prefix'] = os.path.split(sDlg)[1]
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
        """
        Saves a PyHab project to a set of folders dictated by self.folderPath

        :return:
        :rtype:
        """
        if not os.path.exists(self.folderPath):
            os.makedirs(self.folderPath)  # creates the initial folder if it did not exist.
        success = True  # Assume it's going to work.
        # Structure: Top-level folder contains script, then you have data and stimuli.
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
        # Condition file! Save if there are any conditions created.
        # Convoluted mess because the dict won't necessarily be in order and we want the file to be.
        if len(self.condDict) > 0:
            tempArray = []
            for j in range(0, len(self.settings['condList'])):
                tempArray.append([self.settings['condList'][j],self.condDict[self.settings['condList'][j]]])
            with open(self.folderPath+self.settings['condFile'],'w') as co:
                secretWriter = csv.writer(co,lineterminator='\n')
                for k in range(0, len(tempArray)):
                    secretWriter.writerow(tempArray[k])
            if len(self.baseCondDict) > 0:
                # Same again, but for the 'base' conditions, with a modified filename.
                tempArray2 = []
                for l in range(0, len(self.settings['baseCondList'])):
                    tempArray2.append([self.settings['baseCondList'][l], self.baseCondDict[self.settings['baseCondList'][l]]])
                with open(self.folderPath+'base_'+self.settings['condFile'],'w') as bc:
                    baseWriter = csv.writer(bc, lineterminator='\n')
                    for m in range(0, len(tempArray2)):
                        baseWriter.writerow(tempArray2[m])
        # copy stimuli if there are stimuli.
        if len(self.stimSource) > 0:
            for i, j in self.stimSource.items():  # Find each file, copy it over
                try:
                    targPath = stimPath + i
                    shutil.copyfile(j, targPath)
                except:
                    success = False
                    print('Could not copy file ' + j + ' to location ' + targPath + '. Make sure both exist!')
                if success:
                    for q, r in self.settings['stimList'].items():
                        if r['stimType'] != 'Image with audio':
                            if q == i:  # For movies, images, or audio in isolation, the keys match.
                                r['stimLoc'] = 'stimuli' + self.dirMarker + q
                        else:  # Here we have to look at the file paths themselves
                            if os.path.split(r['audioLoc'])[1] == i:
                                r['audioLoc'] = 'stimuli' + self.dirMarker + os.path.split(j)[1]
                            elif os.path.split(r['imageLoc'])[1] == i:
                                r['imageLoc'] = 'stimuli' + self.dirMarker + os.path.split(j)[1]

        if len(list(self.settings['attnGetterList'].keys())) > 0:  # This should virtually always be true b/c default attngetter.
            for i, j in self.settings['attnGetterList'].items():
                try:
                    targPath = stimPath + 'attnGetters' + self.dirMarker
                    if not os.path.exists(targPath):
                        os.makedirs(targPath)
                    if not os.path.exists(targPath + j['stimName']):
                        shutil.copyfile(j['stimLoc'], targPath + j['stimName'])
                        j['stimLoc'] = 'stimuli' + self.dirMarker + 'attnGetters' + self.dirMarker + j['stimName']
                    if 'audioName' in j.keys():
                        if not os.path.exists(targPath + j['audioName']):
                            shutil.copyfile(j['audioLoc'], targPath + j['audioName'])
                            j['audioLoc'] = 'stimuli' + self.dirMarker + 'attnGetters' + self.dirMarker + j['audioName']
                except:
                    success = False
                    print('Could not copy attention-getter file ' + j['stimLoc'] + ' to location ' +  targPath + '. Make sure both exist!')
        if not success:
            errDlg = gui.Dlg(title="Could not copy stimuli!")
            errDlg.addText("Some stimuli could not be copied successfully. See the output of the coder window for details.")
            errDlg.show()
        # Delete any removed stimuli
        if len(self.delList) > 0:
            for i in range(0, len(self.delList)):
                delStimPath = os.path.join(stimPath, self.delList[i])
                if os.path.exists(delStimPath):
                    try:
                        os.remove(delStimPath)
                    except:
                        print("Could not remove stimuli " + delStimPath + " from experiment folder.")
                else:
                    print("Stimuli " + delStimPath + " does not exist to be removed!")
            self.delList = []
        # create/overwrite the settings csv.
        settingsPath = self.folderPath+self.settings['prefix']+'Settings.csv'
        with open(settingsPath,'w') as so: # this is theoretically safer than the "close" system.
            settingsOutput = csv.writer(so, lineterminator='\n')
            for i, j in self.settings.items(): # this is how you write key/value pairs
                settingsOutput.writerow([i, j])

        # Copy over the class and such. Since these aren't modified, make sure they don't exist first.
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
                shutil.copyfile(srcDir+classPLPath, classPLTarg)
            if not os.path.exists(buildTarg):
                shutil.copyfile(srcDir+buildPath, buildTarg)
            if not os.path.exists(initTarg):
                shutil.copyfile(srcDir+initPath, initTarg)
        except:
            # error dialog
            errDlg = gui.Dlg(title="Could not copy PyHab and builder!")
            errDlg.addText("Failed to copy PyHab class scripts and builder script. These can be copied manually from the PyHab folder and will be needed!")
            errDlg.show()
            success=False
            print("Could not copy PyHab and builder!")
        # copy/create the launcher script
        launcherPath = self.folderPath+self.settings['prefix']+'Launcher.py'
        if not os.path.exists(launcherPath):
            try:
                # the location of the pyHabLauncher template file
                if os.path.exists(srcDir+'PyHab Launcher.py'):
                    launcherSource = srcDir+'PyHab Launcher.py'
                else:
                    # It'll end in launcher.py. So need to find a file in the working directory with the last 11 characters 'Launcher.py'
                    fileList = os.listdir()
                    for i in range(0, len(fileList)):
                        if fileList[i][-11:] == 'Launcher.py':
                            launcherSource = fileList[i]
                # Open file and find line 5, aka the path to the settings file, replace it appropriately
                with open(launcherSource,'r') as file:
                    launcherFile = file.readlines()
                newLine = 'setName = \"' + self.settings['prefix']+'Settings.csv\"\r\n'  # Simplified, so it always runs the settings file in that folder.
                launcherFile[6] = newLine
                launcherFile[7] = "#Created in PsychoPy version " + __version__ + "\r\n"
                # now write the new file!
                with open(launcherPath, 'w') as t:
                    t.writelines(launcherFile)
            except:
                errDlg = gui.Dlg(title="Could not save!")
                errDlg.addText("Launcher script failed to save! Please try again or manually copy the launcher script and change the settings line.")
                errDlg.show()
                success=False
                print('creating launcher script failed!')
                if len(launcherSource) == 0:
                    print('Could not find launcher template file!')
                else:
                    print('Found launcher template, still could not save launcher script')
        if success:
            saveSuccessDlg = gui.Dlg(title="Experiment saved!")
            saveSuccessDlg.addText("Experiment saved successfully to" + self.folderPath)
            saveSuccessDlg.show()


    def _runLauncher(self,launcherPath):
        """
        Flagrantly copied from psychopy's own app/coder interface, where it is used for running scripts in the IDE.
        Basically it's like hitting the "run" button in the coder interface, but from within an actively-running script.

        :param launcherPath: Full path to launcher file created by builder
        :type launcherPath: string
        :return:
        :rtype:
        """
        fullPath = launcherPath
        path, scriptName = os.path.split(fullPath)
        importName, ext = os.path.splitext(scriptName)
        # set the directory and add to path
        os.chdir(path)  # try to rewrite to avoid doing chdir in the coder
        sys.path.insert(0, path)

        # do an 'import' on the file to run it
        # delete the sys reference to it (so we think its a new import)
        if importName in sys.modules:
            sys.modules.pop(importName)
        exec ('import %s' % (importName))  # or run first time
