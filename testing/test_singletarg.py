import pytest
import os, sys, copy, time, mock
from psychopy import event

sys.path.insert(0,os.getcwd())

from PyHab import PyHabClass as PH
"""
TODO: FIGURE OUT HOW TO TEST SCREEN AND STUDY FLOW ISSUES. Loops that wait for input may be unstoppable.
That may entail rewriting certain things so that they are modularized functions tripped by key-presses rather than
the big honkers that make up doExperiment and doTrial right now.    
"""

base_settings = {'dataColumns': "['sNum', 'months', 'days', 'sex', 'cond','condLabel', 'trial','GNG','trialType','stimName','habCrit','sumOnA','numOnA','sumOffA','numOffA','sumOnB','numOnB','sumOffB','numOffB']",
                                                        'prefix': 'PyHabExperiment',
                                                        'dataloc':'data/',
                                                        'maxDur': "{'A':60.0,'B':20.0,'C':60.0,'D':60.0}",
                                                        'playThrough': "{'A':0,'B':2,'C':1,'D':1 }",
                                                        'movieEnd': "['D']",
                                                        'maxOff': "{'A':2.0,'B':1.0,'C':5.0,'D':10.0}",
                                                        'minOn': "{'A':1.0,'B':1.0,'C':6.0,'D':8.0}",
                                                        'blindPres': '0',
                                                        'autoAdvance': "['D']",
                                                        'randPres': '0',
                                                        'condPath': '',
                                                        'condFile': '',
                                                        'condList': "[]",
                                                        'trialOrder': "[]",
                                                        'maxHabTrials': '14',
                                                        'setCritWindow': '3',
                                                        'setCritDivisor': '2',
                                                        'setCritType': 'First',
                                                        'metCritWindow': '3',
                                                        'metCritDivisor': '1',
                                                        'metCritStatic': 'Moving',
                                                        'habTrialList':"[]",
                                                        'stimPres': '0',  #Will be set on each run anyways.
                                                        'stimPath': 'stimuli/',
                                                        'stimNames': "{}",
                                                        'stimList': "{}",
                                                        'screenWidth': '1080',
                                                        'screenHeight': '700',
                                                        'screenColor': 'black',
                                                        'movieWidth': '800',
                                                        'movieHeight': '600',
                                                        'screenIndex': '1',
                                                        'ISI': '0.0',
                                                        'freezeFrame': '0.0',
                                                        'playAttnGetter': "{'A':'PyHabDefault','B':'PyHabDefault'}",
                                                        'attnGetterList':"{'PyHabDefault':{'stimType':'Audio','stimName':'upchime1.wav','stimDur':2,'stimLoc':'PyHab/upchime1.wav','shape':'Rectangle','color':'yellow'}}",
                                                        'folderPath':'',
                                                        'trialTypes':"['A','B','C','D']",
                                                        'prefLook':'0'}

def test_init():
    """
    Tests initialization, makes sure everything is being read in as the correct types.

    :return:
    :rtype:
    """
    itest = PH.PyHab(base_settings)
    TheDicts = [itest.maxDur, itest.playThrough, itest.maxOff, itest.minOn, itest.stimNames,
                itest.stimList, itest.playAttnGetter, itest.attnGetterList]
    TheLists = [itest.dataColumns, itest.movieEnd, itest.autoAdvance, itest.condList, itest.trialOrder,
                itest.habTrialList]
    TheStrings = [itest.prefix, itest.dataFolder, itest.stimPath,itest.condFile, itest.setCritType, itest.metCritStatic,
                  itest.screenColor]
    TheFloats = [itest.ISI, itest.freezeFrame]
    TheInts = [itest.blindPres, itest.maxHabTrials, itest.setCritWindow, itest.setCritDivisor, itest.metCritDivisor,
               itest.metCritWindow, itest.screenWidth, itest.screenHeight,itest.movieWidth, itest.movieHeight]
    for i in TheDicts:
        assert type(i) == dict
    for j in TheLists:
        assert type(j) == list
    for k in TheStrings:
        assert type(k) == str
    for l in TheFloats:
        assert type(l) == float
    for m in TheInts:
        assert type(m) == int

    del itest

