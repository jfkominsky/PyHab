import pytest
import os, sys, copy, time, mock
from psychopy import event

sys.path.insert(0, os.getcwd())

from PyHab import PyHabClass as PH
from PyHab import PyHabClassPL as PHL

"""
 
"""

base_settings = {
    'dataColumns': "['sNum', 'months', 'days', 'sex', 'cond','condLabel', 'trial','GNG','trialType','stimName','habCrit','sumOnA','numOnA','sumOffA','numOffA','sumOnB','numOnB','sumOffB','numOffB']",
    'prefix': 'PyHabExperiment',
    'dataloc': 'data/',
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
    'habTrialList': "[]",
    'stimPres': '0',  # Will be set on each run anyways.
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
    'attnGetterList': "{'PyHabDefault':{'stimType':'Audio','stimName':'upchime1.wav','stimDur':2,'stimLoc':'PyHab/upchime1.wav','shape':'Rectangle','color':'yellow'}}",
    'folderPath': '',
    'trialTypes': "['A','B','C','D']",
    'prefLook': '0'}


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
    TheStrings = [itest.prefix, itest.dataFolder, itest.stimPath, itest.condFile, itest.setCritType,
                  itest.metCritStatic,
                  itest.screenColor]
    TheFloats = [itest.ISI, itest.freezeFrame]
    TheInts = [itest.blindPres, itest.maxHabTrials, itest.setCritWindow, itest.setCritDivisor, itest.metCritDivisor,
               itest.metCritWindow, itest.screenWidth, itest.screenHeight, itest.movieWidth, itest.movieHeight]
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
        self.trialVOn1 = [{'trial': 1, 'trialType': 'A', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                          {'trial': 1, 'trialType': 'A', 'startTime': 3.0, 'endTime': 4.5,
                           'duration': 1.5}]  # VerboseOn1
        self.trialVOff1 = [{'trial': 1, 'trialType': 'A', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                           {'trial': 1, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5,
                            'duration': 2.0}]  # VerboseOff1
        self.trialVOn2 = [{'trial': 1, 'trialType': 'A', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                          {'trial': 1, 'trialType': 'A', 'startTime': 3.0, 'endTime': 4.5,
                           'duration': 1.5}]  # VerboseOn2
        self.trialVOff2 = [{'trial': 1, 'trialType': 'A', 'startTime': 1.5, 'endtTime': 3.0, 'duration': 1.5},
                           {'trial': 1, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5,
                            'duration': 2.0}]  # VerboseOff2
        self.testMatrix = [{'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                            'condLabel': 'dataTest', 'trial': 1, 'GNG': 1, 'trialType': 'A', 'stimName': 'movie1.mov',
                            'habCrit': 0, 'sumOnA': 3.0, 'numOnA': 2, 'sumOffA': 3.5,
                            'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                            'numOffB': 2}, {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                            'condLabel': 'dataTest', 'trial': 2, 'GNG': 1, 'trialType': 'B',
                                            'stimName': 'movie2.mov',
                                            'habCrit': 0, 'sumOnA': 3.0, 'numOnA': 2, 'sumOffA': 3.5,
                                            'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                                            'numOffB': 2}]
        self.testDatList = {'verboseOn': [{'trial': 1, 'trialType': 'A', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                           {'trial': 1, 'trialType': 'A', 'startTime': 3.0, 'endTime': 4.5, 'duration': 1.5},
                           {'trial': 2, 'trialType': 'A', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                           {'trial': 2, 'trialType': 'A', 'startTime': 3.0, 'endTime': 4.5, 'duration': 1.5}],
             'verboseOff': [{'trial': 1, 'trialType': 'A', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                            {'trial': 1, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5, 'duration': 2.0},
                            {'trial': 2, 'trialType': 'A', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                            {'trial': 2, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5, 'duration': 2.0}],
             'verboseOn2':[{'trial': 1, 'trialType': 'A', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                           {'trial': 1, 'trialType': 'A', 'startTime': 3.0, 'endTime': 4.5, 'duration': 1.5},
                           {'trial': 2, 'trialType': 'A', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                           {'trial': 2, 'trialType': 'A', 'startTime': 3.0, 'endTime': 4.5, 'duration': 1.5}],
             'verboseOff2':[{'trial': 1, 'trialType': 'A', 'startTime': 1.5, 'endtTime': 3.0, 'duration': 1.5},
                           {'trial': 1, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5, 'duration': 2.0},
                           {'trial': 2, 'trialType': 'A', 'startTime': 1.5, 'endtTime': 3.0, 'duration': 1.5},
                           {'trial': 2, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5, 'duration': 2.0}]}

    def teardown_class(self):
        del self.dataInst
        del self.trialVOn1
        del self.trialVOff1
        del self.trialVOn2
        del self.trialVOff2
        del self.testMatrix

    def test_abort(self):
        self.dataInst.abortTrial(self.trialVOn1, self.trialVOff1, 1, 'A', self.trialVOn2, self.trialVOff2, 'movie1.mov')

        assert self.dataInst.badTrials[0]['trial'] == self.trialVOn1[0]['trial']
        assert self.dataInst.badTrials[0]['trialType'] == self.trialVOn1[0]['trialType']
        assert self.dataInst.badTrials[0]['GNG'] == 0
        assert self.dataInst.badTrials[0]['habCrit'] == 0
        assert self.dataInst.badTrials[0]['sumOnA'] == self.trialVOn1[0]['duration'] + self.trialVOn1[1]['duration']
        assert self.dataInst.badTrials[0]['sumOffA'] == self.trialVOff1[0]['duration'] + self.trialVOff1[1]['duration']
        assert self.dataInst.badTrials[0]['numOnA'] == len(self.trialVOn1)
        assert self.dataInst.badTrials[0]['numOffA'] == len(self.trialVOff1)
        assert self.dataInst.badTrials[0]['sumOnB'] == self.trialVOn2[0]['duration'] + self.trialVOn2[1]['duration']
        assert self.dataInst.badTrials[0]['sumOffB'] == self.trialVOff2[0]['duration'] + self.trialVOff2[1]['duration']
        assert self.dataInst.badTrials[0]['numOnB'] == len(self.trialVOn2)
        assert self.dataInst.badTrials[0]['numOffB'] == len(self.trialVOff2)

    def test_redo(self):
        tempMatrix = copy.deepcopy(self.testMatrix)
        tempDat = copy.deepcopy(self.testDatList)
        self.dataInst.dataMatrix = copy.deepcopy(self.testMatrix)
        self.dataInst.verbDatList = copy.deepcopy(self.testDatList)
        self.dataInst.badTrials = []  # It doesn't teardown until ALL of the functions have been run so we have to reset it
        self.dataInst.verbBadList = {'verboseOn':[], 'verboseOff':[], 'verboseOn2':[], 'verboseOff2':[]}

        self.dataInst.redoTrial(2)

        assert len(self.dataInst.dataMatrix) == 1
        assert self.dataInst.dataMatrix[0] == tempMatrix[0]
        tempMatrix[1]['GNG'] = 0
        assert len(self.dataInst.badTrials) == 1
        assert self.dataInst.badTrials[0] == tempMatrix[1]
        for i in range(0, 2):
            assert self.dataInst.verbBadList['verboseOn'][i] == tempDat['verboseOn'][i+2]
            assert self.dataInst.verbBadList['verboseOff'][i] == tempDat['verboseOff'][i+2]
            assert self.dataInst.verbBadList['verboseOn2'][i] == tempDat['verboseOn2'][i+2]
            assert self.dataInst.verbBadList['verboseOff2'][i] == tempDat['verboseOff2'][i+2]
            assert self.dataInst.verbDatList['verboseOn'][i] == tempDat['verboseOn'][i]
            assert self.dataInst.verbDatList['verboseOff'][i] == tempDat['verboseOff'][i]
            assert self.dataInst.verbDatList['verboseOn2'][i] == tempDat['verboseOn2'][i]
            assert self.dataInst.verbDatList['verboseOff2'][i] == tempDat['verboseOff2'][i]
        for j,k in self.dataInst.verbDatList.items():
            assert len(k) == 2


    def test_datarec(self):
        self.dataInst.dataMatrix = []
        self.dataInst.badTrials = []

        self.dataInst.dataRec(self.trialVOn1, self.trialVOff1, 1, 'A', self.trialVOn2, self.trialVOff2, 'movie1.mov')

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
        self.dataInst.dataMatrix = habMatrix  # We can actually use python's pointer thing to our advantage here: dataMatrix will update with habMatrix
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
        assert self.dataInst.habCrit == 15.0  # Check criteria set properly

        self.dataInst.habCount = 14
        assert self.dataInst.checkStop() == True

        self.dataInst.habCount = 3
        self.dataInst.habCrit = 0  # reset.
        self.dataInst.setCritDivisor = 1
        assert self.dataInst.checkStop() == False
        assert self.dataInst.habCrit == 30.0
        self.dataInst.habCrit = 0  # reset
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
        self.dataInst.setCritType = 'Peak'  # require actualTrialOrder
        self.dataInst.actualTrialOrder = ['A', 'B']
        for i in range(0, 14):
            self.dataInst.actualTrialOrder.append('Hab')
        self.dataInst.actualTrialOrder.append('Test')
        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 7, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})
        self.dataInst.habCount += 1
        assert self.dataInst.checkStop() == False
        assert self.dataInst.habCrit == 40.0  # should not change yet

        habMatrix[6]['sumOnA'] = 25.0
        assert self.dataInst.checkStop() == False
        assert self.dataInst.habCrit == 45.0  # should change to peak now

        self.dataInst.setCritType = 'Max'
        habMatrix[3]['sumOnA'] = 15.0  # 25+15+10=50
        assert self.dataInst.checkStop() == False
        assert self.dataInst.habCrit == 50.0  # should change to max now

        habMatrix[2]['sumOnA'] = 15.0  # 25+15+15=55
        assert self.dataInst.checkStop() == False
        assert self.dataInst.habCrit == 55.0  # should change to max now

        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 8, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})  # At this point, most recent 3 should be 25+10+5=40

        self.dataInst.habCount += 1  # 6
        assert self.dataInst.checkStop() == True
        assert self.dataInst.habCrit == 55.0  # should not have changed.

        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 9, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})

        self.dataInst.habCount += 1  # 7

        self.dataInst.metCritWindow = 4  # 25+10+5+10 = 50
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
        self.dataInst.metCritStatic = 'Fixed'  # Should not trip this time b/c setcritwindow is 3 + 4 = 7
        assert self.dataInst.checkStop() == False
        assert self.dataInst.habCrit == 55.0  # should not have changed.

        self.dataInst.metCritWindow = 5  # Now it should trip
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

        assert self.trialInst.actualTrialOrder == ['A', 'A', 'B', 'B', 'C', 'C', 'D']
        assert self.trialInst.ageMo == 1
        assert self.trialInst.ageDay == 0

    def test_hab_expansion(self):
        testOne = [99, 'Test', 'NB', 7, 2, 18, 'testcond', 8, 2, 18]
        self.trialInst.trialOrder = ['A', 'A', 'B', 'B', 'Hab', 'D']
        self.trialInst.run(testMode=testOne)
        assert len(self.trialInst.actualTrialOrder) == 19
        assert len([x for x in self.trialInst.actualTrialOrder if x == 'Hab']) == 14
        self.trialInst.habTrialList = ['C','Hab']
        self.trialInst.run(testMode=testOne)
        assert len(self.trialInst.actualTrialOrder) == 33
        assert len([x for x in self.trialInst.actualTrialOrder if x == 'Hab']) == 14
        assert len([x for x in self.trialInst.actualTrialOrder if x == 'C']) == 14


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
        self.trialInst.stimNames = {'Intro': ['Movie1', 'Movie2', 'Movie3', 'Movie4'],
                                    'Fam': ['Movie5', 'Movie6', 'Movie7', 'Movie8'],
                                    'Test': ['Movie1', 'Movie2', 'Movie3', 'Movie4']}
        self.trialInst.trialOrder = ['Intro', 'Fam', 'Test']
        self.trialInst.randPres = True
        self.trialInst.stimPres = True

        testTwo = [99, 'Test', 'NB', 7, 2, 16, 'A']  # corresponds to {Intro:[1,2], Fam:[1,2], Test:[1,2]}
        self.trialInst.run(testMode=testTwo)

        # First make sure it won't go without condlist
        assert self.trialInst.stimNames['Intro'] == ['Movie1', 'Movie2', 'Movie3', 'Movie4']
        self.trialInst.condList = ['A', 'B', 'C', 'D']
        self.trialInst.run(testMode=testTwo)

        assert self.trialInst.stimNames['Intro'] == ['Movie1', 'Movie2']
        assert self.trialInst.stimNames['Fam'] == ['Movie5', 'Movie6']
        assert self.trialInst.stimNames['Test'] == ['Movie1', 'Movie2']


class TestCommands(object):
    """
    Tests the setup and operation of redo, jump, insert hab, etc.
    """

    def setup_class(self):
        trial_settings = copy.deepcopy(base_settings)
        trial_settings['trialOrder'] = "['A','A','B','B','C','C','D']"

        self.commandInst = PH.PyHab(trial_settings)
        self.commandInst.sNum = 99
        self.commandInst.ageMo = 5
        self.commandInst.ageDay = 15
        self.commandInst.sex = 'm'
        self.commandInst.cond = 'dataTest'
        self.commandInst.condLabel = 'dataTest'
        self.commandInst.actualTrialOrder = ['A', 'A', 'B', 'B', 'C', 'C', 'D']
        self.commandInst.stimNames = {'A': ['Movie1', 'Movie2', 'Movie3', 'Movie4'],
                                      'B': ['Movie5', 'Movie6', 'Movie7', 'Movie8'],
                                      'C': ['Movie1', 'Movie2', 'Movie3', 'Movie4'],
                                      'D': ['Movie9', 'Movie10']}
        self.commandInst.stimDict={'A': ['Movie1', 'Movie2'],
                                      'B': ['Movie5', 'Movie6'],
                                      'C': ['Movie1', 'Movie2'],
                                      'D': ['Movie9', 'Movie10']}
        self.commandInst.counters={'A':1, 'B':0,'C':0,'D':0} #Counters is number of trials of that type that have occurred.

        self.testMatrix = [{'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                            'condLabel': 'dataTest', 'trial': 1, 'GNG': 1, 'trialType': 'A', 'stimName': 'movie1.mov',
                            'habCrit': 0, 'sumOnA': 3.0, 'numOnA': 2, 'sumOffA': 3.5,
                            'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                           {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                            'condLabel': 'dataTest', 'trial': 2, 'GNG': 1, 'trialType': 'A',
                            'stimName': 'movie2.mov', 'habCrit': 0, 'sumOnA': 3.0, 'numOnA': 2, 'sumOffA': 3.5,
                            'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}]
        self.testDatList = {
            'verboseOn': [{'trial': 1, 'trialType': 'A', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                          {'trial': 1, 'trialType': 'A', 'startTime': 3.0, 'endTime': 4.5, 'duration': 1.5},
                          {'trial': 2, 'trialType': 'A', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                          {'trial': 2, 'trialType': 'A', 'startTime': 3.0, 'endTime': 4.5, 'duration': 1.5}],
            'verboseOff': [{'trial': 1, 'trialType': 'A', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                           {'trial': 1, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5, 'duration': 2.0},
                           {'trial': 2, 'trialType': 'A', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                           {'trial': 2, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5, 'duration': 2.0}],
            'verboseOn2': [{'trial': 1, 'trialType': 'A', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                           {'trial': 1, 'trialType': 'A', 'startTime': 3.0, 'endTime': 4.5, 'duration': 1.5},
                           {'trial': 2, 'trialType': 'A', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                           {'trial': 2, 'trialType': 'A', 'startTime': 3.0, 'endTime': 4.5, 'duration': 1.5}],
            'verboseOff2': [{'trial': 1, 'trialType': 'A', 'startTime': 1.5, 'endtTime': 3.0, 'duration': 1.5},
                            {'trial': 1, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5, 'duration': 2.0},
                            {'trial': 2, 'trialType': 'A', 'startTime': 1.5, 'endtTime': 3.0, 'duration': 1.5},
                            {'trial': 2, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5, 'duration': 2.0}]}

    def teardown_class(self):
        del self.commandInst
        del self.testDatList
        del self.testMatrix

    def test_setupredo(self):
        self.commandInst.trialText = mock.MagicMock()
        self.commandInst.stimPres = True

        self.commandInst.verbDatList = copy.deepcopy(self.testDatList)
        self.commandInst.dataMatrix = copy.deepcopy(self.testMatrix)
        self.commandInst.autoAdvance = ['B']


        [x, y] = self.commandInst.redoSetup(2,self.commandInst.autoAdvance)
        assert y == 1
        assert x == "Movie1"
        assert len(self.commandInst.badTrials) == 1 # we won't test redo here, just make sure it ran.
        assert len(self.commandInst.dataMatrix) == 1
        self.commandInst.verbDatList = copy.deepcopy(self.testDatList)
        self.commandInst.dataMatrix = copy.deepcopy(self.testMatrix)
        self.commandInst.autoAdvance = ['B']
        self.commandInst.counters={'A':2, 'B':1,'C':0,'D':0}
        temp1 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                            'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'B', 'stimName': 'movie5.mov',
                            'habCrit': 0, 'sumOnA': 3.0, 'numOnA': 2, 'sumOffA': 3.5,
                            'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        temp2 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                            'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'B',
                            'stimName': 'movie2.mov', 'habCrit': 0, 'sumOnA': 3.0, 'numOnA': 2, 'sumOffA': 3.5,
                            'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        self.commandInst.dataMatrix.append(temp1)
        [x, y] = self.commandInst.redoSetup(3,['B'])
        assert y == 2
        assert x =="Movie2"

        self.commandInst.verbDatList = copy.deepcopy(self.testDatList)
        self.commandInst.dataMatrix = copy.deepcopy(self.testMatrix)
        self.commandInst.autoAdvance = ['B']
        self.commandInst.counters = {'A': 2, 'B': 2, 'C': 0, 'D': 0}
        self.commandInst.dataMatrix.append(temp1)
        self.commandInst.dataMatrix.append(temp2)
        [x, y] = self.commandInst.redoSetup(4,['B'])
        assert y == 2
        assert x == "Movie2"

    def test_jump_and_insert(self):
        self.commandInst.trialText = mock.MagicMock()
        self.commandInst.stimPres = True
        testOne = [99, 'Test', 'NB', 7, 2, 18, 'testcond', 8, 2, 18]
        self.commandInst.stimNames = {'A': ['Movie1', 'Movie2', 'Movie3', 'Movie4'],
                                      'B': ['Movie5', 'Movie6', 'Movie7', 'Movie8'],
                                      'C': ['Movie1', 'Movie2', 'Movie3', 'Movie4'],
                                      'D': ['Movie9', 'Movie10'],
                                      'Hab': ['Movie12']}
        self.commandInst.stimDict = {'A': ['Movie1', 'Movie2'],
                                     'B': ['Movie5', 'Movie6'],
                                     'C': ['Movie1', 'Movie2'],
                                     'D': ['Movie9', 'Movie10'],
                                     'Hab': ['Movie12']}
        self.commandInst.trialOrder = ['A', 'A', 'B', 'B', 'Hab', 'D']
        self.commandInst.counters = {'A': 2, 'B': 2, 'C': 0, 'D': 0,'Hab':2}
        self.commandInst.run(testMode=testOne)

        [x, y] = self.commandInst.jumpToTest(7)
        assert x == 'Movie9'
        assert y == 'D'
        assert self.commandInst.actualTrialOrder ==['A', 'A', 'B', 'B', 'Hab', 'Hab','D']

        self.commandInst.stimPres = False # Insert would require loading movies otherwise. Requires manual testing.
        [x,y] = self.commandInst.insertHab(7)
        assert x == 0
        assert y == 'Hab'

        self.commandInst.stimPres = True
        self.commandInst.habTrialList = ['Hab','C']
        self.commandInst.trialOrder = ['A', 'A', 'B', 'B', 'Hab', 'D']
        self.commandInst.counters = {'A': 2, 'B': 2, 'C': 1, 'D': 0,'Hab':1}
        self.commandInst.run(testMode=testOne)
        [x, y] = self.commandInst.jumpToTest(7)
        assert x == 'Movie9'
        assert y == 'D'
        assert self.commandInst.actualTrialOrder == ['A', 'A', 'B', 'B', 'Hab', 'C', 'D']

        self.commandInst.stimPres = False
        [x, y] = self.commandInst.insertHab(7)
        assert x == 0
        assert y == 'Hab'
        assert self.commandInst.actualTrialOrder == ['A', 'A', 'B', 'B', 'Hab', 'C','Hab','C','D']


class TestPrefLook(object):
    """
    Tests preferential-looking-specific functions that can be tested, basically just the data functions + end exp.
    """
    def setup_class(self):
        self.dataInstPL = PHL.PyHabPL(base_settings)
        # Set values for things that are usually set in the experimenter dialog
        self.dataInstPL.sNum = 99
        self.dataInstPL.sID = "Lore"
        self.dataInstPL.ageMo = 5
        self.dataInstPL.ageDay = 15
        self.dataInstPL.sex = 'm'
        self.dataInstPL.cond = 'dataTest'
        self.dataInstPL.condLabel = 'dataTest'
        # Create base mock data structures to tinker with
        self.trialVOn1 = [{'trial': 1, 'trialType': 'A', 'startTime': 0.0, 'endTime': 1.5, 'duration': 1.5},
                          {'trial': 1, 'trialType': 'A', 'startTime': 6.5, 'endTime': 8.0,
                           'duration': 1.5}]  # VerboseOn1
        self.trialVOff1 = [{'trial': 1, 'trialType': 'A', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                           {'trial': 1, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5,
                            'duration': 2.0}]  # VerboseOff
        self.trialVOn2 = [{'trial': 1, 'trialType': 'A', 'startTime': 3.0, 'endTime': 4.5, 'duration': 1.5},
                          {'trial': 1, 'trialType': 'A', 'startTime': 8.0, 'endTime': 9.5,
                           'duration': 1.5}]  # VerboseOn2
        self.testMatrix = [{'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                            'condLabel': 'dataTest', 'trial': 1, 'GNG': 1, 'trialType': 'A', 'stimName': 'movie1.mov',
                            'habCrit': 0, 'sumOnL': 3.0, 'numOnL': 2, 'sumOnR': 3.0, 'numOnR': 2, 'sumOff': 3.5,
                            'numOff': 2}, {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                            'condLabel': 'dataTest', 'trial': 2, 'GNG': 1, 'trialType': 'B',
                                            'stimName': 'movie2.mov',
                                            'habCrit': 0, 'sumOnL': 3.0, 'numOnL': 2, 'sumOnR': 3.0, 'numOnR': 2,
                                            'sumOffB': 3.5, 'numOffB': 2}]
        self.testDatList = {'verboseOn': [{'trial': 1, 'trialType': 'A', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                           {'trial': 1, 'trialType': 'A', 'startTime': 6.5, 'endTime': 8.0, 'duration': 1.5},
                           {'trial': 2, 'trialType': 'A', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                           {'trial': 2, 'trialType': 'A', 'startTime': 6.5, 'endTime': 8.0, 'duration': 1.5}],
             'verboseOff': [{'trial': 1, 'trialType': 'A', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                            {'trial': 1, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5, 'duration': 2.0},
                            {'trial': 2, 'trialType': 'A', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                            {'trial': 2, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5, 'duration': 2.0}],
             'verboseOn2':[{'trial': 1, 'trialType': 'A', 'startTime': 3.0, 'endTime': 4.5, 'duration': 1.5},
                           {'trial': 1, 'trialType': 'A', 'startTime': 8.0, 'endTime': 9.5, 'duration': 1.5},
                           {'trial': 2, 'trialType': 'A', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                           {'trial': 2, 'trialType': 'A', 'startTime': 8.0, 'endTime': 9.5, 'duration': 1.5}]}


    def teardown_class(self):
        del self.dataInstPL
        del self.trialVOn1
        del self.trialVOff1
        del self.trialVOn2
        del self.testMatrix

    def test_PLabort(self):
        self.dataInstPL.abortTrial(self.trialVOn1, self.trialVOff1, 1, 'A', self.trialVOn2, 'movie1.mov')

        assert self.dataInstPL.badTrials[0]['trial'] == self.trialVOn1[0]['trial']
        assert self.dataInstPL.badTrials[0]['trialType'] == self.trialVOn1[0]['trialType']
        assert self.dataInstPL.badTrials[0]['GNG'] == 0
        assert self.dataInstPL.badTrials[0]['habCrit'] == 0
        assert self.dataInstPL.badTrials[0]['sumOnL'] == self.trialVOn1[0]['duration'] + self.trialVOn1[1]['duration']
        assert self.dataInstPL.badTrials[0]['sumOff'] == self.trialVOff1[0]['duration'] + self.trialVOff1[1]['duration']
        assert self.dataInstPL.badTrials[0]['numOnL'] == len(self.trialVOn1)
        assert self.dataInstPL.badTrials[0]['numOff'] == len(self.trialVOff1)
        assert self.dataInstPL.badTrials[0]['sumOnR'] == self.trialVOn2[0]['duration'] + self.trialVOn2[1]['duration']
        assert self.dataInstPL.badTrials[0]['numOnR'] == len(self.trialVOn2)

    def test_PLdatarec(self):
        self.dataInstPL.dataMatrix = []
        self.dataInstPL.badTrials = []

        self.dataInstPL.dataRec(self.trialVOn1, self.trialVOff1, 1, 'A', self.trialVOn2, 'movie1.mov')

        assert len(self.dataInstPL.dataMatrix) == 1
        assert self.dataInstPL.dataMatrix[0] == self.testMatrix[0]
        assert len(self.dataInstPL.badTrials) == 0

    def test_PLcheckstop(self):
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
                          'habCrit': 0, 'sumOnL': 7.0, 'numOnL': 2, 'sumOff': 3.5,
                          'numOff': 2, 'sumOnR': 3.0, 'numOnR': 2})
        self.dataInstPL.dataMatrix = habMatrix  # We can actually use python's pointer thing to our advantage here: dataMatrix will update with habMatrix
        self.dataInstPL.badTrials = []
        self.dataInstPL.stimPres = True  # Temporary, so it doesn't try to play the end-hab sound.

        self.dataInstPL.habCount = 1
        assert self.dataInstPL.checkStop() == False
        assert self.dataInstPL.habCrit == 0

        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnL': 7.0, 'numOnL': 2, 'sumOff': 3.5,
                          'numOff': 2, 'sumOnR': 3.0, 'numOnR': 2})

        self.dataInstPL.habCount = 2
        assert self.dataInstPL.checkStop() == False
        assert self.dataInstPL.habCrit == 0

        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 5, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnL': 7.0, 'numOnL': 2, 'sumOff': 3.5,
                          'numOff': 2, 'sumOnR': 3.0, 'numOnR': 2})

        self.dataInstPL.habCount = 3
        assert self.dataInstPL.habCrit == 0
        assert self.dataInstPL.checkStop() == False
        assert self.dataInstPL.habCrit == 15.0  # Check criteria set properly

        self.dataInstPL.habCount = 14
        assert self.dataInstPL.checkStop() == True

        self.dataInstPL.habCount = 3
        self.dataInstPL.habCrit = 0  # reset.
        self.dataInstPL.setCritDivisor = 1
        assert self.dataInstPL.checkStop() == False
        assert self.dataInstPL.habCrit == 30.0
        self.dataInstPL.habCrit = 0  # reset
        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 6, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnL': 7.0, 'numOnL': 2, 'sumOff': 3.5,
                          'numOff': 2, 'sumOnR': 3.0, 'numOnR': 2})
        self.dataInstPL.habCount += 1
        self.dataInstPL.setCritWindow = 4
        assert self.dataInstPL.checkStop() == False
        assert self.dataInstPL.habCrit == 40.0

        self.dataInstPL.setCritWindow = 3
        self.dataInstPL.setCritType = 'Peak'  # require actualTrialOrder
        self.dataInstPL.actualTrialOrder = ['A', 'B']
        for i in range(0, 14):
            self.dataInstPL.actualTrialOrder.append('Hab')
        self.dataInstPL.actualTrialOrder.append('Test')
        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 7, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnL': 2.0, 'numOnL': 2, 'sumOff': 3.5,
                          'numOff': 2, 'sumOnR': 3.0, 'numOnR': 2})
        self.dataInstPL.habCount += 1
        assert self.dataInstPL.checkStop() == False
        assert self.dataInstPL.habCrit == 40.0  # should not change yet

        habMatrix[6]['sumOnL'] = 15.0
        habMatrix[6]['sumOnR'] = 10.0
        assert self.dataInstPL.checkStop() == False
        assert self.dataInstPL.habCrit == 45.0  # should change to peak now

        self.dataInstPL.setCritType = 'Max'
        habMatrix[3]['sumOnL'] = 10.0  # 25+15+10=50
        habMatrix[3]['sumOnR'] = 5.0
        assert self.dataInstPL.checkStop() == False
        assert self.dataInstPL.habCrit == 50.0  # should change to max now

        habMatrix[2]['sumOnL'] = 10.0  # 25+15+15=55
        habMatrix[2]['sumOnR'] = 5.0
        assert self.dataInstPL.checkStop() == False
        assert self.dataInstPL.habCrit == 55.0  # should change to max now

        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 8, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnL': 2.0, 'numOnL': 2, 'sumOff': 3.5,
                          'numOff': 2, 'sumOnR': 3.0, 'numOnR': 2})  # At this point, most recent 3 should be 25+10+5=40

        self.dataInstPL.habCount += 1  # 6
        assert self.dataInstPL.checkStop() == True
        assert self.dataInstPL.habCrit == 55.0  # should not have changed.

        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 9, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnL': 7.0, 'numOnL': 2, 'sumOff': 3.5,
                          'numOff': 2, 'sumOnR': 3.0, 'numOnR': 2})

        self.dataInstPL.habCount += 1  # 7

        self.dataInstPL.metCritWindow = 4  # 25+10+5+10 = 50
        assert self.dataInstPL.checkStop() == True
        assert self.dataInstPL.habCrit == 55.0  # should not have changed.

        habMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 10, 'GNG': 1, 'trialType': 'Hab', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnL': 2.1, 'numOnL': 2, 'sumOff': 3.5,
                          'numOff': 2, 'sumOnR': 3.0, 'numOnR': 2})

        self.dataInstPL.habCount += 1  # 8
        self.dataInstPL.metCritWindow = 5  # 25+10+5+10+5.1  = 55.1
        assert self.dataInstPL.habCrit == 55.0  # should not have changed.
        assert self.dataInstPL.checkStop() == False

        self.dataInstPL.metCritDivisor = 2
        assert self.dataInstPL.checkStop() == True
        assert self.dataInstPL.habCrit == 55.0  # should not have changed.

        self.dataInstPL.metCritWindow = 4
        self.dataInstPL.metCritStatic = 'Fixed'  # Should not trip this time b/c setcritwindow is 3 + 4 = 7
        assert self.dataInstPL.checkStop() == False
        assert self.dataInstPL.habCrit == 55.0  # should not have changed.

        self.dataInstPL.metCritWindow = 5  # Now it should trip
        assert self.dataInstPL.checkStop() == True
        assert self.dataInstPL.habCrit == 55.0  # should not have changed.
