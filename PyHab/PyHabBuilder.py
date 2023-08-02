from psychopy import visual, event, core, gui, monitors, tools, sound,__version__
from psychopy.app import coder
import wx, random, csv, shutil, os, sys, threading, itertools
from math import *
from copy import deepcopy
import pyglet


class PyHabBuilder:
    """
    Graphical interface for constructing PyHab experiments. Runs mostly on a Pyglet window and qtGUI dialogs.
    Saves a settings file in .csv form which can then be read by PyHab Launcher, PyHabClass, PyHabClassPL, and PyHabClassHPP.
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
            self.settings = {'dataColumns': ['sNum', 'sID', 'months', 'days', 'sex', 'cond','condLabel', 'trial','GNG','trialType','stimName','habCrit','habTrialNo','sumOnA','numOnA','sumOffA','numOffA','sumOnB','numOnB','sumOffB','numOffB','trialDuration'],
                                                        'blockSum': '1',
                                                        'trialSum': '1',
                                                        'prefix': 'PyHabExperiment',
                                                        'dataloc':'data'+self.dirMarker,
                                                        'maxDur': {},
                                                        'playThrough': {},
                                                        'movieEnd': [],
                                                        'maxOff': {},
                                                        'minOn': {},
                                                        'maxOn': {},
                                                        'durationCriterion': [],
                                                        'autoRedo': [],
                                                        'onTimeDeadline': {},
                                                        'durationInclude': '1',
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
                                                        'blockList': {},  # 0.10 habituaiton is now handled by blocks entirely
                                                        'blockDataList': [],
                                                        'stimPres': 0,  # Will be set on each run anyways.
                                                        'stimPath': 'stimuli'+self.dirMarker,
                                                        'stimNames': {},
                                                        'stimList': {},
                                                        'screenWidth': {'C':1080,'L':1080,'R':1080},
                                                        'screenHeight': {'C':700,'L':700,'R':700},
                                                        'screenColor': {'C':'black','L':'black','R':'black'},
                                                        'movieWidth': {'C':800,'L':800,'R':800},
                                                        'movieHeight': {'C':600,'L':600,'R':600},
                                                        'screenIndex': {'C':1,'L':1,'R':1},
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
                                                        'dynamicPause': [],
                                                        'midAG': {},
                                                        'hppStimScrOnly': [], # new in 0.9.5, allows for some sophisticaated HPP behavior. List of trial types.
                                                        'folderPath': '',
                                                        'prefLook': '0',
                                                        'startImage': '',
                                                        'endImage': '',
                                                        'nextFlash': '0',
                                                        'loadSep': '0',
                                                        'eyetracker': '0'}
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
            if 'blockDataList' not in self.settings.keys():
                self.settings['blockDataList'] = "[]"
            if 'blockSum' not in self.settings.keys():
                self.settings['blockSum'] = '1'
                self.settings['trialSum'] = '1'
            if 'midAG' not in self.settings:
                self.settings['midAG'] = '{}'
                self.settings['dynamicPause'] = '[]'
            if 'autoRedo' not in self.settings:
                self.settings['durationCriterion'] = '[]'
                self.settings['autoRedo'] = '[]'
                self.settings['onTimeDeadline'] = '{}'
                self.settings['durationInclude'] = '1'
            if 'loadSep' not in self.settings:
                self.settings['loadSep'] = '0'
            if 'hppStimScrOnly' not in self.settings.keys():
                self.settings['hppStimScrOnly'] = '[]'
            if 'maxOn' not in self.settings.keys():
                self.settings['maxOn'] = '{}'
            if 'eyetracker' not in self.settings.keys():
                self.settings['eyetracker'] = '0'
            # Settings requiring evaluation to get sensible values. Mostly dicts.
            evalList = ['dataColumns','blockSum','trialSum','maxDur','condList','baseCondList','movieEnd','playThrough',
                        'trialOrder','stimNames', 'stimList', 'ISI', 'maxOff','minOn', 'maxOn','durationCriterion','autoRedo',
                        'onTimeDeadline','autoAdvance','playAttnGetter','attnGetterList','trialTypes', 'nextFlash',
                        'blockList', 'dynamicPause','midAG','screenWidth','screenHeight','screenIndex','movieWidth',
                        'movieHeight', 'durationInclude', 'loadSep', 'hppStimScrOnly', 'eyetracker']  # in 0.9, this becomes necessary.
            for i in evalList:
                self.settings[i] = eval(self.settings[i])
                if i in ['stimList','attnGetterList']:
                    for [q,j] in self.settings[i].items():
                        try:
                            j['stimLoc'] = ''.join([self.dirMarker if x == otherOS else x for x in j['stimLoc']])
                            if 'audioLoc' in j.keys(): # Specifically for attention-getters of the movie/audio type
                                j['audioLoc'] = ''.join([self.dirMarker if x == otherOS else x for x in j['audioLoc']])
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
            # Backwards compatiblity for attention-getters v0.9.0
            for i, j in self.settings['playAttnGetter'].items():
                if isinstance(j, str):
                    self.settings['playAttnGetter'][i] = {'attnGetter':j,'cutoff':0,'onmin':0.0}
            # Backwards compatibility for new settings format for HPP.
            if not isinstance(self.settings['screenWidth'], dict):
                tmpDict = {'L': self.settings['screenWidth'], 'C': self.settings['screenWidth'], 'R': self.settings['screenWidth']}
                self.settings['screenWidth'] = tmpDict
                tmpDict2 = {'L': self.settings['screenHeight'], 'C': self.settings['screenHeight'], 'R': self.settings['screenHeight']}
                self.settings['screenHeight'] = tmpDict2
                tmpDict3 = {'L': self.settings['movieWidth'], 'C': self.settings['movieWidth'], 'R': self.settings['movieWidth']}
                self.settings['movieWidth'] = tmpDict3
                tmpDict4 = {'L': self.settings['movieHeight'], 'C': self.settings['movieHeight'], 'R': self.settings['movieHeight']}
                self.settings['movieHeight'] = tmpDict4
                tmpDict5 = {'L': self.settings['screenColor'], 'C': self.settings['screenColor'], 'R': self.settings['screenColor']}
                self.settings['screenColor'] = tmpDict5
                tmpDict6 = {'L': self.settings['screenIndex'], 'C': self.settings['screenIndex'], 'R': self.settings['screenIndex']}
                self.settings['screenIndex'] = tmpDict6
            else:
                self.settings['screenColor'] = eval(self.settings['screenColor']) # This is special b/c it cannot be eval'd if it's just a string.
            # back compat for block redo in 0.10.1
            for i,j in self.settings['blockList'].items():
                if 'blockRedo' not in j.keys():
                    self.settings['blockList'][i]['blockRedo'] = False
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
        self.allDataColumns = ['sNum', 'sID', 'months', 'days', 'sex', 'cond','condLabel', 'trial','GNG','trialType','stimName','habCrit','habTrialNo','sumOnA','numOnA','sumOffA','numOffA','sumOnB','numOnB','sumOffB','numOffB', 'trialDuration']
        self.allDataColumnsPL = ['sNum', 'sID', 'months', 'days', 'sex', 'cond','condLabel', 'trial','GNG','trialType','stimName','habCrit','habTrialNo', 'sumOnL','numOnL','sumOnR','numOnR','sumOff','numOff', 'trialDuration']
        self.allDataColumnsHPP = ['sNum', 'sID', 'months', 'days', 'sex', 'cond','condLabel', 'trial','GNG','trialType','stimName','habCrit','habTrialNo', 'sumOnL','numOnL','sumOnC','numOnC','sumOnR','numOnR','sumOff','numOff', 'trialDuration']
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

        # Mode select
        self.modeText = visual.TextStim(self.win, text="Exp Type:", color="white", height=.67*(.15/self.aspect)*.5, pos=[.2, -.9])

        modeColors = ['black','black','black']
        modeColors[eval(self.settings['prefLook'])] = 'green' # Set the color of the initially selected one.

        stButton = visual.Rect(self.win, width=.1, height=.67*(.15/self.aspect), fillColor=modeColors[0], lineColor='white', pos=[.38, -.9])
        stText = visual.TextStim(self.win, text="ST", height=.67*(.15/self.aspect)*.5, pos=stButton.pos)
        self.buttonList['shapes'].append(stButton)
        self.buttonList['text'].append(stText)
        self.buttonList['functions'].append(self.toST)

        plButton = visual.Rect(self.win, width=.1, height=.67 * (.15 / self.aspect), fillColor=modeColors[1], lineColor='white',
                      pos=[.5, -.9])
        plText = visual.TextStim(self.win, text="PL", height=.67*(.15/self.aspect)*.5, pos=plButton.pos)
        self.buttonList['shapes'].append(plButton)
        self.buttonList['text'].append(plText)
        self.buttonList['functions'].append(self.toPL)

        hpButton = visual.Rect(self.win, width=.1, height=.67 * (.15 / self.aspect), fillColor=modeColors[2], lineColor='white',
                      pos=[.62,-.9])
        hpText = visual.TextStim(self.win, text="HPP", height=.67*(.15/self.aspect)*.5, pos=hpButton.pos)
        self.buttonList['shapes'].append(hpButton)
        self.buttonList['text'].append(hpText)
        self.buttonList['functions'].append(self.toHPP)

        # Main function buttons
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
        if len(self.settings['trialTypes']) > 8:
            self.totalPalettePages = floor((len(self.settings['trialTypes'])-1)/8) + 1
        self.trialTypesArray = self.loadTypes(self.typeLocs, self.settings['trialTypes'], page=self.trialPalettePage)
        self.studyFlowArray = self.loadFlow(self.settings['trialOrder'], self.flowArea, self.flowLocs,self.overFlowLocs, self.settings['trialTypes'])

        addBlockButton = visual.Rect(self.win, width=.9*(self.paletteArea[1]-self.paletteArea[0]),height=self.standardPaletteHeight*.20, fillColor="yellow", lineColor="black",
                pos=[self.paletteArea[0]+float(abs(self.paletteArea[1]-self.paletteArea[0]))/2,self.paletteArea[2]-self.standardPaletteHeight*.23])
        addBlockText = visual.TextStim(self.win, alignHoriz='center', alignVert='center', text="Create Block\n(incl. for\nHabituation)", height=.25*addBlockButton.height, pos=addBlockButton.pos,color="black")
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
        dataSetButton = visual.Rect(self.win, width=.3, height=.5*(.2/self.aspect),pos=[-.8,-.65], fillColor="white", lineColor="black")
        dataSetText = visual.TextStim(self.win, text="Data \nsettings",color="black",height=dataSetButton.height*.3, alignHoriz='center', pos=dataSetButton.pos)
        self.buttonList['shapes'].append(dataSetButton)
        self.buttonList['text'].append(dataSetText)
        self.buttonList['functions'].append(self.dataSettingsDlg)
        stimSetButton = visual.Rect(self.win, width=.3, height=.5*(.2/self.aspect),pos=[-.4,-.3], fillColor="white")
        stimSetText = visual.TextStim(self.win, text="Stimuli \nsettings",color="black",height=stimSetButton.height*.3, alignHoriz='center', pos=stimSetButton.pos)
        self.buttonList['shapes'].append(stimSetButton)
        self.buttonList['text'].append(stimSetText)
        if self.settings['prefLook'] in [2, '2']:
            self.buttonList['functions'].append(self.HPP_stimSettingsDlg)
        else:
            self.buttonList['functions'].append(self.stimSettingsDlg)
        condSetButton = visual.Rect(self.win, width=.3, height=.5*(.2/self.aspect),pos=[-.4,-.65], fillColor="white")
        condSetText = visual.TextStim(self.win, text="Condition \nsettings",color="black",height=condSetButton.height*.3, alignHoriz='center', pos=condSetButton.pos)
        self.buttonList['shapes'].append(condSetButton)
        self.buttonList['text'].append(condSetText)
        self.buttonList['functions'].append(self.condSettingsDlg)

        attnGetterButton = visual.Rect(self.win, width=.3, height=.5*(.2/self.aspect), pos=[0, -.3], fillColor = "white")
        attnGetterText = visual.TextStim(self.win, text="Customize \nattention-getters",color="black",height=attnGetterButton.height*.3,alignHoriz='center', pos=attnGetterButton.pos)
        self.buttonList['shapes'].append(attnGetterButton)
        self.buttonList['text'].append(attnGetterText)
        self.buttonList['functions'].append(self.attnGetterDlg)

        stimLibraryButton = visual.Rect(self.win, width=.3, height=.5*(.2/self.aspect), pos=[.4, -.3], fillColor = "white")
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
            blockDataButton = visual.Rect(self.win, width=.15, height=.5*(.2/self.aspect), pos=[-.725, -.65],
                                          fillColor="white")
            blockDataText = visual.TextStim(self.win, text="Block \ndata", color="black",
                                            height=blockDataButton.height*.3, alignHoriz='center',pos=blockDataButton.pos)
            self.buttonList['shapes'].append(blockDataButton)
            self.buttonList['text'].append(blockDataText)
            self.buttonList['functions'].append(self.blockDataDlg)
            # Find the data settings button and shrink it.
            dataIndex = self.buttonList['functions'].index(self.dataSettingsDlg)
            self.buttonList['shapes'][dataIndex].pos = [-.875, -.65]
            self.buttonList['shapes'][dataIndex].width = .15
            self.buttonList['text'][dataIndex].pos = [-.875, -.65]

        if len(self.settings['trialTypes']) > 0:
            advTrialButton = visual.Rect(self.win, width=.3, height=.5 * (.2 / self.aspect), pos=[0, -.65], fillColor="white")
            advTrialText = visual.TextStim(self.win, text="Advanced trial \nsettings", color="black",
                                           height=advTrialButton.height * .3, alignHoriz='center', pos=advTrialButton.pos)
            self.buttonList['shapes'].append(advTrialButton)
            self.buttonList['text'].append(advTrialText)
            self.buttonList['functions'].append(self.advTrialSetup)


        self.workingRect = visual.Rect(self.win, width=1, height=.5, pos=[0,0], fillColor = 'green') #Because there are certain things that take a while.
        self.workingText = visual.TextStim(self.win, text="Working...", height= .3, bold=True, alignHoriz='center', pos=[0,0])


        self.UI = {'bg':[self.flowRect, self.paletteRect, self.modeText], 'buttons': self.buttonList}

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
                    if os.name != 'posix':
                        while self.mouse.getPressed()[0] == 1:
                            pass
                        if self.buttonList['functions'][i] not in [self.toST, self.toPL, self.toHPP]:
                            # If we're opening a dialog box, basically.
                            self.win.winHandle.set_visible(visible=False)
                    self.buttonList['functions'][i]() #It should not be this easy, BUT IT IS. Python is great.
                    if os.name != 'posix':
                        self.win.winHandle.set_visible(visible=True)
            # Some conditions to check if we need to remove buttons, must be done outside the for loop to prevent index errors
            if self.advTrialSetup in self.buttonList['functions'] and len(self.settings['trialTypes']) == 0:
                advTrialIndex = self.buttonList['functions'].index(self.advTrialSetup)
                self.buttonList['shapes'].pop(advTrialIndex)
                self.buttonList['text'].pop(advTrialIndex)
                self.buttonList['functions'].pop(advTrialIndex)
            if self.blockDataDlg in self.buttonList['functions'] and len(list(self.settings['blockList'].keys())) == 0: # TODO: This might be able to survive as is
                blockDataIndex = self.buttonList['functions'].index(self.blockDataDlg)
                self.buttonList['shapes'].pop(blockDataIndex)
                self.buttonList['text'].pop(blockDataIndex)
                self.buttonList['functions'].pop(blockDataIndex)
                # Re-expand old data button
                dataIndex = self.buttonList['functions'].index(self.dataSettingsDlg)
                self.buttonList['shapes'][dataIndex].pos = [-.8,-.65]
                self.buttonList['shapes'][dataIndex].width = .3
                self.buttonList['text'][dataIndex].pos = [-.8, -.65]
            #Check all the trial type elements.
            for j in range(0,len(self.trialTypesArray['shapes'])):
                if self.mouse.isPressedIn(self.trialTypesArray['shapes'][j],buttons=[0]): #Left-click, add to study flow, at end.
                    if self.trialTypesArray['labels'][j] not in self.settings['blockList'].keys():
                        self.settings['trialOrder'].append(self.trialTypesArray['labels'][j])
                    elif self.trialTypesArray['labels'][j] in self.settings['trialOrder'] and self.settings['blockList'][self.trialTypesArray['labels'][j]]['habituation'] in [1, '1', True, 'True']:
                        # If a given habituation block is already in the study flow, prevent adding it twice
                        pass
                    else:
                        self.settings['trialOrder'].append(self.trialTypesArray['labels'][j])
                    self.studyFlowArray=self.loadFlow(self.settings['trialOrder'], self.flowArea, self.flowLocs, self.overFlowLocs, self.settings['trialTypes']) #Reloads the study flow with the new thing added.
                    while self.mouse.isPressedIn(self.trialTypesArray['shapes'][j],buttons=[0]): #waits until the mouse is released before continuing.
                        pass
                elif self.mouse.isPressedIn(self.trialTypesArray['shapes'][j],buttons=[1,2]): #Right-click, modify trial type info.
                    self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)
                    self.workingRect.draw()
                    self.workingText.draw()
                    self.win.flip()
                    if os.name != 'posix': #There's an issue with windows and dialog boxes, don't ask.
                        while 1 in self.mouse.getPressed():
                            pass
                        self.win.winHandle.set_visible(visible=False)
                    # Determine whether we're dealing with a trial or block, launch appropriate interface
                    if self.trialTypesArray['labels'][j] in self.settings['blockList'].keys():
                        self.makeBlockDlg(self.trialTypesArray['labels'][j], new=False)
                    else:
                        self.trialTypeDlg(trialType=self.trialTypesArray['labels'][j], makeNew=False)
                    if os.name != 'posix':
                        self.win.winHandle.set_visible(visible=True)
            for k in range(0, len(self.studyFlowArray['shapes'])):
                if self.mouse.isPressedIn(self.studyFlowArray['shapes'][k]):
                    # Move the trial within the study flow, reload the modified flow array
                    self.settings['trialOrder'] = self.moveTrialInFlow(k, self.settings['trialOrder'], self.flowArea,
                                                                       self.UI, self.studyFlowArray, self.trialTypesArray)
                    self.studyFlowArray = self.loadFlow(self.settings['trialOrder'], self.flowArea, self.flowLocs, self.overFlowLocs, self.settings['trialTypes'])
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

        The dialog by default outputs a list with 12 items in it.
        0 = trial type name

        1 = Maximum duration of trials of this type

        2 = Gaze-contingent trial type?

        3 = Maximum continuous looking-away to end trial of type

        4 = Minimum on-time (cumulative)

        5 = auto-redo trial if minimum on-time not met?

        6 = on-time deadline

        7 = duration criterion rather than on-time

        8 = Auto-advance into trial?

        9 = Attention-getter selection

        10 = End trial on movie end or mid-movie

        11 = inter-stimulus interveral (ISI) for this trial type

        12 = Maximum on-time (single use case, for new gaze contingent trial type mode).

        [if movies assigned to trial type already, they occupy 13 - N]

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
        if len(self.settings['trialTypes']) == len(self.colorsArray) and makeNew:
            errDlg = gui.Dlg(title="Max trial types reached!")
            errDlg.addText("PyHab's builder currently supports a maximum of " + str(len(self.colorsArray)) + " trial or block types.")
            errDlg.show()
        else:
            typeDlg = gui.Dlg(title="Trial Type " + trialType)
            typeDlg.addField("Trial type name: ", trialType)  # Index 0
            if not makeNew:  # if this modifying an existing trial type, pre-fill the existing info.
                if len(prevInfo) == 0:  # allows for removal of movies from the trial type
                    typeDlg.addField("Max duration", self.settings['maxDur'][trialType])  # Index 1
                    maxOff = self.settings['maxOff'][trialType]
                    minOn = self.settings['minOn'][trialType]
                    ISI = self.settings['ISI'][trialType]
                    if trialType in self.settings['maxOn'].keys():
                        maxOn = self.settings['maxOn'][trialType]
                    else:
                        maxOn = 5.0

                else:
                    typeDlg.addField("Max duration", prevInfo[1])  # Index 1
                    maxOff = prevInfo[3]
                    minOn = prevInfo[4]
                    ISI = prevInfo[11]
                    maxOn = prevInfo[12]

                # Find the index of the existing trial type in the study flow and type pane.
                flowIndexes=[]
                for i in range(0,len(self.studyFlowArray['labels'])):
                    if self.studyFlowArray['labels'][i] == trialType:
                        flowIndexes.append(i) 
                typeIndex = self.trialTypesArray['labels'].index(trialType)
                if self.settings['playThrough'][trialType] == 3:
                    chz = ["EitherOr", "Yes", "OnOnly", "No", "MaxOff/MaxOn"]
                elif self.settings['playThrough'][trialType] == 2:
                    chz = ["No", "OnOnly", "Yes", "EitherOr", "MaxOff/MaxOn"]
                elif self.settings['playThrough'][trialType] == 1:
                    chz = ["OnOnly", "Yes", "No", "EitherOr", "MaxOff/MaxOn"]
                elif self.settings['playThrough'][trialType] == 4:
                    chz = ["MaxOff/MaxOn", "Yes", "No", "OnOnly", "EitherOr"]
                else:
                    chz = ["Yes", "OnOnly", "No", "EitherOr", "MaxOff/MaxOn"]
            elif len(prevInfo) > 0:
                typeDlg.addField("Max duration", prevInfo[1])  # Index 1
                maxOff = prevInfo[3]
                minOn = prevInfo[4]
                ISI = prevInfo[11]
                maxOn = prevInfo[12]
                if prevInfo[2] == 3:
                    chz = ["EitherOr", "Yes", "OnOnly", "No", "MaxOff/MaxOn"]
                elif prevInfo[2] == 2:
                    chz = ["No", "Yes", "OnOnly", "EitherOr", "MaxOff/MaxOn"]
                elif prevInfo[2] == 1:
                    chz = ["OnOnly", "Yes", "EitherOr", "No", "MaxOff/MaxOn"]
                elif prevInfo[2] == 4:
                    chz = ["MaxOff/MaxOn", "Yes", "OnOnly", "EitherOr", "No"]
                else:
                    chz = ["Yes", "OnOnly", "EitherOr", "No","MaxOff/MaxOn"]
            else:  # if there are no existing indexes to refer to
                typeDlg.addField("Max duration", 60.0)  # Index 1
                maxOff = 2.0
                minOn = 1.0
                ISI = 0.0
                maxOn = 5.0
                chz = ["Yes", "OnOnly", "EitherOr", "No","MaxOff/MaxOn"]
            typeDlg.addField("Gaze-contingent trial type (next three lines ignored otherwise)", choices=chz)  # Index 2
            typeDlg.addField("Number of continuous seconds looking away to end trial", maxOff)  # Index 3
            typeDlg.addField("Minimum time looking at screen before stimuli can be ended (not consecutive)", minOn)  # Index 4
            # On-time deadline
            if len(prevInfo) > 0:
                if prevInfo[5] in [True, 'True', 1, '1']:
                    autoredo = True
                otdl = prevInfo[6]
                if prevInfo[7] in [True, 'True', 1, '1']:
                    durCrit = True
            else:
                if trialType in self.settings['autoRedo']:
                    autoRedo = True
                else:
                    autoRedo = False
                if trialType in self.settings['onTimeDeadline'].keys():
                    otdl = self.settings['onTimeDeadline'][trialType]
                    if otdl == self.settings['maxDur'][trialType]: # Because it has to default to this under certain circumstances
                        otdl = -1
                else:
                    otdl = -1
                if trialType in self.settings['durationCriterion']:
                    durCrit = True
                else:
                    durCrit = False
            typeDlg.addField("Auto-redo of minimum on-time criterion not met?", autoRedo)  # Index 5
            typeDlg.addField("Deadline to meet on-time criterion (ignored if <= 0)", otdl)  # Index 6
            typeDlg.addField("Check to use total trial duration instead of gaze-on time for trial length calculation", durCrit)  # Index 7

            if len(prevInfo) > 0:
                if prevInfo[8] in [True, 'True', 1, '1']:
                    chz2 = True
            elif trialType in self.settings['autoAdvance']:
                chz2 = True
            else:
                chz2 = False
            typeDlg.addField("Auto-advance INTO trial without waiting for expeirmenter?", initial=chz2)  # Index 8

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
                chz3 = [x for x in list(self.settings['attnGetterList'].keys()) if x != self.settings['playAttnGetter'][trialType]['attnGetter']]
                chz3.insert(0, 'None')
                chz3.insert(0, self.settings['playAttnGetter'][trialType]['attnGetter'])
            typeDlg.addField("Attention-getter for this trial type (Stim presentation mode only)", choices = chz3)  # Index 9
            if trialType in self.settings['movieEnd']:
                chz4 = True
            else:
                chz4 = False
            typeDlg.addField("Only end trial on end of movie repetition? (Only works when presenting stimuli)", initial = chz4)  # Index 10
            typeDlg.addField("Inter-stimulus interval on loops (pause between end of one loop and start of next)", ISI)  # Index 11
            typeDlg.addField("MAXIMUM on-time (only used for 'max-off and max-on' gaze contingent setting", maxOn) # Index 12
            if not makeNew:
                if len(prevInfo) == 0:
                    if len(self.settings['stimNames'][trialType]) > 0:
                        typeDlg.addText("Current movie files in trial type (uncheck to remove)")
                        for i in range(0, len(self.settings['stimNames'][trialType])):
                            if self.settings['prefLook'] in [2,'2']:
                                typeDlg.addField(self.settings['stimNames'][trialType][i]['C'], initial=True) # HPP defaults to C on everything
                            else:
                                typeDlg.addField(self.settings['stimNames'][trialType][i], initial=True)
                elif len(prevInfo) > 13: # If there were no movies to start with, this will have a length of 13.
                    typeDlg.addText("Current stimuli in trial type (uncheck to remove)")
                    for i in range(0,len(self.settings['stimNames'][trialType])):
                        if self.settings['prefLook'] in [2,'2']:
                            typeDlg.addField(self.settings['stimNames'][trialType][i+9]['C'], initial=prevInfo[i + 13])
                        else:
                            typeDlg.addField(self.settings['stimNames'][trialType][i], initial=prevInfo[i+13])


            typeInfo = typeDlg.show()

            if typeDlg.OK:
                # Check if all the things that need to be numbers are actually numbers.
                for i in [1, 3, 4, 6]:
                    if not isinstance(typeInfo[i], float) and not isinstance(typeInfo[i], int):
                        try:
                            typeInfo[i] = eval(typeInfo[i])
                        except:
                            warnDlg = gui.Dlg(title="Warning!")
                            warnDlg.addText(
                                "Number expected, got text instead. \nPlease make sure maximum duration, minimum on-time, maximum off-time, and on-time deadline are all numbers!")
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
                            if trialType in self.settings['playAttnGetter'].keys():
                                self.settings['playAttnGetter'][typeInfo[0]] = self.settings['playAttnGetter'].pop(trialType)
                            if trialType in self.settings['onTimeDeadline'].keys():
                                self.settings['onTimeDeadline'][typeInfo[0]] = self.settings['onTimeDeadline'].pop(trialType)
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
                            self.trialTypesArray = self.loadTypes(self.typeLocs, self.settings['trialTypes'], page=self.trialPalettePage)
                            # Update in all the things that are lists of filenames with a given property
                            listsList = ['autoRedo','autoAdvance','movieEnd','durationCriterion']
                            for k in range(0, len(listsList)):
                                if trialType in self.settings[listsList[k]]:
                                    self.settings[listsList[k]].remove(trialType)
                                    self.settings[listsList[k]].append(typeInfo[0])

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
                        elif '.' in typeInfo[0] or '^' in typeInfo[0] or '*' in typeInfo[0]:
                            warnDlg = gui.Dlg(title="llegal character!")
                            warnDlg.addText("The '.', '^', and '*' characters cannot be used as part of a trial type name. Please rename your trial type")
                            warnDlg.show()
                            skip = True
                            self.trialTypeDlg(typeInfo[0], makeNew, typeInfo)
                        trialType = typeInfo[0]
                    if not skip:

                        self.settings['maxDur'][trialType] = typeInfo[1] #Update maxDur
                        self.settings['maxOff'][trialType] = typeInfo[3]
                        self.settings['minOn'][trialType] = typeInfo[4]
                        self.settings['ISI'][trialType] = typeInfo[11]
                        self.settings['maxOn'][trialType] = typeInfo[12]

                        # Gaze-contingency settings
                        if trialType not in self.settings['playThrough'].keys(): #Initialize if needed.
                            self.settings['playThrough'][trialType] = 0
                        if typeInfo[2] == "Yes" and self.settings['playThrough'][trialType] is not 0: #gaze-contingent trial type, not already tagged as such.
                            self.settings['playThrough'][trialType] = 0
                        elif typeInfo[2] == "No" and self.settings['playThrough'][trialType] is not 2:
                            self.settings['playThrough'][trialType] = 2
                        elif typeInfo[2] == "OnOnly" and self.settings['playThrough'][trialType] is not 1:
                            self.settings['playThrough'][trialType] = 1
                        elif typeInfo[2] == "EitherOr" and self.settings['playThrough'][trialType] is not 3:
                            self.settings['playThrough'][trialType] = 3
                        elif typeInfo[2] == "MaxOff/MaxOn" and self.settings['playThrough'][trialType] is not 4:
                            self.settings['playThrough'][trialType] = 4

                        # Auto-redo trial settings
                        if typeInfo[5] in [False,0,'False','0'] and trialType in self.settings['autoRedo']: #gaze-contingent trial type, not already tagged as such.
                            self.settings['autoRedo'].remove(trialType)
                        elif typeInfo[5] in [True, 1, 'True', '1'] and not trialType in self.settings['autoRedo']:
                            self.settings['autoRedo'].append(trialType)

                        if typeInfo[6] > 0:
                            self.settings['onTimeDeadline'][trialType] = typeInfo[6]
                        elif trialType in self.settings['autoRedo']:
                            self.settings['onTimeDeadline'][trialType] = self.settings['maxDur'][trialType]
                        elif trialType in self.settings['onTimeDeadline'].keys():
                            del self.settings['onTimeDeadline'][trialType]

                        if typeInfo[7] in [False,0,'False','0'] and trialType in self.settings['durationCriterion']:
                            self.settings['durationCriterion'].remove(trialType)
                        elif typeInfo[7] in [True, 1, 'True', '1'] and not trialType in self.settings['durationCriterion']:
                            self.settings['durationCriterion'].append(trialType)

                        # Auto-advance settings
                        if typeInfo[8] in [False,0,'False','0'] and trialType in self.settings['autoAdvance']: #gaze-contingent trial type, not already tagged as such.
                            self.settings['autoAdvance'].remove(trialType)
                        elif typeInfo[8] in [True, 1, 'True', '1'] and not trialType in self.settings['autoAdvance']:
                            self.settings['autoAdvance'].append(trialType)

                        # Attention-getter settings
                        if typeInfo[9] == 'None':
                            if trialType in self.settings['playAttnGetter']:
                                del self.settings['playAttnGetter'][trialType]
                        else:
                            if trialType not in self.settings['playAttnGetter']:  # If it did not have an attngetter before.
                                agname = typeInfo[9]
                                self.settings['playAttnGetter'][trialType] = {'attnGetter':agname, 'cutoff':0, 'onmin':0.0}
                            elif typeInfo[9] is not self.settings['playAttnGetter'][trialType]:
                                # If a different attention-getter has been selected
                                agname = typeInfo[9]
                                self.settings['playAttnGetter'][trialType]['attnGetter'] = agname # leaves cutoff and onmin intact

                        # End-trial-on-movie-end settings
                        if typeInfo[10] in [False,0,'False','0'] and trialType in self.settings['movieEnd']:
                            self.settings['movieEnd'].remove(trialType)
                        elif typeInfo[10] in [True, 1, 'True', '1'] and not trialType in self.settings['movieEnd']:
                            self.settings['movieEnd'].append(trialType)

                        # Remove stimuli if needed
                        if len(typeInfo) > 13: #Again, if there were movies to list.
                            tempMovies = [] #This will just replace the stimNames list
                            for i in range(0,len(self.settings['stimNames'][trialType])):
                                if typeInfo[i+13]:
                                    tempMovies.append(self.settings['stimNames'][trialType][i])
                            self.settings['stimNames'][trialType] = tempMovies

                        # If we need to update the flow pane, it's taken care of above. Here we update the type pallette.
                        if makeNew:
                            self.settings['trialTypes'].append(typeInfo[0])
                            self.settings['stimNames'][typeInfo[0]] = []
                            self.totalPalettePages = floor((len(self.settings['trialTypes'])-1)/8)+1  # Update if needed
                            self.trialPalettePage = deepcopy(self.totalPalettePages)
                            self.trialTypesArray = self.loadTypes(self.typeLocs, self.settings['trialTypes'], page=self.trialPalettePage)
                            # If there exists a condition file or condition settings, warn the user that they will need to be updated!
                            if self.settings['condFile'] is not '':
                                warnDlg = gui.Dlg(title="Update conditions")
                                warnDlg.addText("WARNING! UPDATE CONDITION SETTINGS AFTER ADDING STIMULI TO THIS TRIAL TYPE! \nIf you do not update conditions, the experiment will crash whenever it reaches this trial type.")
                                warnDlg.show()
                            if self.advTrialSetup not in self.buttonList['functions']:
                                advTrialButton = visual.Rect(self.win, width=.3, height=.5 * (.2 / self.aspect),
                                                             pos=[0, -.65], fillColor="white")
                                advTrialText = visual.TextStim(self.win, text="Advanced trial \nsettings",
                                                               color="black",
                                                               height=advTrialButton.height * .3, alignHoriz='center',
                                                               pos=advTrialButton.pos)
                                self.buttonList['shapes'].append(advTrialButton)
                                self.buttonList['text'].append(advTrialText)
                                self.buttonList['functions'].append(self.advTrialSetup)
                self.studyFlowArray = self.loadFlow(self.settings['trialOrder'], self.flowArea, self.flowLocs, self.overFlowLocs, self.settings['trialTypes'])
                self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)
                self.win.flip()

    def advTrialDlg(self, trialType):
        """
        A dialog for advanced trial settings mostly having to do with attention-getters and stimulus presentation

        0/-8 = cutoff attention-getter on gaze-on? T/F [if trial has an AG - not always present]

        1/-7 = cutoff on-time: How long do they have to look to cut off presentation? [if trial has an AG - not always present]

        2/-6 = Pause stimulus presentation when infant is not looking at screen?

        3/-5 = Mid-trial AG: Play an attention-getter if infant looks away mid-trial?

        4/-4 = mid-trial AG trigger: Minimum time to trigger mid-trial AG

        5/-3 = mid-trial AG cutoff: Stop mid-trial AG on gaze-on?

        6/-2 = mid-trial AG cutoff ontime

        7/-1 = HPP ONLY: Only count gaze-on to stimulus-presenting screen? T/F, casts to hppStimScrOnly



        :param trialType: The trial type being modified.
        :type trialType: str
        :return:
        :rtype:
        """
        self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)
        self.workingRect.draw()
        self.workingText.draw()
        self.win.flip()

        adTypeDlg = gui.Dlg("Advanced trial settings")
        adTypeDlg.addText("Advanced trial settings for trial type " + trialType)
        if trialType in self.settings['playAttnGetter']:
            if self.settings['playAttnGetter'][trialType]['cutoff'] in [1, '1', True, 'True']:
                chz1 = True
            else:
                chz1 = False
            adTypeDlg.addField("Cutoff attention-getter on gaze-on?", initial=chz1)
            adTypeDlg.addField("Minimum on-time to cutoff attention-getter (ignored if box above is not checked)",
                               self.settings['playAttnGetter'][trialType]['onmin'])
        # The "dynamic pause" feature is available even if there are no stimuli in order to allow offline coding to
        # simulate it, and if necessary add time to the trial (...?)
        if trialType in self.settings['dynamicPause']:
            chz2 = True
        else:
            chz2 = False
        adTypeDlg.addField("Pause stimulus presentation when infant is not looking at screen?", initial=chz2)

        # mid-trial AG settings are present regardless of whether there is an AG at the start of the trial or not.
        if trialType in self.settings['midAG']:
            chz3 = [x for x in list(self.settings['attnGetterList'].keys()) if x != self.settings['midAG'][trialType]['attnGetter']]
            chz3.insert(0, 'No mid-trial AG')
            chz3.insert(0, self.settings['midAG'][trialType]['attnGetter'])
            trigger = self.settings['midAG'][trialType]['trigger']
            if self.settings['midAG'][trialType]['cutoff'] in [1, '1', True, 'True']:
                midcutoff = True
            else:
                midcutoff = False
            midonmin = self.settings['midAG'][trialType]['onmin']
        elif trialType in self.settings['playAttnGetter']:
            # Default to the start-of-trial attention-getter as first non-None option, with all settings
            chz3 = [x for x in list(self.settings['attnGetterList'].keys()) if x != self.settings['playAttnGetter'][trialType]['attnGetter']]
            chz3.insert(0, self.settings['playAttnGetter'][trialType]['attnGetter'])
            chz3.insert(0, 'No mid-trial AG')
            trigger = 0.0
            if self.settings['playAttnGetter'][trialType]['cutoff'] in [1, '1', True, 'True']:
                midcutoff = True
            else:
                midcutoff = False
            midonmin = self.settings['playAttnGetter'][trialType]['onmin']
        else:
            chz3 = [x for x in list(self.settings['attnGetterList'].keys())]
            chz3.insert(0, 'No mid-trial AG')
            trigger = 2.0
            midcutoff = False
            midonmin = 0.0
        adTypeDlg.addField("Play mid-trial attention-getter on sustained gaze-off (select AG)?", choices=chz3)
        adTypeDlg.addField("Seconds of gaze-off to trigger attention-getter", trigger)
        adTypeDlg.addField("Stop mid-trial AG on gaze-on?", initial=midcutoff)
        adTypeDlg.addField("Minimum on-time to stop mid-trial AG", midonmin)

        hppstimonly = False
        if trialType in self.settings['hppStimScrOnly']:
            hppstimonly = True
        adTypeDlg.addField("HPP Only: Only count stim screen as gaze-on for ending trials?", initial=hppstimonly)


        adTypeInfo = adTypeDlg.show()
        if adTypeDlg.OK:
            fail = [] # amass invalid inputs, save the rest
            if trialType in self.settings['playAttnGetter']:
                if adTypeInfo[len(adTypeInfo)-8] in [True, 1, 'True', '1']:
                    self.settings['playAttnGetter'][trialType]['cutoff'] = 1
                else:
                    self.settings['playAttnGetter'][trialType]['cutoff'] = 0
                if not isinstance(adTypeInfo[len(adTypeInfo)-7], float) and not isinstance(adTypeInfo[len(adTypeInfo)-6], int):
                    try:
                        eval(adTypeInfo[len(adTypeInfo)-7])
                    except:
                        fail.append("Number expected for minimum on-time to end attention-getter, got text instead!")
                if isinstance(adTypeInfo[len(adTypeInfo)-7], float) and not isinstance(adTypeInfo[len(adTypeInfo)-7], int):
                    self.settings['playAttnGetter'][trialType]['onmin'] = adTypeInfo[len(adTypeInfo)-7]
            # Pause behavior
            if adTypeInfo[len(adTypeInfo)-6] in [True, 1, 'True', '1'] and trialType not in self.settings['dynamicPause']:
                self.settings['dynamicPause'].append(trialType)
            elif adTypeInfo[len(adTypeInfo)-6] in [False, 0, 'False', '0'] and trialType in self.settings['dynamicPause']:
                # Remove if this behavior has been turned off.
                self.settings['dynamicPause'].pop(self.settings['dynamicPause'].index(trialType))
            # Mid-trial AG
            if adTypeInfo[len(adTypeInfo)-5] in self.settings['attnGetterList']:
                # We have the luxury of only caring about certain inputs if there is a mid-trial AG
                if not isinstance(adTypeInfo[len(adTypeInfo) - 4], float) and not isinstance(adTypeInfo[len(adTypeInfo) - 4], int):
                    try:
                        trigger = eval(adTypeInfo[len(adTypeInfo) - 4])
                    except:
                        trigger = 0.0
                        fail.append("Number expected for minimum off-time to trigger mid-trail AG, got text instead!")
                else:
                    trigger = adTypeInfo[len(adTypeInfo) - 4]

                if adTypeInfo[len(adTypeInfo)-3] in [1, '1', True, 'True']:
                    midcut = 1
                    if not isinstance(adTypeInfo[len(adTypeInfo) - 2], float) and not isinstance(adTypeInfo[len(adTypeInfo) - 2], int):
                        try:
                            midmin = eval(adTypeInfo[len(adTypeInfo) - 2])
                        except:
                            midmin = 0.0
                            fail.append("Number expected for minimum on-time to cutoff mid-trail AG, got text instead!")
                    else:
                        midmin = adTypeInfo[len(adTypeInfo) - 2]
                else:
                    midcut = 0
                    midmin = 0.0
                self.settings['midAG'][trialType] = {'attnGetter':adTypeInfo[len(adTypeInfo)-5], 'trigger':trigger,
                                                     'cutoff':midcut, 'onmin':midmin}
            elif trialType in self.settings['midAG'].keys():
                # If the mid-trial AG has been set to "none" but was previously set to something, remove it.
                self.settings['midAG'].pop(trialType)
            if adTypeInfo[len(adTypeInfo) - 1] in [1, '1', True, 'True']:
                if trialType not in self.settings['hppStimScrOnly']:
                    self.settings['hppStimScrOnly'].append(trialType)
            elif trialType in self.settings['hppStimScrOnly']:
                # remove it.
                self.settings['hppStimScrOnly'].pop(self.settings['hppStimScrOnly'].index(trialType))

            if len(fail) > 0:
                errDlg = gui.Dlg("Problem!")
                errDlg.addText("The following fields received invalid input, please re-enter! (Other fields have been saved)")
                for i in range(0, len(fail)):
                    errDlg.addText(fail[i])
                failDisp = errDlg.show()
                self.advTrialDlg(trialType)

    def advTrialSetup(self):
        """
        A function for selecting the trials you want to access the advanced settings of.
        Spawns a panel with all the trial types. Reuses code from the block interface.
        Doesn't need to check existence of trials because

        :return:
        :rtype:
        """
        if os.name != 'posix':
            self.win.winHandle.set_visible(visible=True) # Might cause a little flicker, but the best solution for now

        blockUI = {'bg': [], 'buttons': {'shapes': [], 'text': [], 'functions': []}}
        blockOrder = []  # This will be what contains the order for the block!
        end = False
        newFlowArea = [-.9, .9, .9, -.9]  # X,X,Y,Y
        menuArea = visual.Rect(self.win, width=newFlowArea[1] - newFlowArea[0],
                                  height=newFlowArea[3] - newFlowArea[2], fillColor='lightgrey', lineColor='black',
                                  pos=[newFlowArea[0] + float(abs(newFlowArea[1] - newFlowArea[0])) / 2,
                                       newFlowArea[2] - float(abs(newFlowArea[3] - newFlowArea[2])) / 2])
        cancelButton = visual.Rect(self.win, width=.15, height=.67 * (.15 / self.aspect), pos=[-.52, -.8],
                                   fillColor="red")
        cancelText = visual.TextStim(self.win, text="Cancel", height=.45 * cancelButton.height, pos=cancelButton.pos,
                                     color='white')
        instrText = visual.TextStim(self.win, text="Choose trial type to access advanced settings", pos=[.1, -.8], color='black',
                                    height=.08)

        blockUI['bg'].append(menuArea)
        blockUI['bg'].append(instrText)
        blockUI['buttons']['shapes'].append(cancelButton)
        blockUI['buttons']['text'].append(cancelText)
        menuLocs = []

        for y in [.2, .4, .6, .8]:  # four rows for the block flow.
            for z in range(1,11):
                menuLocs.append([newFlowArea[0] + z * (newFlowArea[1] - newFlowArea[0]) * self.flowGap,
                                    newFlowArea[2] + y * (newFlowArea[3] - newFlowArea[2])])

        trialTypes = self.loadTypes(menuLocs, self.settings['trialTypes'])
        # We only want base trial types, not blocks, so we omit all blocks.
        delIndex = []
        forbid = list(self.settings['blockList'].keys())  # If we're using this to make hab blocks, we need to allow (indeed mandate) Hab trials.
        for i in range(0, len(trialTypes['labels'])):
            if trialTypes['labels'][i] in forbid:
                delIndex.insert(0, deepcopy(i))  # In reverse order, because it makes the next part way simpler
        for j in range(0, len(delIndex)):
            del trialTypes['labels'][delIndex[j]]
            del trialTypes['shapes'][delIndex[j]]
            del trialTypes['text'][delIndex[j]]

        # Going to leave the gaps this will leave for now. Think it actually communicates more info.
        flow={'lines':[],'shapes':[],'labels':[],'text':[],'extras':[]}
        done = False
        while not done:
            self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray) # put main UI under new one.
            self.showMainUI(blockUI, flow, trialTypes)
            self.win.flip()
            if self.mouse.isPressedIn(blockUI['buttons']['shapes'][0]):
                # There's only one button in this mode, it's cancel
                done = True  # Just break the loop and that's that.
                while self.mouse.isPressedIn(blockUI['buttons']['shapes'][0], buttons=[0]):  # waits until the mouse is released before continuing.
                    pass
            for k in range(0, len(trialTypes['shapes'])):  # Simply access the dialog for that trial
                if self.mouse.isPressedIn(trialTypes['shapes'][k], buttons=[0]):
                    done = True
                    while self.mouse.isPressedIn(trialTypes['shapes'][k], buttons=[0]):
                        pass  # Wait until mouse-up
                    if os.name != 'posix':
                        self.win.winHandle.set_visible(visible=False)
                    self.advTrialDlg(trialTypes['labels'][k])

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
        if len(self.settings['trialTypes']) > 0 and not (len(self.settings['trialTypes']) == 20 and new):
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
                startsSameAs = False
                for i,j in self.settings['blockList'].items():
                    if len(newBlock[0]) <= len(i):
                        if newBlock[0] == i[0:len(newBlock[0])]:
                            startsSameAs = True
                    if len(i) <= len(newBlock[0]):
                        if i == newBlock[0][0:len(i)]:
                            startsSameAs = True
                if newBlock[0] == '':
                    errDlg = gui.Dlg(title="Missing information!")
                    errDlg.addText("Name cannot be blank!")
                    irrel = errDlg.show()
                    self.makeBlockDlg(name, new)
                elif '.' in newBlock[0] or '^' in newBlock[0] or '*' in newBlock[0]:
                    errDlg = gui.Dlg(title="Illegal block name!")
                    errDlg.addText("Name contains illegal character, or is reserved. Please rename!")
                    irrel = errDlg.show()
                    self.makeBlockDlg(name, new)
                elif new and newBlock[0] in self.settings['trialTypes']:
                    errDlg = gui.Dlg(title="Name already in use!")
                    errDlg.addText("Name is already in use for another trial or block. Please rename!")
                    irrel = errDlg.show()
                    self.makeBlockDlg(name, new)
                elif new and startsSameAs:
                    # For safety, make it so names can't start the same as an existing block
                    errDlg = gui.Dlg(title="Block name is the start of another block name!")
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
                    if os.name != 'posix':
                        # For Windows, because now we snap back to the regular window.
                        self.win.winHandle.set_visible(visible=True)
                    self.blockMaker(newBlock[0], new)
        elif len(self.settings['trialTypes']) == 0:
            errDlg = gui.Dlg(title="No trials to make blocks with!")
            errDlg.addText("Make some trial types before trying to add them to a block.")
            irrel = errDlg.show()
        else:
            errDlg = gui.Dlg(title="Max trial/block types reached!")
            errDlg.addText("Maximum number of trial/block types has been reached (20), no more can be made.")
            irrel = errDlg.show()


    def blockMaker(self, blockName, new=True, hab=False):
        """
        For making multi-trial blocks. Or multi-block-blocks. Blocks are necessary for habituation.

        Creates a kind of sub-UI that overlays over the main UI. Because it's just for blocks, we can ditch some things.
        We can actually completely overlay the regular UI. Problem is, if the regular UI continues to draw, the mouse
        detection will still work, even if a shape is behind another shape. So, like with conditions, we need a totally
        parallel UI

        Hab blocks cannot be embedded in other blocks.

        :param blockName: Name of new block
        :type blockName: str
        :param new: Is this a new block or a modification of an existing one?
        :type new: bool
        :param hab: Is this for a habituation meta-trial? # TODO: No longer needs to be an argument?
        :type hab: bool
        :return:
        :rtype:
        """
        self.showMainUI(self.UI,self.studyFlowArray, self.trialTypesArray)  # Draw the usual UI under the new one...
        # Define new flow UI. We can reuse a lot of the base UI, happily.
        blockUI = {'bg':[],'buttons':{'shapes':[],'text':[],'functions':[]}}
        blockOrder = []  # This will be what contains the order of trials for the block!
        # It's useful to keep this separate for the block UI stuff, just means it needs to be tied together later.
        habFields = {'habituation': 0, # All of the habituation settings fields, starting with hab on/off. Defaults.
                    'habByDuration': 0,
                    'maxHabTrials': 14,
                    'setCritWindow': 3,
                    'setCritDivisor': 2.0,
                    'setCritType': 'First',
                    'habThresh': 5.0,
                    'metCritWindow': 3,
                    'metCritDivisor': 1.0,
                    'metCritStatic': 'Moving',
                    'calcHabOver': []
        }
        blockRedo = False # 0.10.1: Block-level redo setting

        end = False
        newFlowArea = [-.97, .75, .97, -.97]  # X,X,Y,Y
        newFlowRect = visual.Rect(self.win, width=newFlowArea[1] - newFlowArea[0],
                                    height=newFlowArea[3] - newFlowArea[2], fillColor='lightgrey', lineColor='black',
                                    pos=[newFlowArea[0] + float(abs(newFlowArea[1] - newFlowArea[0])) / 2,
                                         newFlowArea[2] - float(abs(newFlowArea[3] - newFlowArea[2])) / 2])

        doneButton = visual.Rect(self.win,width=.15, height=.67*(.15/self.aspect), pos=[-.82,-.8],fillColor="springgreen")
        doneText = visual.TextStim(self.win, text="Done", height=.5*doneButton.height, pos=doneButton.pos, color='black')
        cancelButton = visual.Rect(self.win, width=.15, height=.67 * (.15 / self.aspect), pos=[-.62, -.8],
                                 fillColor="red")
        cancelText = visual.TextStim(self.win, text="Cancel", height=.45 * doneButton.height, pos=cancelButton.pos,
                                   color='white')
        habSettingsButton = visual.Rect(self.win, width=.4, height=.67*(.15/self.aspect), pos=[-.32,-.8],fillColor = "DarkOrange")
        habSettingsText = visual.TextStim(self.win, text="Habituation (OFF)", height=.45 * habSettingsButton.height, pos=habSettingsButton.pos,
                                   color='white')

        blockRedoButton = visual.Rect(self.win, width=.4, height=.67*(.15/self.aspect), pos=[.1,-.8],fillColor = "grey")
        blockRedoText = visual.TextStim(self.win, text="Block redo (OFF)", height=.45 * blockRedoButton.height, pos=blockRedoButton.pos,
                                   color='white')

        instrText = visual.TextStim(self.win, text="Construct block trial order", pos=[.5, -.8], color='black', height=.06)
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
        blockUI['buttons']['shapes'].append(habSettingsButton)
        blockUI['buttons']['text'].append(habSettingsText)
        blockUI['buttons']['shapes'].append(blockRedoButton)
        blockUI['buttons']['text'].append(blockRedoText)

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
        trialTypes = self.loadTypes(bigPaletteLocs, self.settings['trialTypes'])
        delIndex = []
        forbid = [blockName]  # List of trials and blocks which can't be added to the block's internal trial list
        for q,z in self.settings['blockList'].items():  # Attempt to eliminate infinite loops
            if blockName in z['trialList'] and blockName != q:
                forbid.append(q)
        for i in range(0, len(trialTypes['labels'])):
            if trialTypes['labels'][i] in forbid:
                delIndex.insert(0, deepcopy(i))  # In reverse order, because it makes the next part way simpler
        for j in range(0, len(delIndex)):
            del trialTypes['labels'][delIndex[j]]
            del trialTypes['shapes'][delIndex[j]]
            del trialTypes['text'][delIndex[j]]
        # Go through and update positions
        for k in range(0, len(trialTypes['labels'])):
            trialTypes['shapes'][k].pos = bigPaletteLocs[k]
            trialTypes['text'][k].pos = bigPaletteLocs[k]
        if not new:
            blockOrder = deepcopy(self.settings['blockList'][blockName]['trialList'])
            blockFlow = self.loadFlow(tOrd=blockOrder, space=newFlowArea, locs=newFlowLocs, overflow=newFlowLocs, types=self.settings['trialTypes'])
            if self.settings['blockList'][blockName]['habituation'] in [1, '1', True, 'True']:
                habSettingsText.text = 'Habituation (ON)'
                habSettingsButton.fillColor = "DarkGreen"
                # Copy over existing habituation settings.
                for i,j in ['blockList'][blockName].items():
                    if i in habFields.keys():
                        habFields[i] = j
            if self.settings['blockList'][blockName]['blockRedo'] in [1, '1', True, 'True']:
                blockRedo = True
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
                        else:  # Create our new block or modify existing
                            # Since most of the fields are going to come from the hab fields, we start with that
                            # and add the trial list entry, and done!
                            tempBlockObject = habFields
                            tempBlockObject['trialList'] = blockOrder
                            tempBlockObject['blockRedo'] = blockRedo
                            self.settings['blockList'][blockName] = tempBlockObject
                            if new:
                                self.settings['trialTypes'].append(blockName)
                                # Update palette pages if needed.
                                self.totalPalettePages = floor((len(self.settings['trialTypes'])-1) / 8) + 1
                                self.trialPalettePage = deepcopy(self.totalPalettePages)
                                self.trialTypesArray = self.loadTypes(self.typeLocs, self.settings['trialTypes'], page=self.trialPalettePage)
                            else:
                                self.studyFlowArray=self.loadFlow(self.settings['trialOrder'], self.flowArea, self.flowLocs, self.overFlowLocs, types=self.settings['trialTypes'])
                            done = True
                            if self.blockDataDlg not in self.buttonList['functions']:
                                blockDataButton = visual.Rect(self.win, width=.15, height=.5 * (.2 / self.aspect),
                                                              pos=[-.725, -.65],
                                                              fillColor="white", lineColor="black")
                                blockDataText = visual.TextStim(self.win, text="Block \ndata",
                                                                color="black",
                                                                height=blockDataButton.height * .3, alignHoriz='center',
                                                                pos=blockDataButton.pos)
                                self.buttonList['shapes'].append(blockDataButton)
                                self.buttonList['text'].append(blockDataText)
                                self.buttonList['functions'].append(self.blockDataDlg)
                                # Find the data settings and shrink it.
                                dataIndex = self.buttonList['functions'].index(self.dataSettingsDlg)
                                self.buttonList['shapes'][dataIndex].pos = [-.875, -.65]
                                self.buttonList['shapes'][dataIndex].width = .15
                                self.buttonList['text'][dataIndex].pos = [-.875, -.65]
                            while self.mouse.isPressedIn(blockUI['buttons']['shapes'][i], buttons=[0]):  # waits until the mouse is released before continuing.
                                pass
                    elif blockUI['buttons']['text'][i].text == 'Cancel':
                        done = True  # Just break the loop and that's that.
                        while self.mouse.isPressedIn(blockUI['buttons']['shapes'][i], buttons=[0]):  # waits until the mouse is released before continuing.
                            pass
                    elif blockUI['buttons']['text'][i].text[0] == 'H': # Since hab can have two text values.
                        if len(blockFlow['labels']) > 0:
                            habFields = self.habSettingsDlg(trialList=blockOrder, lastSet=deepcopy(habFields))
                            if habFields['habituation'] in [1, '1', True, 'True']:
                                habSettingsText.text = 'Habituation (ON)'
                                habSettingsButton.fillColor = "DarkGreen"
                    elif blockUI['buttons']['text'][i].text[0] == 'B': # Block redo also has multiple values.
                        if blockRedo == False:
                            blockRedo = True
                            blockRedoText.text="Block redo (ON)"
                            blockRedoButton.fillColor = "Gold"
                            while self.mouse.isPressedIn(blockUI['buttons']['shapes'][i], buttons=[0]):  # waits until the mouse is released before continuing.
                                pass
                        else:
                            blockRedo = False
                            blockRedoText.text = "Block redo (OFF)"
                            blockRedoButton.fillColor = "Gray"
                            while self.mouse.isPressedIn(blockUI['buttons']['shapes'][i], buttons=[0]):  # waits until the mouse is released before continuing.
                                pass

            for j in range(0, len(trialTypes['shapes'])):  # Only need to worry about adding trials, no modding them from here!
                if self.mouse.isPressedIn(trialTypes['shapes'][j], buttons=[0]):
                    blockOrder.append(trialTypes['labels'][j])
                    blockFlow = self.loadFlow(tOrd=blockOrder, space=newFlowArea, locs=newFlowLocs, overflow=newFlowLocs, types=self.settings['trialTypes'])
                    while self.mouse.isPressedIn(trialTypes['shapes'][j],buttons=[0]):  # waits until the mouse is released before continuing.
                        pass
            for k in range(0, len(blockFlow['shapes'])):  # Rearrange or remove, as in the usual loop!
                if self.mouse.isPressedIn(blockFlow['shapes'][k], buttons=[0]):
                    blockOrder = self.moveTrialInFlow(k, blockOrder, newFlowArea, blockUI, blockFlow, trialTypes)
                    blockFlow = self.loadFlow(tOrd=blockOrder, space=newFlowArea, locs=newFlowLocs, overflow=newFlowLocs, types=self.settings['trialTypes'])
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
            for q in range(0, len(self.settings['blockList'][blockName]['trialList'])):
                if self.settings['blockList'][blockName]['trialList'][q] in self.settings['blockList'].keys():
                    # Identifies any nested blocks, adds them to the 'forbid' list.
                    forbid.append(self.settings['blockList'][blockName]['trialList'][q])

            for r,l in self.settings['blockList'].items(): # hab blocks cannot be added to other blocks.
                if l['habituation'] in [1, '1', True, 'True']:
                    forbid.append(r)

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
        if len(self.settings['trialTypes']) > 0:  # A catch if we've deleted the last trial type so it doesn't break the palette
            self.totalPalettePages = floor((len(self.settings['trialTypes']) - 1) / 8) + 1  # Update if needed
            if self.trialPalettePage > self.totalPalettePages:  # In case we've lost the page we're on. Otherwise, stay on current page
                self.trialPalettePage = deepcopy(self.totalPalettePages)
        self.trialTypesArray = self.loadTypes(self.typeLocs,self.settings['trialTypes'], page=self.trialPalettePage)  # easiest to just reload the trial types.
        # For the study flow, it's easiest just to remove it from the trial order and reload the study flow.
        if dType in self.settings['trialOrder']:
            while dType in self.settings['trialOrder']:
                self.settings['trialOrder'].remove(dType)
        self.studyFlowArray = self.loadFlow(self.settings['trialOrder'], self.flowArea, self.flowLocs, self.overFlowLocs, types=self.settings['trialTypes'])  # To update colors if needed.
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

    
    def loadFlow(self, tOrd, space, locs, overflow, types, conlines=True, trials=True, specNumItems=0):
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
        :param types: List of items being put into this flow. Typically the list of trial types, except when making conditions.
        :type types: list
        :param conlines: A special boolean added for cases where we might not want connecting lines between items in the flow, e.g. conditions.
        :type conLines: bool
        :param trials: A special bool added for cases where we might not be dealing with trial types, to avoid certain pitfalls in conditional logic.
        :type trials: bool
        :param specNumItems: A special argument for cases where there are weird line overlaps that change the length of things. Defaults to 0, only used when calling recursively.
        :type specNumItems: int
        :return: A dictionary of all of the entities to draw into the block or study flow
        :rtype: dict
        """

        numItems = len(tOrd)
        tTypes = types
        outputDict = {'lines':[],'shapes':[],'text':[],'labels':[], 'extras':[]}  #Labels allows us to index the others while still keeping order.
        j = 0 # This serves a purpose, trust me. It's for rendering hab blocks.
        if specNumItems > 0:
            numItems = specNumItems  # Currently this deals with the edge of edge cases, a hab in position 20 looping into the second line.
        if numItems < 21:  # This determines which of the two grid layouts are used.
            flowSpace = locs
        else:
            flowSpace = overflow
        for i in range(0, len(tOrd)):
            # Now, actually build the list of objects to render.
            if j < len(flowSpace)-1 or (j == len(flowSpace)-1 and numItems == len(flowSpace)):
                try:
                    c = tTypes.index(tOrd[i])  # find the trial type, get color index
                except:
                    c=0
                if tOrd[i] in self.settings['blockList'].keys() and trials:
                    if self.settings['blockList'][tOrd[i]]['habituation'] in [1, '1', True, 'True']:  # The special category todo: remove
                        numItems += 1
                        if j % 10 == 9:
                            j += 1  # Just in case we're at the point where it would loop around to the second row. We don't want that.
                            if numItems == 20 or numItems == 39:  # Special case of breaking flowLocs limits.
                                # TODO: BF: if there are multiple hab blocks or if there are precisely 41 items when you have a line skip like this it doesn't count them correctly in the study flow interface.
                                # But, having more than one hab block breaks the whole program anyways. Will become an issue with generic blocks
                                return self.loadFlow(tOrd, space, locs, overflow, types, specNumItems=numItems + 1)
                        lx1 = flowSpace[j][0]
                        j += 1
                        lx2 = flowSpace[j][0]
                        lx = (lx2 + lx1) / 2  # Ideally putting it square in between the two places.
                        loc = [lx, flowSpace[j][1]]
                        tempObj = visual.Rect(self.win, width=self.flowWidthObj * 2, height=self.flowHeightObj,
                                              fillColor=self.colorsArray[c], pos=loc)
                        for q in range(0, len(self.settings['blockList'][tOrd[i]]['trialList'])):
                            tempStr = self.settings['blockList'][tOrd[i]]['trialList'][q]
                            newwidth = self.flowWidthObj / len(self.settings['blockList'][tOrd[i]]['trialList'])
                            tempPip = visual.Rect(self.win, width=newwidth, height=self.flowHeightObj / 2.5,
                                                  fillColor=self.colorsArray[tTypes.index(tempStr)],
                                                  pos=[lx + newwidth * (
                                                              q - (len(self.settings['blockList'][tOrd[i]]['trialList']) - 1) / 2),
                                                       flowSpace[j][1] - self.flowHeightObj / 2.25])
                            outputDict['extras'].append(tempPip)
                    else:
                        tempObj = visual.Rect(self.win, width=self.flowWidthObj, height=self.flowHeightObj, fillColor=self.colorsArray[c], pos=flowSpace[j])
                        for q in range(0, len(self.settings['blockList'][tOrd[i]]['trialList'])):
                            tempStr = self.settings['blockList'][tOrd[i]]['trialList'][q]
                            newwidth = self.flowWidthObj/(2*len(self.settings['blockList'][tOrd[i]]['trialList']))
                            tempPip = visual.Rect(self.win, width=newwidth, height=self.flowHeightObj / 2.5,
                                                  fillColor=self.colorsArray[tTypes.index(tempStr)],
                                                  pos=[flowSpace[j][0] + newwidth * (q - (len(self.settings['blockList'][tOrd[i]]['trialList']) - 1) / 2),
                                                       flowSpace[j][1] - self.flowHeightObj / 2.25])
                            outputDict['extras'].append(tempPip)
                elif tOrd[i] in self.settings['autoAdvance'] and j not in [0, 10, 20, 30] and trials:
                    # Make it adjacent to the last one, unless it would start a row, in which case leave it.
                    loc = [flowSpace[j][0]-abs(space[1]-space[0])*((self.flowGap-self.flowWidMult)/2), flowSpace[j][1]]
                    tempObj = visual.Rect(self.win, width=abs(space[1]-space[0])*(self.flowWidMult + (self.flowGap-self.flowWidMult)), height=self.flowHeightObj, fillColor=self.colorsArray[c], pos=loc)
                elif tOrd[i] in [0, '0']:
                    # A special case for the condition thing for HPP!
                    if tOrd[i] == 0:
                        tOrd[i] = str(tOrd[i])  # string conversion helps with the text element later
                    tempObj = visual.Rect(self.win, width=self.flowWidthObj, height=self.flowHeightObj, fillColor='white', lineColor='black', pos=flowSpace[j])
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
        if conlines:
            if numItems == 0:
                pass #So we do not add a line if there is no line to draw!
            elif numItems < 11:
                tempLine = visual.Line(self.win, start=locs[0], end=outputDict['shapes'][-1].pos, color="White")
                outputDict['lines'].append(tempLine)
            elif numItems < 21:
                tempLine = visual.Line(self.win, start=locs[0], end=locs[9], color="White")
                tempLine2 = visual.Line(self.win, start=locs[10], end=outputDict['shapes'][-1].pos, color="White")
                outputDict['lines'].append(tempLine)
                outputDict['lines'].append(tempLine2)
            elif numItems < 31:
                tempLine = visual.Line(self.win, start=overflow[0], end=overflow[9], color="White")
                tempLine2 = visual.Line(self.win, start=overflow[10], end=overflow[19], color="White")
                tempLine3 = visual.Line(self.win, start=overflow[20], end=outputDict['shapes'][-1].pos, color="White")
                outputDict['lines'].append(tempLine)
                outputDict['lines'].append(tempLine2)
                outputDict['lines'].append(tempLine3)
            elif numItems < 41:
                tempLine = visual.Line(self.win, start=overflow[0], end=overflow[9], color="White")
                tempLine2 = visual.Line(self.win, start=overflow[10], end=overflow[19], color="White")
                tempLine3 = visual.Line(self.win, start=overflow[20], end=overflow[29], color="White")
                tempLine4 = visual.Line(self.win, start=overflow[30], end=outputDict['shapes'][-1].pos, color="White")
                outputDict['lines'].append(tempLine)
                outputDict['lines'].append(tempLine2)
                outputDict['lines'].append(tempLine3)
                outputDict['lines'].append(tempLine4)
            else:
                tempLine = visual.Line(self.win, start=overflow[0], end=self.overFlowLocs[9], color="White")
                tempLine2 = visual.Line(self.win, start=overflow[10], end=self.overFlowLocs[19], color="White")
                tempLine3 = visual.Line(self.win, start=overflow[20], end=overflow[29], color="White")
                tempLine4 = visual.Line(self.win, start=overflow[30], end=outputDict['shapes'][-1].pos, color="White")
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
        self.trialTypesArray = self.loadTypes(self.typeLocs,self.settings['trialTypes'], page=self.trialPalettePage)

    def lastPalettePage(self):
        """
        Simple function for moving to the previous page of the trial type palette
        :return:
        :rtype:
        """
        if self.trialPalettePage > 1:
            self.trialPalettePage -= 1
        self.trialTypesArray = self.loadTypes(self.typeLocs, self.settings['trialTypes'], page=self.trialPalettePage)

    def loadTypes(self, typeLocations, typeList, page=1):
        """
        This function creates the trial types palette.

        Type pallette dictionary components:
        'shapes': visual.Rect objects
        'text': visual.TextStim objects
        'labels': A sort of index for the other two, a plain string labeling the trial or block type.

        :param typeLocations: The array of coordinates on which buttons can be placed. Usually self.typeLocs
        :type typeLocations: list
        :param typeList: A list of what is being populated into the array. Usually self.settings['trialTypes']
        :type typeList: list
        :param page: Page number for when there are more types than fit on one page, in order to render the correct one.
        :type page: int
        :return:
        :rtype:
        """
        if len(typeList) == 0:  # if working w/ an old settings file or one that for w/e reason has no ttypes.
            tOrd = self.settings['trialOrder']
            tTypes = []#list of trial types
            for i in range(0,len(tOrd)):
                if tOrd[i] not in tTypes:
                    tTypes.append(tOrd[i]) #creating a  list of unique trial types
        else:
            tTypes = typeList
        outputDict=  {'shapes':[],'text':[],'labels':[]} #Dicts ain't ordered but lists within dicts sure are!
        #Create the same trial type squares we see in the flow, but wholly independent objects for drawing purposes (allowing one to change w/out the other)
        for i in range(0+len(typeLocations)*(page-1), min(len(typeLocations)*page,len(tTypes))):
            #Now, actually build the list of objects to render.
            tempObj = visual.Rect(self.win,width=self.typeWidthObj, height=self.typeHeightObj, fillColor=self.colorsArray[i], pos=typeLocations[i%len(typeLocations)])
            numChar = len(tTypes[i])
            dispText = deepcopy(tTypes[i])
            if numChar > 10:
                # Get first 5 and last 4. For readability. Happily, labels is unaffected.
                strt = dispText[0:5]
                dispText = strt+'...'+dispText[-4:len(dispText)]
                numChar=10
            elif numChar <= 3:
                numChar = 4 #Maximum height
            tempTxt = visual.TextStim(self.win, alignHoriz='center', alignVert='center',bold=True,height=self.typeHeightObj/(.34*numChar),text=dispText, pos=typeLocations[i%len(typeLocations)])
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
                #launcherPath = self.folderPath+self.settings['prefix']+'Launcher.py'
                # TODO: This no longer works.
                #launcher = coder.ScriptThread(target=self._runLauncher(launcherPath), gui=self)
                #launcher.start()
    
    def univSettingsDlg(self): #The universal settings button.
        """
        Settings that apply to every PyHab study regardless of anything else.

        0 = prefix: The prefix of the launcher and all data files.

        1 = blindPres: Level of experimenter blinding, 0 (none), 1 (no trial type info), or
            2 (only info is whether a trial is currently active.

        2 = nextFlash: Whether to have the coder window flash to alert the experimenter they need to manually trigger
            the next trial

        3 = durationInclude: Trial duration calculations include last gaze-off or not

        4 = loadSeparate: New setting in 0.9.4, movie playback issues have created a situation where some (but not all)
            experiments might benefit from going back to the old ways of loading one movie file for *each* individual
            instance of a trial, rather than trying to load one movie file and load it once. This setting controls
            whether that happens.

        5 = eyetracker: New in 0.10.4, Tobii integration (which is much more seamless than alternatives). Can be set
            to simply record eye-tracking info OR to control the experiment as a replacement for a human coder. (0/1/2)

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
        if self.settings['nextFlash'] in ['1',1,'True',True]:
            ch3 = ["Yes","No"]
        else:
            ch3= ["No","Yes"]
        uDlg.addField("Flash to alert experimenter to manually start next trial?", choices=ch3)
        if self.settings['durationInclude'] in ['1',1,'True',True]:
            ch4 = ["Yes","No"]
        else:
            ch4 = ["No","Yes"]
        uDlg.addField("Trial duration calculations include last gaze-off event?", choices=ch4)

        if self.settings['loadSep'] in ['1',1,'True',True]:
            ch5 = ["Yes","No"]
        else:
            ch5 = ["No", "Yes"]
        uDlg.addField("Load each stimulus file multiple times to prevent rewind glitches? SEE 'Troubleshooting' IN MANUAL", choices=ch5)

        ch6 = []
        if self.settings['eyetracker'] in ['1',1]:
            ch6 = ["Record only", "Off", "Control advancement"]
        elif self.settings['eyetracker'] in ['2',2]:
            ch6 = ["Control advancement", "Off", "Record only"]
        else:
            ch6 = ["Off", "Record only", "Control advancement"]
        uDlg.addField("Tobii eye-tracker integration", choices=ch6)

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
            if uInfo[2] == "Yes":
                self.settings['nextFlash'] = 1
            else:
                self.settings['nextFlash'] = 0
            if uInfo[3] == "Yes":
                self.settings['durationInclude'] = 1
            else:
                self.settings['durationInclude'] = 0
            if uInfo[4] == "Yes":
                self.settings['loadSep'] = 1
            else:
                self.settings['loadSep'] = 0
            if uInfo[5] == "Off":
                self.settings['eyetracker'] = 0
            elif self.settings['prefLook'] == 2:
                self.settings['eyetracker'] = 0
                errDlg = gui.Dlg()
                errDlg.addText("Cannot use eye-tracker in HPP experiments!")
                errDlg.addText("Set eye-tracker mode to 'Off'")
                errDlg.show()
            elif uInfo[5] == "Record only":
                self.settings['eyetracker'] = 1
            elif self.settings['prefLook'] == 1:
                self.settings['eyetracker'] = 1
                errDlg = gui.Dlg()
                errDlg.addText("Cannot use 'control advancement' with Preferential Looking designs at this time.")
                errDlg.addText("Set eye-tracker mode to 'Record only'")
                errDlg.show()
            else:
                self.settings['eyetracker'] = 2
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
        # Because addField is very literal about check-boxes, need to do this
        if self.settings['blockSum']:
            dDlg.addField("Block-level", initial=True)
        else:
            dDlg.addField("Block-level", initial=False)
        if self.settings['trialSum']:
            dDlg.addField("Trial-level", initial=True)
        else:
            dDlg.addField("Trial-level", initial=False)
        dDlg.addText("Check all columns you would like to be recorded in your data files. ")
        dDlg.addText("ANYTHING UNCHECKED WILL NOT BE STORED IN ANY WAY!")
        if self.settings['prefLook'] in [1,'1',True,'True']:
            tempDataCols = self.allDataColumnsPL
        elif self.settings['prefLook'] in [2,'2']:
            tempDataCols = self.allDataColumnsHPP
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
            if datInfo[0]:
                self.settings['blockSum'] = 1
            else:
                self.settings['blockSum'] = 0
            if datInfo[1]:
                self.settings['trialSum'] = 1
            else:
                self.settings['trialSum'] = 0
            for j in range(2, len(datInfo)): # For the data columsn themselves, separate from the toggle of block/trial level
                if datInfo[j]:
                    tempCols.append(tempDataCols[j-2])
            self.settings['dataColumns'] = tempCols
        
    def toST(self):
        """
        A function that converts PL or HPP to single-target. PL to ST is NBD. HPP is more of a challenge.

        :return:
        :rtype:
        """
        if self.settings['prefLook'] not in [0,'0']:

            if self.settings['prefLook'] in [2,'2']:
                # If we're coming from HPP we have some transforms to do
                warnDlg = gui.Dlg("Warning, HPP conversion!")
                warnDlg.addText("You are about to convert the experiment away from head-turn preference procedure.")
                warnDlg.addText("This will remove all HPP stimulus and data settings, and all conditions settings")
                warnDlg.addText("Press OK to continue, or cancel to cancel.")
                if os.name != 'posix':
                    self.win.winHandle.set_visible(visible=False)
                irrel = warnDlg.show()
                if warnDlg.OK:
                    self.buttonList['functions'][
                        self.buttonList['functions'].index(self.HPP_stimSettingsDlg)] = self.stimSettingsDlg
                    stIndex = self.buttonList['functions'].index(self.toST)
                    plIndex = self.buttonList['functions'].index(self.toPL)
                    hpIndex = self.buttonList['functions'].index(self.toHPP)
                    self.buttonList['shapes'][stIndex].fillColor = 'green'
                    self.buttonList['shapes'][plIndex].fillColor = 'black'
                    self.buttonList['shapes'][hpIndex].fillColor = 'black'
                    self.settings['prefLook'] = 0
                    self.settings['dataColumns'] = self.allDataColumnsPL
                    for i, j in self.settings['stimNames'].items():
                        for x in range(0, len(j)):
                            tmp = deepcopy(j[x]['C'])
                            j[x] = tmp
                    self.settings['condFile'] = ""
                    self.settings['condList'] = []
                    self.condDict = {}
                    self.settings['randPres'] = 0
                if os.name != 'posix':
                    self.win.winHandle.set_visible(visible=True)

            else:
                stIndex = self.buttonList['functions'].index(self.toST)
                plIndex = self.buttonList['functions'].index(self.toPL)
                hpIndex = self.buttonList['functions'].index(self.toHPP)
                self.buttonList['shapes'][stIndex].fillColor='green'
                self.buttonList['shapes'][plIndex].fillColor='black'
                self.buttonList['shapes'][hpIndex].fillColor = 'black'

                self.settings['prefLook'] = 0
                self.settings['dataColumns'] = self.allDataColumns
            while 1 in self.mouse.getPressed():
                pass # Just a little thing so it doesn't get called for every frame the mouse is down on the button.


    def toPL(self):
        """
        A function that converts ST or HPP to preferential looking. ST to PL is NBD. HPP is more of a challenge.
        :return:
        :rtype:
        """
        if self.settings['prefLook'] not in [1, '1']:
            if self.settings['prefLook'] in [2, '2']:
                # If we're coming from HPP we have some transforms to do
                warnDlg = gui.Dlg("Warning, HPP conversion!")
                warnDlg.addText("You are about to convert the experiment away from head-turn preference procedure.")
                warnDlg.addText("This will remove all HPP stimulus and data settings, and all conditions settings")
                warnDlg.addText("Press OK to continue, or cancel to cancel.")
                if os.name != 'posix':
                    self.win.winHandle.set_visible(visible=False)
                irrel = warnDlg.show()
                if warnDlg.OK:
                    self.buttonList['functions'][self.buttonList['functions'].index(self.HPP_stimSettingsDlg)] = self.stimSettingsDlg
                    stIndex = self.buttonList['functions'].index(self.toST)
                    plIndex = self.buttonList['functions'].index(self.toPL)
                    hpIndex = self.buttonList['functions'].index(self.toHPP)
                    self.buttonList['shapes'][stIndex].fillColor = 'black'
                    self.buttonList['shapes'][plIndex].fillColor = 'green'
                    self.buttonList['shapes'][hpIndex].fillColor = 'black'
                    self.settings['prefLook'] = 1
                    self.settings['dataColumns'] = self.allDataColumnsPL
                    for i, j in self.settings['stimNames'].items():
                        for x in range(0, len(j)):
                            tmp = deepcopy(j[x]['C'])
                            j[x] = tmp
                    self.settings['condFile'] = ""
                    self.settings['condList'] = []
                    self.condDict = {}
                    self.settings['randPres'] = 0
                if os.name != 'posix':
                    self.win.winHandle.set_visible(visible=True)


            else:
                # No warning just do it
                stIndex = self.buttonList['functions'].index(self.toST)
                plIndex = self.buttonList['functions'].index(self.toPL)
                hpIndex = self.buttonList['functions'].index(self.toHPP)
                self.buttonList['shapes'][stIndex].fillColor = 'black'
                self.buttonList['shapes'][plIndex].fillColor = 'green'
                self.buttonList['shapes'][hpIndex].fillColor = 'black'
                self.settings['prefLook'] = 1
                self.settings['dataColumns'] = self.allDataColumnsPL
                if self.settings['eyetracker'] == 2:
                    self.settings['eyetracker'] = 1  # Because it can't be used for control purposes.
            while 1 in self.mouse.getPressed():
                pass # Just a little thing so it doesn't get called for every frame the mouse is down on the button.


    def toHPP(self):
        """
        A function that converts ST or PL experiments to HPP. Always a little complicated.

        :return:
        :rtype:
        """
        if self.settings['prefLook'] not in [2, '2']:
            warnDlg = gui.Dlg("Warning, HPP conversion!")
            warnDlg.addText("You are about to convert the experiment to head-turn preference procedure.")
            warnDlg.addText("You will need to update stimulus settings for multiple screens, and use ")
            warnDlg.addText("the conditions interface to control which screen stimuli appear on. Any")
            warnDlg.addText("existing conditions settings and conditions will be removed.")
            warnDlg.addText("Press OK to continue, or cancel to cancel.")
            if os.name != 'posix':
                self.win.winHandle.set_visible(visible=False)
            irrel = warnDlg.show()
            if warnDlg.OK:
                stIndex = self.buttonList['functions'].index(self.toST)
                plIndex = self.buttonList['functions'].index(self.toPL)
                hpIndex = self.buttonList['functions'].index(self.toHPP)
                self.buttonList['shapes'][stIndex].fillColor = 'black'
                self.buttonList['shapes'][plIndex].fillColor = 'black'
                self.buttonList['shapes'][hpIndex].fillColor = 'green'
                self.settings['prefLook'] = 2
                # find the stim settings button and change its behavior
                self.buttonList['functions'][self.buttonList['functions'].index(self.stimSettingsDlg)] = self.HPP_stimSettingsDlg

                # Convert stimNames into the right format, move all things to 'C'
                for i, j in self.settings['stimNames'].items():
                    for x in range(0, len(j)):
                        tmp = {'L':0,'C':j[x],'R':0}
                        j[x] = tmp

                self.settings['dataColumns'] = self.allDataColumnsHPP

                # Forget any extant conditions
                self.settings['condFile'] = ""
                self.settings['condList'] = []
                self.condDict = {}
                self.settings['randPres'] = 0

                self.settings['eyetracker'] = 0

            if os.name != 'posix':
                self.win.winHandle.set_visible(visible=True)
            while 1 in self.mouse.getPressed():
                pass # Just a little thing so it doesn't get called for every frame the mouse is down on the button.

    def stimSettingsDlg(self, lastSet=[], redo=False, screen='all'):
        """

        Settings relating to stimulus presentation. Indexes from the dialog (non-HPP version):

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
        :param screen: Optional. For HPP, lets you set for just the individual screen the settings apply to.
        :type screen: string
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
            if screen == 'all':
                lastSet.append(self.settings['screenWidth']['C'])
                lastSet.append(self.settings['screenHeight']['C'])
                lastSet.append(self.settings['screenColor']['C'])
                lastSet.append(self.settings['movieWidth']['C'])
                lastSet.append(self.settings['movieHeight']['C'])
            else:
                lastSet.append(self.settings['screenWidth'][screen])
                lastSet.append(self.settings['screenHeight'][screen])
                lastSet.append(self.settings['screenColor'][screen])
                lastSet.append(self.settings['movieWidth'][screen])
                lastSet.append(self.settings['movieHeight'][screen])
            lastSet.append(self.settings['freezeFrame'])
            if screen == 'all':
                lastSet.append(self.settings['screenIndex']['C'])
            else:
                lastSet.append(self.settings['screenIndex'][screen])
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
        defDisp = pyglet.canvas.Display()
        allScrs = defDisp.get_screens()
        if len(allScrs) > 1:
            screenList = list(range(0, len(allScrs)))
        elif self.settings['prefLook'] in [2, '2']:
            screenList = [0, 1, 2, 3]  # Because even if you don't have a second screen now, you presumably will later.
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
                if screen == 'all':
                    # Settings that are screen-specific, setting for all screens at once.
                    allScreenSets = ['screenWidth','screenHeight','screenColor','movieWidth','movieHeight','screenIndex']
                    indList = [0, 1, 2, 3, 4, 6]  # indexes that are screen-spec settings
                    for q in range(0, len(allScreenSets)):
                        # Iterates through the dicts of screen-specific settings
                        for i,j in self.settings[allScreenSets[q]].items():
                            self.settings[allScreenSets[q]][i] = stimfo[indList[q]]
                else:
                    self.settings['screenWidth'][screen] = stimfo[0]
                    self.settings['screenHeight'][screen] = stimfo[1]
                    self.settings['screenColor'][screen] = stimfo[2]
                    self.settings['movieWidth'][screen] = stimfo[3]
                    self.settings['movieHeight'][screen] = stimfo[4]
                    self.settings['screenIndex'][screen] = stimfo[6]
                self.settings['freezeFrame'] = stimfo[5]
                self.settings['expScreenIndex'] = stimfo[7]
            else:
                warnDlg = gui.Dlg(title="Warning!")
                warnDlg.addText(
                    "Number expected, got text instead. \nPlease make sure window height/width, movie height/width, and freeze-frame duration are all numbers!")
                warnDlg.show()
                self.stimSettingsDlg(stimfo, redo=True)

    def HPP_stimSettingsDlg(self):
        """
        A dialog box for the stimulus settings unique to head-turn preference procedures. Just selects the screen to
        then open the stimulus dialog window for.

        :return:
        :rtype:
        """
        self.showMainUI(self.UI, self.studyFlowArray, self.trialTypesArray)
        self.workingRect.draw()
        self.workingText.draw()
        self.win.flip()

        sDlg = gui.Dlg(title="Select screen")

        sDlg.addField("Select which screen to modify settings of", choices=['all','Left','Center','Right'])
        sDlg.addText("WARNING: selecting 'all' will overwrite all settings for individual screens!")
        screenChoice = sDlg.show()
        if sDlg.OK:
            if screenChoice[0] != 'all':
                screenChoice[0] = screenChoice[0][0]  # Get just the first letter for L/C/R
            self.stimSettingsDlg(screen=screenChoice[0])


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
            cz = ['Movie', 'Image', 'Audio', 'Image with audio', 'Animation']
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
                if stType in ['Movie', 'Image', 'Audio']:  # Image w/ audio is complicated, so we will take care of that separately.
                    for i in range(0, stNum):
                        stimDlg = gui.fileOpenDlg(prompt="Select stimulus file (only one!)")
                        if type(stimDlg) is not NoneType:
                            fileName = os.path.split(stimDlg[0])[1] # Gets the file name in isolation.
                            self.stimSource[fileName] = stimDlg[0]  # Creates a "Find this file" path for the save function.
                            self.settings['stimList'][fileName] = {'stimType': stType, 'stimLoc': stimDlg[0]}
                elif stType == 'Animation':  #Animations don't require files, just names
                    sDlg2 = gui.Dlg(title="Name of animations (no spaces)")
                    sDlg2.addText("Put the names of the different animation functions you will create here")
                    for i in range(0, stNum):
                        sDlg2.addField("Animation name:")
                    animInfo = sDlg2.show()
                    if sDlg2.OK:
                        for j in range(0, len(animInfo)):
                            # As long as nothing is added to stimSource it won't fail because stimLoc isn't a path
                            self.settings['stimList'][animInfo[j]] = {'stimType':stType, 'stimLoc':animInfo[j]}
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
                    if self.settings['stimList'][toRemove]['stimType'] != 'Image with audio' and self.settings['stimList'][toRemove]['stimType'] != 'Animation':
                        self.delList.append(toRemove)
                        if toRemove in self.stimSource.keys():
                            try:
                                del self.stimSource[toRemove]
                            except:
                                print("Could not remove from stimSource!")
                    elif self.settings['stimList'][toRemove]['stimType'] == 'Image with audio':
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
                        if self.settings['prefLook'] in [2, '2']:
                            self.settings['stimNames'][q] = [x for x in self.settings['stimNames'][q] if x['C'] != toRemove]
                        else:
                            self.settings['stimNames'][q] = [x for x in self.settings['stimNames'][q] if x != toRemove]





    def addStimToTypesDlg(self):
        """
        A series dialog boxes, the first selecting a trial type and the number of stimuli to add to it,
        a second allowing you to add stimuli from the stimulus library that is stimList in the settings.
        Also used for adding beginning and end of experiment images

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
                            if self.settings['prefLook'] in [2, '2']: # HPP
                                self.settings['stimNames'][tType].append({'L':0, 'C':newList[z], 'R':0})
                            else:
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
                aDlg2.addField("Attention-getter background color (default = same as stimuli)", choices=['default','white','black','gray'])
                ans2 = aDlg2.show()
                if aDlg2.OK:
                    tempGetter={'stimType': ans2[1], 'bgColor': ans2[2]}
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
                ch2 = ['default','white','black','gray']
                if 'bgColor' in currAG.keys():
                    ch2 = [x for x in ch2 if x != currAG['bgColor']]
                    ch2.insert(0, currAG['bgColor'])
                aDlg2b.addField("Attention-getter background color: ", choices=ch2) # Index 2
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
                        if ans2b[3] is "Yes":  # Same stim type, change file. Ignore shape settings for now
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
                    if len(ans2b) > 5:  # If we had shape/color settings
                        self.settings['attnGetterList'][ans2b[0]].update({'shape': ans2b[4], 'color': ans2b[5]})
                    self.settings['attnGetterList'][ans2b[0]].update({'bgColor': ans2b[2]}) # update BGcolor

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
        cDlg.addField("Use condition-based presentation? If yes, a new interface will open",initial=chkBox)
        cDlg.addField("Pre-existing condition file (optional, leave blank to make new file called conditions.csv)", self.settings['condFile'])
        if not chkBox:
            cDlg.addText("NOTE: This will overwrite any existing file named conditions.csv! If you have an existing conditions file, rename it first.")
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
                if len(self.settings['trialTypes']) == 0:  # If there are no trial types
                    allReady = False
                for i in range(0,len(self.settings['trialTypes'])):
                    if self.settings['trialTypes'][i] not in self.settings['blockList'].keys(): # If a trial type has no movies associated with it
                        if self.settings['trialTypes'][i] not in self.settings['stimNames'].keys():
                            allReady = False
                        elif len(self.settings['stimNames'][self.settings['trialTypes'][i]]) == 0:  # Another way that it can have no movies associated with it.
                            allReady = False
                if allReady:
                    if len(condInfo[1]) > 0:
                        self.settings['condFile'] = condInfo[1]
                    else:
                        self.settings['condFile'] = ""
                    if os.name != 'posix':
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
        condContent = [] # The content of each condition (a dict of lists).
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
        if condPath != "" and os.path.exists(condPath) and not rep:  # If we already have a pre-existing cond file and aren't in the process of looping.
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
        if condPath == "":
            self.settings['condFile'] = 'conditions.csv'
            condPath = 'conditions.csv'
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
        if self.settings['prefLook'] not in [2, '2'] and len(self.settings['condList']) == 0:
            txt2 = "Auto-generate\nconditions"
        else:
            txt2 = "Randomize\nover subjects"
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
            if len(self.settings['blockList']) > 0:
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
                        if os.name != 'posix':
                            while 1 in self.mouse.getPressed():  # Work on mouseup, impt. for windows.
                                pass
                            self.win.winHandle.set_visible(visible=False)
                        if trialMode:
                            thisDict = self.settings['stimNames']
                            bm = False
                        else:
                            thisDict = self.settings['blockList'] # TODO: This is not going to work?
                            bm = True
                        self.condSetter(thisDict, cond=condList[i], ex=True, blockmode=bm)
                        if os.name != 'posix':
                            self.win.winHandle.set_visible(visible=True)
                        while 1 in self.mouse.getPressed():
                            # Making sure that clicking "OK" doesn't immediately trip a click inside the interface
                            pass
                        done = True
                        # Refresh the condition display
                        self.condMaker(rep=True, currPage=currPage, trialMode=trialMode, resetDict=resetDict)
                if self.mouse.isPressedIn(addCondButton):
                    if os.name != 'posix':
                        while 1 in self.mouse.getPressed():
                            pass
                        self.win.winHandle.set_visible(visible=False)
                    if trialMode:
                        thisDict = self.settings['stimNames']
                        bm = False
                    else:
                        thisDict = self.settings['blockList']
                        bm = True
                    self.condSetter(thisDict, ex=False, blockmode=bm)
                    if os.name != 'posix':
                        self.win.winHandle.set_visible(visible=True)
                    while 1 in self.mouse.getPressed():
                        pass
                    done = True
                    # Start this over...
                    self.condMaker(rep=True, currPage=currPage, bc=bc, trialMode=trialMode, resetDict=resetDict)
                if self.mouse.isPressedIn(blockModeButton) and len(self.settings['blockList'])>0:
                    while 1 in self.mouse.getPressed():
                        pass
                    done = True
                    self.condMaker(rep=True, currPage=currPage, bc=bc, trialMode=not trialMode, resetDict=resetDict)
                if self.mouse.isPressedIn(deleteCondButton) and len(condList)>0:
                    if os.name != 'posix':
                        while 1 in self.mouse.getPressed():
                            pass
                        self.win.winHandle.set_visible(visible=False)
                    self.delCond()
                    if os.name != 'posix':
                        self.win.winHandle.set_visible(visible=True)
                    while len(self.mouse.getPressed()) < 0:
                        pass
                    done = True
                    # Start this over...
                    self.condMaker(rep=True, currPage=currPage, bc=bc, trialMode=trialMode, resetDict=resetDict)
                if self.mouse.isPressedIn(randomCondsButton) and len(condList)>0:
                    if os.name != 'posix':
                        while 1 in self.mouse.getPressed():
                            pass
                        self.win.winHandle.set_visible(visible=False)
                    self.condRandomizer(bcReset=bc)
                    if os.name != 'posix':
                        self.win.winHandle.set_visible(visible=True)
                    while len(self.mouse.getPressed()) < 0:
                        pass
                    done = True
                elif self.mouse.isPressedIn(randomCondsButton) and len(condList) == 0 and self.settings['prefLook'] not in [2, '2']:
                    if os.name != 'posix':
                        while 1 in self.mouse.getPressed():
                            pass
                        self.win.winHandle.set_visible(visible=False)
                    self.autoCondSetup()
                    if os.name != 'posix':
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


    def condSetter(self, shuffleList, cond='NEW', ex=False, blockmode=False):
        """
        A new interface for ordering stimuli within a trial type or trials within a block for a specific condition.
        Increases flexibility and usability. Uses an overlay like the block-constructor interface

        ST/PL output: {trialType:[stim1, stim2]}
        HPP output: {trialType:[{'L':0,'C':stim1,'R':0},{}]}

        :param shuffleList: Either the stimNames dict or the blockList dict. Defines which one we are modifying.
        :type shuffleList: dict
        :param cond: Condition name
        :type cond: str
        :param ex: Whether the condition already exists
        :type ex: bool
        :param blockmode: Are we reordering a block or a trial? Matters because even in HPP need to be blocks
        :type blockmode: bool
        :return:
        :rtype:
        """
        condDlg2 = gui.Dlg(title="Define condition")
        condDlg2.addField("Condition label:", cond)
        condDlg2.addText("You will have separate screens to set the order of movies in each trial type. Press OK to begin")
        condDinfo = condDlg2.show()
        if condDlg2.OK:
            if os.name != 'posix':
                self.win.winHandle.set_visible(visible=True)
            condDinfo[0] = str(condDinfo[0])
            if ex and condDinfo[0] != cond:  # Renamed existing condition
                self.settings['condList'][self.settings['condList'].index(cond)] = condDinfo[0]
                if cond in self.condDict.keys():
                    self.condDict[condDinfo[0]] = self.condDict.pop(cond)
            cond = condDinfo[0]
            outputDict = {}
            if self.settings['prefLook'] in [2, '2']: # Just for convenience
                HPP = True
            else:
                HPP = False

            # Define new UI. We can reuse a lot of the base UI, happily.
            condUI = {'bg': [], 'buttons': {'shapes': [], 'text': [], 'functions': []}}

            newFlowArea = [-1, .75, 1, -1]  # X,X,Y,Y
            newFlowRect = visual.Rect(self.win, width=newFlowArea[1] - newFlowArea[0],
                                      height=newFlowArea[3] - newFlowArea[2], fillColor='DarkGrey', lineColor='black',
                                      pos=[newFlowArea[0] + float(abs(newFlowArea[1] - newFlowArea[0])) / 2,
                                           newFlowArea[2] - float(abs(newFlowArea[3] - newFlowArea[2])) / 2])

            doneButton = visual.Rect(self.win, width=.15, height=.67 * (.15 / self.aspect), pos=[-.72, -.8],
                                     fillColor="springgreen")
            doneText = visual.TextStim(self.win, text="Done", height=.5 * doneButton.height, pos=doneButton.pos,
                                       color='black')
            cancelButton = visual.Rect(self.win, width=.15, height=.67 * (.15 / self.aspect), pos=[-.52, -.8],
                                       fillColor="red")
            cancelText = visual.TextStim(self.win, text="Cancel", height=.45 * doneButton.height, pos=cancelButton.pos,
                                         color='white')




            bigPaletteArea = [.7, 1, 1, -1]  # temporary, bigger palette, without trial type maker buttons!
            bigPaletteRect = visual.Rect(self.win, width=bigPaletteArea[1] - bigPaletteArea[0],
                                         height=bigPaletteArea[3] - bigPaletteArea[2], fillColor='white',
                                         lineColor='black',
                                         pos=[bigPaletteArea[0] + float(abs(bigPaletteArea[1] - bigPaletteArea[0])) / 2,
                                              bigPaletteArea[2] - float(abs(bigPaletteArea[3] - bigPaletteArea[2])) / 2])

            instrText = visual.TextStim(self.win, text="Set stimulus order for trial type", pos=[.1, -.9], color='black', height=.1)

            condUI['bg'].append(newFlowRect)
            condUI['bg'].append(bigPaletteRect)
            condUI['bg'].append(instrText)
            condUI['buttons']['shapes'].append(doneButton)
            condUI['buttons']['text'].append(doneText)
            condUI['buttons']['shapes'].append(cancelButton)
            condUI['buttons']['text'].append(cancelText)

            bigPaletteLocs = []
            newFlowLocs = []


            for x in [.27, .73]:  # Two columns of trial types
                for z in range(0, 10):
                    bigPaletteLocs.append([bigPaletteArea[0] + x * (bigPaletteArea[1] - bigPaletteArea[0]),
                                           bigPaletteArea[2] + .05 * (bigPaletteArea[3] - bigPaletteArea[2]) +
                                           z * .09 * (bigPaletteArea[3] - bigPaletteArea[2])])

            if HPP and not blockmode:
                # For HPP we actually want to number this differently. Two sets of three vertical locations, sequential.
                for a in [.22, .67]: # Two rows, ultimately, each one with a stack!
                    for z in range(1,8):
                        for y in [-.1, 0, .1]:  # additions to a. Multiplication is bad.
                            newFlowLocs.append([newFlowArea[0] + z * (newFlowArea[1] - newFlowArea[0]) * (self.flowGap*1.25),
                                                newFlowArea[2] + (y+a) * (newFlowArea[3] - newFlowArea[2])])
            else:
                for y in [.2, .4, .6, .8]:  # four rows for the block flow.
                    for z in range(1, 11):
                        newFlowLocs.append([newFlowArea[0] + z * (newFlowArea[1] - newFlowArea[0]) * self.flowGap,
                                            newFlowArea[2] + y * (newFlowArea[3] - newFlowArea[2])])



            labelList = list(shuffleList.keys())
            i = 0
            while i < len(labelList):
                tempType = labelList[i]
                instrText.text="Set stimulus order for trial type " + tempType
                # Rebuilding this every time allows us to make boxes for each instance and update the instr text
                condUI['bg'] = [newFlowRect, bigPaletteRect, instrText]
                tempStims = deepcopy(shuffleList[tempType])
                if blockmode:
                    tempStims = tempStims['trialList']
                if HPP and not blockmode:
                    tempStims = [x['C'] for x in tempStims]
                    for l in range(0, len(newFlowLocs)):
                        if l % 3 == 0:
                            txtFill = 'L:'
                            tempBox = visual.Rect(self.win, width=(newFlowLocs[3][0] - newFlowLocs[0][0])*.975,
                                                  height=4 * (self.flowHeightObj), pos=[newFlowLocs[l][0], newFlowLocs[l+1][1]],
                                                  lineColor='black', fillColor='white')
                            tempBoxText = visual.TextStim(self.win, text=str(round(l/3) + 1),
                                                          pos=[tempBox.pos[0], tempBox.pos[1] + tempBox.height * .55],
                                                          color='white')
                            condUI['bg'].append(tempBox)
                            condUI['bg'].append(tempBoxText)
                        elif l % 3 == 1:
                            txtFill = 'C:'
                        elif l % 3 == 2:
                            txtFill = 'R:'

                        tempLabel = visual.TextStim(self.win, text=txtFill, pos=[newFlowLocs[l][0]-(newFlowLocs[3][0]-newFlowLocs[0][0])*.4, newFlowLocs[l][1]],color='black', height=.06)

                        condUI['bg'].append(tempLabel)
                    if ex:
                        tempOrder = deepcopy(self.condDict[cond][tempType])
                        # format: [{L:0,C:stimName,R:0}] etc., need to convert to just a list in LCR order
                        condOrder = []
                        for p in range(0, len(tempOrder)):
                            condOrder.append(tempOrder[p]['L'])
                            condOrder.append(tempOrder[p]['C'])
                            condOrder.append(tempOrder[p]['R'])
                    else:
                        condOrder = []
                    stims = self.loadTypes(bigPaletteLocs, tempStims)  # Populates the palette with stimuli. No need to bother with invisibles here.
                else:
                    if not blockmode:
                        for l in range(0, len(tempStims)):
                            tempBox = visual.Rect(self.win, width=(newFlowLocs[1][0]-newFlowLocs[0][0]),
                                                  height=self.flowHeightObj+.1, pos=newFlowLocs[l],
                                                  lineColor='black', fillColor='white')
                            tempBoxText = visual.TextStim(self.win, text=str(l+1), pos=[tempBox.pos[0], tempBox.pos[1]+self.flowHeightObj+.1], color='white')
                            condUI['bg'].append(tempBox)
                            condUI['bg'].append(tempBoxText)
                    invisStims = []
                    if ex:
                        condOrder = deepcopy(self.condDict[cond][tempType])
                        for q in range(0, len(tempStims)):
                            if tempStims[q] in condOrder:
                                invisStims.append(tempStims[q])
                    else:
                        condOrder = []
                    stims = self.loadTypes(bigPaletteLocs, tempStims)  # Populates the palette with stimuli.
                    for n in range(0, len(invisStims)):
                        invisdex = stims['labels'].index(invisStims[n])
                        # Can't delete it outright, but can make it not render...
                        stims['shapes'][invisdex].fillColor='white'
                        stims['shapes'][invisdex].lineColor='white'


                condFlow = self.loadFlow(tOrd=condOrder, space=newFlowArea, locs=newFlowLocs, overflow=newFlowLocs,
                                         types=tempStims, trials=False, conlines=blockmode)

                done = False

                while not done:
                    self.showMainUI(condUI, condFlow, stims)
                    self.win.flip()
                    # Now for all the interactability!
                    for z in range(0, len(condUI['buttons']['shapes'])):
                        if self.mouse.isPressedIn(condUI['buttons']['shapes'][z]):
                            if condUI['buttons']['text'][z].text == 'Done':
                                done = True
                                i += 1
                                if HPP and not blockmode:
                                    # Need to re-interpret condOrder into the right format.
                                    tempOut = []
                                    for b in range(0, round(len(condOrder)/3)):
                                        tmpDict = {}
                                        tmpDict['L'] = condOrder[b * 3]
                                        tmpDict['C'] = condOrder[b * 3 + 1]
                                        tmpDict['R'] = condOrder[b * 3 + 2]
                                        tempOut.append(tmpDict)
                                    outputDict[tempType] = tempOut
                                else:
                                    outputDict[tempType] = condOrder  # should be simple as that.
                            else:
                                done = True
                                i = len(labelList)
                            while self.mouse.isPressedIn(condUI['buttons']['shapes'][z], buttons=[0]):  # waits until the mouse is released before continuing.
                                pass

                    if HPP and not blockmode:
                        # If they click inside the flow, behavior is as before.
                        for k in range(0, len(condFlow['shapes'])):  # Rearrange or remove, as in the usual loop!
                            # Provided that the thing at this location is not 0
                            if self.mouse.isPressedIn(condFlow['shapes'][k], buttons=[0]) and condOrder[k] not in [0,'0']:
                                # TODO: Text in moveTrialInFlow shows up in an awkward spot
                                oldOrder = deepcopy(condOrder)
                                condOrder = self.moveTrialInFlow(k, condOrder, newFlowArea, condUI, condFlow,
                                                                 stims)
                                # Determine if something has been removed, if so update things appropriately
                                if len(condOrder) < len(oldOrder):
                                    # Determine what was removed
                                    wasEnd = True
                                    for q in range(0, len(condOrder)):
                                        if condOrder[q] != oldOrder[q]:
                                            condOrder.insert(q, 0)
                                            wasEnd = False
                                            break
                                    if wasEnd:
                                        condOrder.append(0)  # A special case for removing the very last thing in the flow
                                    # Examine each set of three, determine if all zeroes, remove if so.
                                    wipeList = []
                                    for s in range(0, round(len(condOrder)/3)):
                                        zeroCount = 0
                                        for t in range(0,3):
                                            if condOrder[s*3+t] in [0, '0']:
                                                zeroCount += 1
                                        if zeroCount == 3:
                                            wipeList.append(s*3)
                                    if len(wipeList) > 0:
                                        for u in range(0, len(wipeList)):
                                            del condOrder[wipeList[u]+2]
                                            del condOrder[wipeList[u]+1]
                                            del condOrder[wipeList[u]]

                                condFlow = self.loadFlow(tOrd=condOrder, space=newFlowArea, locs=newFlowLocs,
                                                         overflow=newFlowLocs, types=tempStims, trials=False,
                                                         conlines=blockmode)
                                break
                        # Drag and drop
                        for j in range(0, len(stims['shapes'])):  # Only need to worry about adding stim
                            if self.mouse.isPressedIn(stims['shapes'][j], buttons=[0]):
                                drag = self.mouse.getPressed()
                                dragShape = stims['shapes'][j]
                                dragText = stims['text'][j]
                                dragname = stims['labels'][j]
                                while drag[0]: # our drag and drop loop!
                                    self.showMainUI(condUI, condFlow, stims)
                                    # Draw the copy of the thing being dragged!
                                    curPos = self.mouse.getPos()
                                    dragShape.pos = curPos
                                    dragText.pos = dragShape.pos
                                    dragShape.draw()
                                    dragText.draw()
                                    self.win.flip()
                                    drag = self.mouse.getPressed()
                                finPos = self.mouse.getPos()
                                # Reset the position of the thing while adding it to the flow
                                stims = self.loadTypes(bigPaletteLocs, tempStims)
                                # Now we have to translate this position back into a place in the flow!
                                minDist = 2 # Maximum possible distance
                                closest = 0 # index of closest location
                                for loc in range(0, len(newFlowLocs)):
                                    tmpDist = self._distanceCalc(finPos, newFlowLocs[loc])
                                    if tmpDist < minDist:
                                        closest = deepcopy(loc)
                                        minDist = tmpDist
                                # now to see if that's a valid place and if so update accordingly!
                                if closest < len(condOrder):
                                    condOrder[closest] = dragname
                                elif closest < len(condOrder)+3:  # +3 to allow us to add to the next trial
                                    condOrder.append(0)
                                    condOrder.append(0)
                                    condOrder.append(0)
                                    condOrder[closest] = dragname
                                self.mouse.clickReset() # This just prevents the flow-click from tripping instantly, or should
                                condFlow = self.loadFlow(tOrd=condOrder, space=newFlowArea, locs=newFlowLocs,
                                                         overflow=newFlowLocs, types=tempStims, trials=False,
                                                         conlines=blockmode)
                    else:
                        # Click on a stimulus to add it. Remove it from the palette when added. Re-add it as appropriate.
                        for j in range(0, len(stims['shapes'])):  # Only need to worry about adding stim
                            if self.mouse.isPressedIn(stims['shapes'][j], buttons=[0]):
                                if stims['labels'][j] not in invisStims:
                                    condOrder.append(stims['labels'][j])
                                    condFlow = self.loadFlow(tOrd=condOrder, space=newFlowArea, locs=newFlowLocs,
                                                             overflow=newFlowLocs, types=tempStims, trials=False,
                                                             conlines=blockmode)
                                    invisStims.append(stims['labels'][j])

                                while self.mouse.isPressedIn(stims['shapes'][j], buttons=[0]):  # waits until the mouse is released before continuing.
                                    pass
                        for k in range(0, len(condFlow['shapes'])):  # Rearrange or remove, as in the usual loop!
                            if self.mouse.isPressedIn(condFlow['shapes'][k], buttons=[0]):
                                condOrder = self.moveTrialInFlow(k, condOrder, newFlowArea, condUI, condFlow,
                                                                  stims)
                                # Re-initialize the palette if something was deleted.
                                invisStims=[]
                                for q in range(0, len(tempStims)):
                                    if tempStims[q] in condOrder:
                                        invisStims.append(tempStims[q])

                                condFlow = self.loadFlow(tOrd=condOrder, space=newFlowArea, locs=newFlowLocs,
                                                         overflow=newFlowLocs, types=tempStims, trials=False,
                                                         conlines=blockmode)
                                break
                        stims = self.loadTypes(bigPaletteLocs, tempStims)  # update the palette.
                        for n in range(0, len(invisStims)):
                            invisdex = stims['labels'].index(invisStims[n])
                            # Can't delete it outright, but can make it not render and non-interactible elsewhere.
                            stims['shapes'][invisdex].fillColor = 'white'
                            stims['shapes'][invisdex].lineColor = 'white'


            # Finally, rewrite everything that needs rewriting.
            # This includes making sure that blocks or trial types, whichever were left blank, are not left blank.
            listAll = list(self.settings['stimNames'].keys()) + list(self.settings['blockList'].keys())
            for q in listAll:
                if q not in outputDict.keys() and not ex:
                    if q in self.settings['blockList'].keys():
                        outputDict[q] = self.settings['blockList'][q]['trialList']
                    elif q in self.settings['stimNames'].keys():
                        outputDict[q] = self.settings['stimNames'][q]
                elif q not in outputDict.keys():  # Implied: ex == True
                    outputDict[q] = self.condDict[cond][q]
            self.condDict[cond] = outputDict
            if not ex:
                self.settings['condList'].append(str(cond))


    def _distanceCalc(self, pos1, pos2):
        """
        A simple function for computing distance between two points

        :param pos1: X,Y location 1
        :type pos1: list
        :param pos2: X,Y location 2
        :type pos2: list
        :return: Distance
        :rtype: float
        """
        x1 = pos1[0]
        x2 = pos2[0]
        y1 = pos1[1]
        y2 = pos2[1]
        dist = sqrt((x1-x2)**2 + (y1-y2)**2)
        return dist


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
                    counterDict[k] = len(l['trialList'])
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
                template[i] = deepcopy(self.settings['blockList'][i]['trialList'])
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
                    j[y] = self.settings['blockList'][y]['trialList']
                elif y in self.settings['stimNames'].keys():
                    j[y] = self.settings['stimNames'][y]

        self.condDict = deepcopy(outputDict)
        self.settings['condList'] = list(outputDict.keys())


    def condRandomizer(self, bcReset=False):
        """
        This is based on other scripts I've made. Basically, say you have four conditions, and you want four participants
        to be assigned to each one, but you want to be totally blind to which condition a given participant is in. Here,
        once you have made your four conditions, you can tell it to create a condition list that it never shows you that
        has each condition X times, and that becomes the new condition file/list/etc.

        :param bcReset: For the edge case where someone re-loads the base conditions and wants to re-randomize them.
        :type bcReset: bool

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
            # However, we need a safety in case the cond list has been randomized once, so we only randomize the
            # base conditions and not re-randomize the old list. In that case, we essentially force revert the
            # old randomized conditions to the base conditions.
            if not bcReset:
                self.baseCondDict = deepcopy(self.condDict)
                self.settings['baseCondList'] = deepcopy(self.settings['condList'])
            else:
                self.condDict = deepcopy(self.baseCondDict)  # because this is what the randomizer will pull from
                self.settings['condList'] = deepcopy(self.settings['baseCondList']) # as above.
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
   
   
    def habSettingsDlg(self, trialList, lastSet, redo=False): #Habituation criteria
        """
        Dialog for settings relating to habituation criteria:

        0 = habituation (Active/not active)

        1 = maxHabTrials (maximum possible hab trials if criterion not met)

        2 = setCritWindow (# trials summed over when creating criterion)

        3 = setCritDivisor (denominator of criterion calculation . e.g., sum of first 3 trials
            divided by 2 would have 3 for setCritWindow and 2 for this.)

        4 = setCritType (peak window, max trials, first N, last N, or first N above threshold)

        5 = habThresh (threshold for N above threshold)

        6 = metCritWindow (# trials summed over when evaluating whether criterion has been met)

        7 = metCritDivisor (denominator of sum calculated when determining if criterion has been met)

        8 = metCritStatic (static or moving window?)

        9 = habByDuration (habituation by duration or by on-time)

        10-N = Which trials to calculate hab over for multi-trial blocks.

        :param trialList: List of available trials in the block, since this follows from block settings.
        :type trialList: list
        :param lastSet: If information entered is invalid and the dialog needs to be shown again, this allows it to remember what was previously entered. Also pulls from existing block settings.
        :type lastSet: dict
        :param redo: Checking if redoing last setting
        :type redo: boolean
        :return: A dictionary of settings fed back into the block-maker UI.
        :rtype: dict
        """

        hDlg = gui.Dlg(title="Habituation block settings")
        windowtypes = ['First', 'Peak', 'Max', 'Last', 'Threshold']
        winchz = [x for x in windowtypes if x != lastSet['setCritType']]
        winchz.insert(0, lastSet['setCritType'])
        if lastSet['metCritStatic'] == 'Fixed':
            evalChz = ['Fixed', 'Moving']
        else:
            evalChz = ['Moving', 'Fixed']

        if lastSet['habByDuration'] in ['1',1,'True',True]:
            byDur = True
        else:
            byDur = False

        hDlg.addField("Habituation on/off (uncheck to turn off)", True) # Always defaults to true if you open this menu.
        hDlg.addField("Max number of habituation trials (if criterion not met)", lastSet['maxHabTrials'])
        hDlg.addField("Number of trials to sum looking time over when making hab criterion", lastSet['setCritWindow'])
        hDlg.addField("Number to divide sum of looking time by when computing criterion", lastSet['setCritDivisor'])
        hDlg.addField("Criterion window First trials, first trials above Threshold, dynamic Peak contiguous window, or the set of hab trials with Max looking time?", choices=winchz)
        hDlg.addField("Threshold value to use if 'Threshold' selected above (ignored otherwise)", lastSet['habThresh'])
        hDlg.addField("Number of trials to sum looking time over when determining whether criterion has been met", lastSet['metCritWindow'])
        hDlg.addField("Number to divide sum of looking time by when determining whether criterion has been met", lastSet['metCritDivisor'])
        hDlg.addField("Evaluate criterion over moving window or fixed windows?", choices=evalChz)
        hDlg.addField("Compute habituation over total trial duration instead of on-time?", byDur)
        if len(trialList) > 1: # If there's only one trial, then it's automatically that trial!
            hDlg.addText("Check which trial types criteria should be computed over (both setting and checking)")
            expandedHabList = []
            for q in range(0, len(trialList)):
                if trialList[q] in self.settings['blockList'].keys():
                    doneBlock = False
                    listThings = []
                    listBlocks = [] # A list of all blocks that need to go into the thing.
                    blockType = trialList[q]
                    prfx = blockType + '.'
                    while not doneBlock:
                        for i in self.settings['blockList'][blockType]['trialList']:
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
                        if listThings[z] in lastSet['calcHabOver']:
                            chk = True
                        else:
                            chk = False
                        hDlg.addField(listThings[z], initial=chk)
                        expandedHabList.append(listThings[z])
                else:
                    if trialList[q] in lastSet['calcHabOver']:
                        chk = True
                    else:
                        chk = False
                    hDlg.addField(trialList[q], initial=chk)
                    expandedHabList.append(trialList[q])
        habDat=hDlg.show()
        if hDlg.OK:
            skip = False
            intevals = [1,2,6]
            fevals = [3,5,7] # These can be floats
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

            if not skip:
                newHabSettings = {}
                newHabSettings['habituation'] = habDat[0]
                newHabSettings['maxHabTrials'] = habDat[1]
                newHabSettings['setCritWindow'] = habDat[2]
                newHabSettings['setCritDivisor'] = habDat[3]
                newHabSettings['setCritType'] = habDat[4]
                newHabSettings['habThresh'] = habDat[5]
                newHabSettings['metCritWindow'] = habDat[6]
                newHabSettings['metCritDivisor'] = habDat[7]
                newHabSettings['metCritStatic'] = habDat[8]
                if habDat[9] in [1, '1', True, 'True']:
                    newHabSettings['habByDuration'] = 1
                else:
                    newHabSettings['habByDuration'] = 0

                if len(trialList) > 1:
                    tempArr = []
                    for i in range(0, len(expandedHabList)):
                        if habDat[i+10]:
                           tempArr.append(expandedHabList[i])
                    if len(tempArr) > 0:
                        newHabSettings['calcHabOver'] = tempArr
                    else:
                        errDlg = gui.Dlg(title="Warning, no trial types selected!")
                        errDlg.addText("You must select at least one trial to calculate habituation over!")
                        errDlg.show()
                        return self.habSettingsDlg(trialList, newHabSettings, redo=True)
                else: # If there's only one trial in the block then that's the hab trial!
                    newHabSettings['calcHabOver'] = trialList[0]
                return newHabSettings
            else:
                errDlg = gui.Dlg(title="Warning, invalid number!")
                errDlg.addText(
                    "Please make sure all values are valid numbers. Remember that any 'number of trials' field must be a whole number (no decimal).")
                errDlg.show()
                lastSetDat = {}
                lastSetDat['habituation'] = habDat[0]
                lastSetDat['maxHabTrials'] = habDat[1]
                lastSetDat['setCritWindow'] = habDat[2]
                lastSetDat['setCritDivisor'] = habDat[3]
                lastSetDat['setCritType'] = habDat[4]
                lastSetDat['habThresh'] = habDat[5]
                lastSetDat['metCritWindow'] = habDat[6]
                lastSetDat['metCritDivisor'] = habDat[7]
                lastSetDat['metCritStatic'] = habDat[8]
                if habDat[9] in [1, '1', True, 'True']:
                    lastSetDat['habByDuration'] = 1
                else:
                    lastSetDat['habByDuration'] = 0

                if len(trialList) > 1:
                    tempArr = []
                    for i in range(0, len(expandedHabList)):
                        if habDat[i+10]:
                           tempArr.append(expandedHabList[i])
                    if len(tempArr) > 0:
                        lastSetDat['calcHabOver'] = tempArr

                return self.habSettingsDlg(trialList, lastSetDat, redo=True)



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
        elif self.settings['prefLook'] in [2, '2'] and self.settings['randPres'] in [0, '0', False, 'False']:
            warnDlg = gui.Dlg("Warning: HPP without conditions!")
            warnDlg.addText("No conditions in HPP experiment! All stimuli will appear on center screen")
            warnDlg.addText("Hit 'OK' to save anyways (you can add conditions later and save then) or cancel to go back.")
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

        todo: Add psychopy_tobii_infant to this. Saved in the code folder.

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
                self.settings['baseCondFile'] = 'base_'+self.settings['condFile']
                with open(self.folderPath+self.settings['baseCondFile'],'w') as bc:
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
                        elif r['stimType'] == 'Image with audio':  # Here we have to look at the file paths themselves
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
                    # Edge case: Multiple attngetters using the same audio file, so it doesn't  need re-copying, but the path does need to be updated.
                    elif j['stimLoc'] != 'stimuli' + self.dirMarker + 'attnGetters' + self.dirMarker + j['stimName']:
                        j['stimLoc'] = 'stimuli' + self.dirMarker + 'attnGetters' + self.dirMarker + j['stimName']
                    if 'audioName' in j.keys():
                        if not os.path.exists(targPath + j['audioName']):
                            shutil.copyfile(j['audioLoc'], targPath + j['audioName'])
                            j['audioLoc'] = 'stimuli' + self.dirMarker + 'attnGetters' + self.dirMarker + j['audioName']
                        elif j['audioLoc'] != 'stimuli' + self.dirMarker + 'attnGetters' + self.dirMarker + j['audioName']:
                            j['audioLoc'] = 'stimuli' + self.dirMarker + 'attnGetters' + self.dirMarker + j['audioName']
                except:
                    success = False
                    print('Could not copy attention-getter file ' + j['stimLoc'] + ' to location ' +  targPath + '. Make sure both exist!')

        # todo: Customizable calibration images, calibration process.
        calibImgPath = 'calib'
        calibImgTarg = stimPath+calibImgPath
        if not os.path.exists(calibImgTarg):
            try:
                shutil.copytree(srcDir+calibImgPath, calibImgTarg)
            except:
                success = False
                print('Could not copy calibration images folder')
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
        classHPPPath = 'PyHabClassHPP.py'
        classHPPTarg = codePath+classHPPPath
        buildPath = 'PyHabBuilder.py'
        buildTarg = codePath+buildPath
        initPath = '__init__.py'
        initTarg = codePath+initPath

        tobiiPath = 'psychopy_tobii_infant'
        tobiiTarg = codePath+tobiiPath

        try:
            if not os.path.exists(classTarg):
                shutil.copyfile(srcDir+classPath, classTarg)
            if not os.path.exists(classPLTarg):
                shutil.copyfile(srcDir+classPLPath, classPLTarg)
            if not os.path.exists(classHPPTarg):
                shutil.copyfile(srcDir + classHPPPath, classHPPTarg)
            if not os.path.exists(buildTarg):
                shutil.copyfile(srcDir+buildPath, buildTarg)
            if not os.path.exists(initTarg):
                shutil.copyfile(srcDir+initPath, initTarg)
            if not os.path.exists(tobiiTarg):
                shutil.copytree(srcDir+tobiiPath, tobiiTarg)

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
                # Open file and find the line that sets the path to the settings file, update it appropriately
                with open(launcherSource,'r') as file:
                    launcherFile = file.readlines()
                newLine = 'setName = \"' + self.settings['prefix']+'Settings.csv\"\r\n'  # Simplified, so it always runs the settings file in that folder.
                for i in range(0, 20): # An inelegant solution but one flexible enough to find the right line to overwrite
                    if launcherFile[i][0:7] == 'setName':
                        targetLine = i
                        break
                launcherFile[targetLine] = newLine
                launcherFile[targetLine+1] = "#Created in PsychoPy version " + __version__ + "\r\n"
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