class TestDataFunc(object):
    """
    Tests functions that modify data (abortTrial, redoTrial, checkStop, dataRec), using a fake data array
    :return:
    :rtype:
    """
    def setup_class(self):
        self.dataInst = PH.PyHab(base_settings)
        # Set values for things that are usually set in the experimenter dialog
        self.dataInst.sNum = 99
        self.dataInst.ageMo = 5
        self.dataInst.ageDay = 15
        self.dataInst.sex = 'm'
        self.dataInst.cond = 'dataTest'
        self.dataInst.condLabel = 'dataTest'
        # Create base mock data structures to tinker with
        self.trialVOn1 = [{'trial':1, 'trialType':'A', 'startTime':0, 'endTime':1.5, 'duration':1.5},
                     {'trial': 1, 'trialType': 'A', 'startTime': 3.0, 'endTime': 4.5, 'duration': 1.5}] # VerboseOn1
        self.trialVOff1 = [{'trial':1, 'trialType':'A', 'startTime':1.5, 'endTime':3.0, 'duration':1.5},
                      {'trial': 1, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5, 'duration': 2.0}]  # VerboseOff1
        self.trialVOn2 = [{'trial':1, 'trialType':'A', 'startTime':0, 'endTime':1.5, 'duration':1.5},
                     {'trial': 1, 'trialType': 'A', 'startTime': 3.0, 'endTime': 4.5, 'duration': 1.5}]  # VerboseOn2
        self.trialVOff2 = [{'trial':1, 'trialType':'A', 'startTime':1.5, 'endtTime':3.0, 'duration':1.5},
                      {'trial': 1, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5, 'duration': 2.0}] # VerboseOff2
        self.testMatrix = [{'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                    'condLabel': 'dataTest', 'trial': 1, 'GNG': 1, 'trialType': 'A', 'stimName': 'movie1.mov',
                    'habCrit': 0, 'sumOnA': 3.0, 'numOnA': 2, 'sumOffA': 3.5,
                    'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                    'numOffB': 2}, {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                    'condLabel': 'dataTest', 'trial': 2, 'GNG': 1, 'trialType': 'B', 'stimName': 'movie2.mov',
                    'habCrit': 0, 'sumOnA': 3.0, 'numOnA': 2, 'sumOffA': 3.5,
                    'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                    'numOffB': 2}]

    def teardown_class(self):
        del self.dataInst
        del self.trialVOn1
        del self.trialVOff1
        del self.trialVOn2
        del self.trialVOff2
        del self.testMatrix

    def test_abort(self):

        self.dataInst.abortTrial(self.trialVOn1, self.trialVOff2, 1, 'A', self.trialVOn2, self.trialVOff2, 'movie1.mov')

        assert self.dataInst.badTrials[0]['trial'] == self.trialVOn1[0]['trial']
        assert self.dataInst.badTrials[0]['trialType'] == self.trialVOn1[0]['trialType']
        assert self.dataInst.badTrials[0]['GNG'] == 0
        assert self.dataInst.badTrials[0]['habCrit'] == 0
        assert self.dataInst.badTrials[0]['sumOnA'] == self.trialVOn1[0]['duration']+self.trialVOn1[1]['duration']
        assert self.dataInst.badTrials[0]['sumOffA'] == self.trialVOff1[0]['duration']+self.trialVOff1[1]['duration']
        assert self.dataInst.badTrials[0]['numOnA'] == len(self.trialVOn1)
        assert self.dataInst.badTrials[0]['numOffA'] == len(self.trialVOff1)
        assert self.dataInst.badTrials[0]['sumOnB'] == self.trialVOn2[0]['duration'] + self.trialVOn2[1]['duration']
        assert self.dataInst.badTrials[0]['sumOffB'] == self.trialVOff2[0]['duration'] + self.trialVOff2[1]['duration']
        assert self.dataInst.badTrials[0]['numOnB'] == len(self.trialVOn2)
        assert self.dataInst.badTrials[0]['numOffB'] == len(self.trialVOff2)

    def test_redo(self):
        tempMatrix = copy.deepcopy(self.testMatrix)
        self.dataInst.dataMatrix = copy.deepcopy(self.testMatrix)
        self.dataInst.badTrials = [] # It doesn't teardown until ALL of the functions have been run so we have to reset it

        self.dataInst.redoTrial(2)

        assert len(self.dataInst.dataMatrix) == 1
        assert self.dataInst.dataMatrix[0] == tempMatrix[0]
        tempMatrix[1]['GNG'] = 0
        assert len(self.dataInst.badTrials) == 1
        assert self.dataInst.badTrials[0] == tempMatrix[1]

    def test_datarec(self):
        self.dataInst.dataMatrix=[]
        self.dataInst.badTrials=[]

        self.dataInst.dataRec(self.trialVOn1, self.trialVOff2, 1, 'A', self.trialVOn2, self.trialVOff2, 'movie1.mov')

        assert len(self.dataInst.dataMatrix) == 1
        assert self.dataInst.dataMatrix[0] == self.testMatrix[0]
        assert len(self.dataInst.badTrials) == 0

    def test_checkstop(self):
        """
        This one's a little trickier than the others because it requires creating fake hab data and testing all of the
        different modes!
        Default settings: Set first 3, divisor 2. Test moving window, 3, divisor 1. Maxhab 14
        :return:
        :rtype:
        """
        habMatrix = copy.deepcopy(self.testMatrix)
        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                    'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                    'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                    'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                    'numOffB': 2})
        self.dataInst.dataMatrix = habMatrix # We can actually use python's pointer thing to our advantage here: dataMatrix will update with habMatrix
        self.dataInst.badTrials = []
        self.dataInst.stimPres = True  # Temporary, so it doesn't try to play the end-hab sound.

        self.dataInst.habCount = 1
        assert self.dataInst.checkStop() == False
        assert self.dataInst.habCrit == 0

        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                    'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                    'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                    'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                    'numOffB': 2})

        self.dataInst.habCount = 2
        assert self.dataInst.checkStop() == False
        assert self.dataInst.habCrit == 0

        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 5, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})

        self.dataInst.habCount = 3
        assert self.dataInst.habCrit == 0
        assert self.dataInst.checkStop() == False
        assert self.dataInst.habCrit == 15.0 # Check criteria set properly

        self.dataInst.habCount = 14
        assert self.dataInst.checkStop() == True

        self.dataInst.habCount = 3
        self.dataInst.habCrit = 0 # reset.
        self.dataInst.setCritDivisor = 1
        assert self.dataInst.checkStop() == False
        assert self.dataInst.habCrit == 30.0
        self.dataInst.habCrit = 0 # reset
        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 6, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})
        self.dataInst.habCount += 1
        self.dataInst.setCritWindow = 4
        assert self.dataInst.checkStop() == False
        assert self.dataInst.habCrit == 40.0

        self.dataInst.setCritWindow = 3
        self.dataInst.setCritType = 'Peak' #require actualTrialOrder
        self.dataInst.actualTrialOrder = ['A','B']
        for i in range(0,14):
            self.dataInst.actualTrialOrder.append('Hab')
        self.dataInst.actualTrialOrder.append('Test')
        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 7, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})
        self.dataInst.habCount += 1
        assert self.dataInst.checkStop() == False
        assert self.dataInst.habCrit == 40.0 # should not change yet

        habMatrix[6]['sumOnA'] = 25.0
        assert self.dataInst.checkStop() == False
        assert self.dataInst.habCrit == 45.0  # should change to peak now

        self.dataInst.setCritType = 'Max'
        habMatrix[3]['sumOnA'] = 15.0 # 25+15+10=50
        assert self.dataInst.checkStop() == False
        assert self.dataInst.habCrit == 50.0  # should change to max now

        habMatrix[2]['sumOnA'] = 15.0  # 25+15+15=55
        assert self.dataInst.checkStop() == False
        assert self.dataInst.habCrit == 55.0  # should change to max now

        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 8, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2}) # At this point, most recent 3 should be 25+10+5=40

        self.dataInst.habCount += 1 # 6
        assert self.dataInst.checkStop() == True
        assert self.dataInst.habCrit == 55.0  # should not have changed.

        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 9, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})

        self.dataInst.habCount += 1 # 7

        self.dataInst.metCritWindow = 4 # 25+10+5+10 = 50
        assert self.dataInst.checkStop() == True
        assert self.dataInst.habCrit == 55.0  # should not have changed.

        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 10, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 5.1, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})

        self.dataInst.habCount += 1  # 8
        self.dataInst.metCritWindow = 5  # 25+10+5+10+5.1  = 55.1
        assert self.dataInst.habCrit == 55.0  # should not have changed.
        assert self.dataInst.checkStop() == False

        self.dataInst.metCritDivisor = 2
        assert self.dataInst.checkStop() == True
        assert self.dataInst.habCrit == 55.0  # should not have changed.

        self.dataInst.metCritWindow = 4
        self.dataInst.metCritStatic = 'Fixed' # Should not trip this time b/c setcritwindow is 3 + 4 = 7
        assert self.dataInst.checkStop() == False
        assert self.dataInst.habCrit == 55.0  # should not have changed.

        self.dataInst.metCritWindow = 5 # Now it should trip
        assert self.dataInst.checkStop() == True
        assert self.dataInst.habCrit == 55.0  # should not have changed.


class TestRunSetup(object):
    """
    Tests initialization functions that build the trial order and read participant info, calculate age, etc.
    """
    def setup_class(self):
        trial_settings = copy.deepcopy(base_settings)
        trial_settings['trialOrder'] = "['A','A','B','B','C','C','D']"

        self.trialInst = PH.PyHab(trial_settings)



    def teardown_class(self):
        del self.trialInst

    def test_setup(self):
        testOne = [99, 'Test', 'NB', 7, 2, 18, 'testcond', 8, 2, 18]

        self.trialInst.run(testMode=testOne)

        assert self.trialInst.actualTrialOrder == ['A','A','B','B','C','C','D']
        assert self.trialInst.ageMo == 1
        assert self.trialInst.ageDay == 0


    def test_hab_expansion(self):
        testOne = [99, 'Test', 'NB', 7, 2, 18, 'testcond', 8, 2, 18]
        self.trialInst.trialOrder = ['A','A','B','B','Hab','D']
        self.trialInst.run(testMode=testOne)
        assert len(self.trialInst.actualTrialOrder) == 19
        assert len([x for x in self.trialInst.actualTrialOrder if x == 'Hab']) == 14

    def test_multiyear_age(self):
        testOne = [99, 'Test', 'NB', 7, 2, 16, 'testcond', 8, 2, 18]
        self.trialInst.run(testMode=testOne)

        assert self.trialInst.ageMo == 25
        assert self.trialInst.ageDay == 0

        testTwo = [99, 'Test', 'NB', 7, 2, 16, 'testcond', 8, 1, 18]
        self.trialInst.run(testMode=testTwo)

        assert self.trialInst.ageMo == 24
        assert self.trialInst.ageDay == 30

    def test_condition_files(self):
        """
        To test condition files requires a condition file. The demo is handy here.
        :return:
        :rtype:
        """
        self.trialInst.condFile = 'PyHabDemo/conditions.csv'
        self.trialInst.stimNames = {'Intro':['Movie1','Movie2','Movie3','Movie4'], 'Fam':['Movie5', 'Movie6', 'Movie7', 'Movie8'],
                                    'Test':['Movie1','Movie2','Movie3','Movie4']}
        self.trialInst.trialOrder = ['Intro','Fam','Test']
        self.trialInst.randPres = True
        self.trialInst.stimPres = True

        testTwo = [99, 'Test', 'NB', 7, 2, 16, 'A'] # corresponds to {Intro:[1,2], Fam:[1,2], Test:[1,2]}
        self.trialInst.run(testMode=testTwo)

        #First make sure it won't go without condlist
        assert self.trialInst.stimNames['Intro'] == ['Movie1', 'Movie2', 'Movie3', 'Movie4']
        self.trialInst.condList=['A','B','C','D']
        self.trialInst.run(testMode=testTwo)

        assert self.trialInst.stimNames['Intro'] == ['Movie1','Movie2']
        assert self.trialInst.stimNames['Fam'] == ['Movie5', 'Movie6']
        assert self.trialInst.stimNames['Test'] == ['Movie1','Movie2']


