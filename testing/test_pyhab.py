import math

import pytest
import os, sys, copy, time, mock
from psychopy import event

sys.path.insert(0, os.getcwd())

from PyHab import PyHabClass as PH
from PyHab import PyHabClassPL as PHL
from PyHab import PyHabClassHPP as PHPP

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
    'durationCriterion': "[]",
    'durationInclude': "0",
    'autoRedo': "[]",
    'onTimeDeadline': '{}',
    'habByDuration': '0',
    'randPres': '0',
    'condPath': '',
    'condFile': '',
    'condList': "[]",
    'trialOrder': "[]",
    'blockList': "{}",
    'blockDataList': '[]',
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
    'expScreenIndex': 0,
    'ISI': "{'A':0.0,'B':0.0,'C':0.0,'D':0.0}",
    'freezeFrame': '0.0',
    'playAttnGetter': "{'A':'PyHabDefault','B':'PyHabDefault'}",
    'dynamicPause': '[]',
    'midAG': '{}',
    'hppStimScrOnly': '[]',
    'attnGetterList': "{'PyHabDefault':{'stimType':'Audio','stimName':'upchime1.wav','stimDur':2,'stimLoc':'PyHab/upchime1.wav','shape':'Rectangle','color':'yellow'}}",
    'folderPath': '',
    'trialTypes': "['A','B','C','D']",
    'prefLook': '0',
    'loadSep': '0'}

testOne= {'snum':99, 'sID':'Test', 'sex':'NB', 'dob_m':'7', 'dob_d':'2', 'dob_y':'18', 'cond':'testcond',
                   'dot_m':'8', 'dot_d':'2', 'dot_y':'18'}

def test_init():
    """
    Tests initialization, makes sure everything is being read in as the correct types.

    :return:
    :rtype:
    """
    itest = PH.PyHab(base_settings, testMode=True)
    TheDicts = [itest.maxDur, itest.playThrough, itest.maxOff, itest.minOn, itest.stimNames,
                itest.stimList, itest.playAttnGetter, itest.attnGetterList, itest.ISI, itest.screenColor,
                itest.screenWidth, itest.screenHeight, itest.movieWidth, itest.movieHeight, itest.screenIndex,
                itest.onTimeDeadline, itest.blockList]
    TheLists = [itest.dataColumns, itest.movieEnd, itest.autoAdvance, itest.condList, itest.trialOrder,
                itest.autoRedo, itest.durationCriterion, itest.hppStimScrOnly]
    TheStrings = [itest.prefix, itest.dataFolder, itest.stimPath, itest.condFile]
    TheFloats = [itest.freezeFrame]
    TheInts = [itest.blindPres, itest.durationInclude, itest.loadSep]
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
        self.dataInst = PH.PyHab(base_settings, testMode=True)
        # Set values for things that are usually set in the experimenter dialog
        self.dataInst.sNum = 99
        self.dataInst.sID = 'TEST'
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
        self.testMatrix = [{'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                            'condLabel': 'dataTest', 'trial': 1, 'GNG': 1, 'trialType': 'A', 'stimName': 'movie1.mov',
                            'habCrit': 0, 'habTrialNo':'', 'sumOnA': 3.0, 'numOnA': 2, 'sumOffA': 3.5,
                            'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                            'numOffB': 2, 'trialDuration': 4.5, 'firstLook': 1.5}, {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                            'condLabel': 'dataTest', 'trial': 2, 'GNG': 1, 'trialType': 'B',
                                            'stimName': 'movie2.mov',
                                            'habCrit': 0, 'habTrialNo':'', 'sumOnA': 3.0, 'numOnA': 2, 'sumOffA': 3.5,
                                            'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                                            'numOffB': 2, 'trialDuration': 4.5}]
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
        """
        Test that redo properly updates the data file and structures. Does not test 'redosetup' for auto-advancing
        :return:
        :rtype:
        """
        tempMatrix = copy.deepcopy(self.testMatrix)
        tempDat = copy.deepcopy(self.testDatList)
        self.dataInst.dataMatrix = copy.deepcopy(self.testMatrix)
        self.dataInst.verbDatList = copy.deepcopy(self.testDatList)
        self.dataInst.badTrials = []  # It doesn't teardown until ALL of the functions have been run so we have to reset it
        self.dataInst.verbBadList = {'verboseOn':[], 'verboseOff':[], 'verboseOn2':[], 'verboseOff2':[]}
        # Needs an ActualTrialOrder
        self.dataInst.actualTrialOrder=['A','A','A']
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

    def test_redo_hab(self):

        self.dataInst.dataMatrix = copy.deepcopy(self.testMatrix)
        self.dataInst.verbDatList = copy.deepcopy(self.testDatList)
        self.dataInst.badTrials = []  # It doesn't teardown until ALL of the functions have been run so we have to reset it
        self.dataInst.verbBadList = {'verboseOn': [], 'verboseOff': [], 'verboseOn2': [], 'verboseOff2': []}

        self.dataInst.blockList={'D':{'trialList': ['Hab'],
                                        'habituation': 1,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'First',
                                        'habThresh': 5.0,
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': ['C']}}
        i = 'D'
        # These are settings which would normally happen during init, but we are doing here b/c hab is added late.
        self.dataInst.habCount[i] = 0
        self.dataInst.habCrit[i] = 0
        self.dataInst.habSetWhen[i] = -1
        self.dataInst.habMetWhen[i] = -1
        self.dataInst.maxHabIndex[i] = 0
        self.dataInst.habDataCompiled[i] = [0] * self.dataInst.blockList['D']['maxHabTrials']

        self.dataInst.actualTrialOrder = ['A','B','D1*^.C','D2*^.C','D3*^.C','D4*^.C']

        self.dataInst.dataMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'D1.C', 'stimName': 'movie1.mov',
                'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                'numOffB': 2})
        self.dataInst.verbDatList['verboseOn'].append({'trial':3, 'trialType':'Hab', 'startTime':0, 'endTime':3.5, 'duration':3.5})
        self.dataInst.verbDatList['verboseOff'].append({'trial':3, 'trialType':'Hab', 'startTime':3.5, 'endTime':5.0, 'duration':1.5})
        self.dataInst.verbDatList['verboseOn'].append({'trial':3, 'trialType':'Hab', 'startTime':5.0, 'endTime':11.5, 'duration':6.5})
        self.dataInst.verbDatList['verboseOff'].append({'trial':3,'trialType':'Hab', 'startTime':11.5, 'endTime':13.5, 'duration':2.0})


        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] = self.dataInst.dataMatrix[-1]['sumOnA']
        self.dataInst.habCount['D'] = 1

        self.dataInst.redoTrial(3)
        # All that setup, but there are only two things not tested in the above test. Still, some redundancies just to be sure
        assert self.dataInst.habCount['D'] == 0
        assert self.dataInst.habDataCompiled['D'][0] == 0
        assert len(self.dataInst.dataMatrix) == 2
        assert len(self.dataInst.badTrials) == 1

        # Reset again, but this time with a multi-trial hab block

        self.dataInst.dataMatrix = copy.deepcopy(self.testMatrix)
        self.dataInst.verbDatList = copy.deepcopy(self.testDatList)
        self.dataInst.badTrials = []
        self.dataInst.verbBadList = {'verboseOn': [], 'verboseOff': [], 'verboseOn2': [], 'verboseOff2': []}
        self.dataInst.actualTrialOrder = ['A','B','D1*.B','D1*^.C','D2*.B','D2*^.C','D3*.B','D3*^.C','D4*.B','D4*^.C','D5*.B','D5*^.C']

        self.dataInst.blockList = {'D': {'trialList': ['B','C'],
                                         'habituation': 1,
                                         'habByDuration': 0,
                                         'maxHabTrials': 14,
                                         'setCritWindow': 3,
                                         'setCritDivisor': 2.0,
                                         'setCritType': 'First',
                                         'habThresh': 5.0,
                                         'metCritWindow': 3,
                                         'metCritDivisor': 1.0,
                                         'metCritStatic': 'Moving',
                                         'calcHabOver': ['B','C']}}

        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'D1.B', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2})
        self.dataInst.verbDatList['verboseOn'].append(
            {'trial': 3, 'trialType': 'D.B', 'startTime': 0, 'endTime': 3.5, 'duration': 3.5})
        self.dataInst.verbDatList['verboseOff'].append(
            {'trial': 3, 'trialType': 'D.B', 'startTime': 3.5, 'endTime': 5.0, 'duration': 1.5})
        self.dataInst.verbDatList['verboseOn'].append(
            {'trial': 3, 'trialType': 'D.B', 'startTime': 5.0, 'endTime': 11.5, 'duration': 6.5})
        self.dataInst.verbDatList['verboseOff'].append(
            {'trial': 3, 'trialType': 'D.B', 'startTime': 11.5, 'endTime': 13.5, 'duration': 2.0})
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] = self.dataInst.dataMatrix[-1]['sumOnA']
        self.dataInst.habCount['D'] = 0  # Has not yet proceeded to end of hab trial!

        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'D1.C', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2})
        self.dataInst.verbDatList['verboseOn'].append(
            {'trial': 4, 'trialType': 'D.C', 'startTime': 0, 'endTime': 3.5, 'duration': 3.5})
        self.dataInst.verbDatList['verboseOff'].append(
            {'trial': 4, 'trialType': 'D.C', 'startTime': 3.5, 'endTime': 5.0, 'duration': 1.5})
        self.dataInst.verbDatList['verboseOn'].append(
            {'trial': 4, 'trialType': 'D.C', 'startTime': 5.0, 'endTime': 11.5, 'duration': 6.5})
        self.dataInst.verbDatList['verboseOff'].append(
            {'trial': 4, 'trialType': 'D.C', 'startTime': 11.5, 'endTime': 13.5, 'duration': 2.0})
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += self.dataInst.dataMatrix[-1]['sumOnA']
        self.dataInst.habCount['D'] = 1

        # Try redoing 3, then 4.
        self.dataInst.redoTrial(3)
        assert self.dataInst.habCount['D'] == 1
        assert self.dataInst.habDataCompiled['D'][0] == 10
        assert len(self.dataInst.dataMatrix) == 3
        assert len(self.dataInst.badTrials) == 1

        self.dataInst.redoTrial(4)
        assert self.dataInst.habCount['D'] == 0
        assert self.dataInst.habDataCompiled['D'][0] == 0
        assert len(self.dataInst.dataMatrix) == 2
        assert len(self.dataInst.badTrials) == 2

        # 'undo' the last two redos, try again, this time with only 'Hab' in the calcHabOver list.
        self.dataInst.badTrials = []
        self.dataInst.verbBadList = {'verboseOn': [], 'verboseOff': [], 'verboseOn2': [], 'verboseOff2': []}

        self.dataInst.blockList = {'D': {'trialList': ['B', 'C'],
                                         'habituation': 1,
                                         'habByDuration': 0,
                                         'maxHabTrials': 14,
                                         'setCritWindow': 3,
                                         'setCritDivisor': 2.0,
                                         'setCritType': 'First',
                                         'habThresh': 5.0,
                                         'metCritWindow': 3,
                                         'metCritDivisor': 1.0,
                                         'metCritStatic': 'Moving',
                                         'calcHabOver': ['B']}}

        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'D1.B', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2})
        self.dataInst.verbDatList['verboseOn'].append(
            {'trial': 3, 'trialType': 'D.B', 'startTime': 0, 'endTime': 3.5, 'duration': 3.5})
        self.dataInst.verbDatList['verboseOff'].append(
            {'trial': 3, 'trialType': 'D.B', 'startTime': 3.5, 'endTime': 5.0, 'duration': 1.5})
        self.dataInst.verbDatList['verboseOn'].append(
            {'trial': 3, 'trialType': 'D.B', 'startTime': 5.0, 'endTime': 11.5, 'duration': 6.5})
        self.dataInst.verbDatList['verboseOff'].append(
            {'trial': 3, 'trialType': 'D.B', 'startTime': 11.5, 'endTime': 13.5, 'duration': 2.0})
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] = self.dataInst.dataMatrix[-1]['sumOnA']
        self.dataInst.habCount['D'] = 0  # Has not yet proceeded to end of hab trial!

        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'D1.C', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2})
        self.dataInst.verbDatList['verboseOn'].append(
            {'trial': 4, 'trialType': 'D.C', 'startTime': 0, 'endTime': 3.5, 'duration': 3.5})
        self.dataInst.verbDatList['verboseOff'].append(
            {'trial': 4, 'trialType': 'D.C', 'startTime': 3.5, 'endTime': 5.0, 'duration': 1.5})
        self.dataInst.verbDatList['verboseOn'].append(
            {'trial': 4, 'trialType': 'D.C', 'startTime': 5.0, 'endTime': 11.5, 'duration': 6.5})
        self.dataInst.verbDatList['verboseOff'].append(
            {'trial': 4, 'trialType': 'D.C', 'startTime': 11.5, 'endTime': 13.5, 'duration': 2.0})
        # self.dataInst.habDataCompiled[self.dataInst.habCount] += self.dataInst.dataMatrix[-1]['sumOnA']
        # Because this is no longer included in calcHabOver.
        self.dataInst.habCount['D'] = 1

        # Try redoing 3, then 4.
        self.dataInst.redoTrial(3)
        assert self.dataInst.habCount['D'] == 1
        assert self.dataInst.habDataCompiled['D'][0] == 0
        assert len(self.dataInst.dataMatrix) == 3
        assert len(self.dataInst.badTrials) == 1

        self.dataInst.redoTrial(4)
        assert self.dataInst.habCount['D'] == 0
        assert self.dataInst.habDataCompiled['D'][0] == 0
        assert len(self.dataInst.dataMatrix) == 2
        assert len(self.dataInst.badTrials) == 2

        # Reset one more to test an edge case: When there are multiple instances of the same trial type in a single hab
        # block iteration.
        self.dataInst.dataMatrix = copy.deepcopy(self.testMatrix)
        self.dataInst.verbDatList = copy.deepcopy(self.testDatList)
        self.dataInst.badTrials = []
        self.dataInst.verbBadList = {'verboseOn': [], 'verboseOff': [], 'verboseOn2': [], 'verboseOff2': []}
        self.dataInst.blockList = {'D': {'trialList': ['B', 'C', 'B'],
                                         'habituation': 1,
                                         'habByDuration': 0,
                                         'maxHabTrials': 14,
                                         'setCritWindow': 3,
                                         'setCritDivisor': 2.0,
                                         'setCritType': 'First',
                                         'habThresh': 5.0,
                                         'metCritWindow': 3,
                                         'metCritDivisor': 1.0,
                                         'metCritStatic': 'Moving',
                                         'calcHabOver': ['B','C']}}
        self.dataInst.actualTrialOrder = ['A', 'B', 'D1*.C', 'D1*.B', 'D1*^.C','D2*.C', 'D2*.B', 'D2*^.C','D3*.C', 'D3*.B', 'D3*^.C']

        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'D1.C', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2})
        self.dataInst.verbDatList['verboseOn'].append(
            {'trial': 3, 'trialType': 'hab.C', 'startTime': 0, 'endTime': 3.5, 'duration': 3.5})
        self.dataInst.verbDatList['verboseOff'].append(
            {'trial': 3, 'trialType': 'hab.C', 'startTime': 3.5, 'endTime': 5.0, 'duration': 1.5})
        self.dataInst.verbDatList['verboseOn'].append(
            {'trial': 3, 'trialType': 'hab.C', 'startTime': 5.0, 'endTime': 11.5, 'duration': 6.5})
        self.dataInst.verbDatList['verboseOff'].append(
            {'trial': 3, 'trialType': 'hab.C', 'startTime': 11.5, 'endTime': 13.5, 'duration': 2.0})
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] = self.dataInst.dataMatrix[-1]['sumOnA']  # 10
        self.dataInst.habCount['D'] = 0  # Has not yet proceeded to end of hab trial!

        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'D1.B', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2})
        self.dataInst.verbDatList['verboseOn'].append(
            {'trial': 4, 'trialType': 'hab.B', 'startTime': 0, 'endTime': 3.5, 'duration': 3.5})
        self.dataInst.verbDatList['verboseOff'].append(
            {'trial': 4, 'trialType': 'hab.B', 'startTime': 3.5, 'endTime': 5.0, 'duration': 1.5})
        self.dataInst.verbDatList['verboseOn'].append(
            {'trial': 4, 'trialType': 'hab.B', 'startTime': 5.0, 'endTime': 11.5, 'duration': 6.5})
        self.dataInst.verbDatList['verboseOff'].append(
            {'trial': 4, 'trialType': 'hab.B', 'startTime': 11.5, 'endTime': 13.5, 'duration': 2.0})
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += self.dataInst.dataMatrix[-1]['sumOnA']  # 20
        self.dataInst.habCount['D'] = 0  # Has not yet proceeded to end of hab trial!

        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 5, 'GNG': 1, 'trialType': 'D2.C', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2})
        self.dataInst.verbDatList['verboseOn'].append(
            {'trial': 5, 'trialType': 'hab.C', 'startTime': 0, 'endTime': 3.5, 'duration': 3.5})
        self.dataInst.verbDatList['verboseOff'].append(
            {'trial': 5, 'trialType': 'hab.C', 'startTime': 3.5, 'endTime': 5.0, 'duration': 1.5})
        self.dataInst.verbDatList['verboseOn'].append(
            {'trial': 5, 'trialType': 'hab.C', 'startTime': 5.0, 'endTime': 11.5, 'duration': 6.5})
        self.dataInst.verbDatList['verboseOff'].append(
            {'trial': 5, 'trialType': 'hab.C', 'startTime': 11.5, 'endTime': 13.5, 'duration': 2.0})
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += self.dataInst.dataMatrix[-1]['sumOnA']  # 30
        self.dataInst.habCount['D'] = 1

        # Now redo 3, then 4, then 5.

        self.dataInst.redoTrial(3)
        assert self.dataInst.habCount['D'] == 1
        assert self.dataInst.habDataCompiled['D'][0] == 20
        assert len(self.dataInst.dataMatrix) == 4
        assert len(self.dataInst.badTrials) == 1

        self.dataInst.redoTrial(4)
        assert self.dataInst.habCount['D'] == 1
        assert self.dataInst.habDataCompiled['D'][0] == 10
        assert len(self.dataInst.dataMatrix) == 3
        assert len(self.dataInst.badTrials) == 2

        self.dataInst.redoTrial(5)
        assert self.dataInst.habCount['D'] == 0
        assert self.dataInst.habDataCompiled['D'][0] == 0
        assert len(self.dataInst.dataMatrix) == 2
        assert len(self.dataInst.badTrials) == 3

    def test_datarec(self):
        self.dataInst.dataMatrix = []
        self.dataInst.badTrials = []

        self.dataInst.dataRec(self.trialVOn1, self.trialVOff1, 1, 'A', self.trialVOn2, self.trialVOff2, 'movie1.mov')

        assert len(self.dataInst.dataMatrix) == 1
        assert self.dataInst.dataMatrix[0] == self.testMatrix[0]
        assert len(self.dataInst.badTrials) == 0

    def test_blockSave(self):
        self.dataInst.dataMatrix = copy.deepcopy(self.testMatrix)
        self.dataInst.verbDatList = copy.deepcopy(self.testDatList)
        self.dataInst.badTrials = []
        self.dataInst.blockList = {'C': {'trialList': ['A','B'],
                                        'habituation': 0,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'First',
                                        'habThresh': 5.0,
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': []}
                                   }
        self.dataInst.actualTrialOrder = ['A','B','C.A','C.B','C.A','C.B']
        self.dataInst.blockDataList=['C']
        self.dataInst.blockDataTags={'C':[[3,4],[5,6]]}
        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'C.A', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2, 'trialDuration': 11.5})
        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'C.B', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2, 'trialDuration': 11.5})
        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 5, 'GNG': 1, 'trialType': 'C.A', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2, 'trialDuration': 11.5})
        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 6, 'GNG': 1, 'trialType': 'C.B', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2, 'trialDuration': 11.5})

        testMatrix = self.dataInst.saveBlockFile()
        assert len(testMatrix) == 4
        assert testMatrix[2]['trialType'] == 'C'
        assert testMatrix[2]['sumOnA'] == 20.0
        assert testMatrix[2]['numOnA'] == 4
        assert testMatrix[2]['trialDuration'] == 23.0
        assert testMatrix[3]['sumOnA'] == 20.0
        assert testMatrix[3]['numOnA'] == 4
        assert testMatrix[3]['trialDuration'] == 23.0
        assert testMatrix[2]['stimName'] == 'movie1.mov+movie1.mov'
        assert testMatrix[3]['trial'] == 4

    def test_blockSave_incomplete_data(self):
        # Now try it again, but the study finished early
        self.dataInst.dataMatrix = copy.deepcopy(self.testMatrix)
        self.dataInst.verbDatList = copy.deepcopy(self.testDatList)
        self.dataInst.badTrials = []
        self.dataInst.blockList = {'C': {'trialList': ['A','B'],
                                        'habituation': 0,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'First',
                                        'habThresh': 5.0,
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': []}
                                   }
        self.dataInst.actualTrialOrder = ['A', 'B', 'C.A', 'C.B', 'C.A', 'C.B']
        self.dataInst.blockDataList = ['C']
        self.dataInst.blockDataTags = {'C': [[3, 4], [5, 6]]}
        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'C.A', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2, 'trialDuration':11.5})
        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'C.B', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2, 'trialDuration':11.5})
        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 5, 'GNG': 1, 'trialType': 'C.A', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2, 'trialDuration':11.5})

        testMatrix = self.dataInst.saveBlockFile()
        assert len(testMatrix) == 4 # Should still have the first half of the last block.
        assert testMatrix[2]['trialType'] == 'C'
        assert testMatrix[2]['sumOnA'] == 20.0
        assert testMatrix[2]['numOnA'] == 4
        assert testMatrix[2]['trialDuration'] == 23.0
        assert testMatrix[3]['sumOnA'] == 10.0
        assert testMatrix[3]['numOnA'] == 2
        assert testMatrix[3]['trialDuration'] == 11.5
        assert testMatrix[2]['stimName'] == 'movie1.mov+movie1.mov'
        assert testMatrix[3]['trial'] == 4

    def test_blockSave_nested_blocks(self):
        # Now redo for a block-in-block setup, save the lower block.
        self.dataInst.dataMatrix = copy.deepcopy(self.testMatrix)
        self.dataInst.verbDatList = copy.deepcopy(self.testDatList)
        self.dataInst.badTrials = []
        self.dataInst.blockList = {'C': {'trialList': ['A','B'],
                                        'habituation': 0,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'First',
                                        'habThresh': 5.0,
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': []},
                                   'D': {'trialList': ['B','C'],
                                        'habituation': 0,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'First',
                                        'habThresh': 5.0,
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': []}}
        self.dataInst.actualTrialOrder = ['A', 'B', 'C.A', 'C.B', 'C.A', 'C.B','D.B','D.C.A','D.C.B']
        self.dataInst.blockDataList = ['C']
        self.dataInst.blockDataTags = {'C': [[3, 4], [5, 6], [8,9]]}
        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'C.A', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2, 'trialDuration': 11.5})
        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'C.B', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2, 'trialDuration': 11.5})
        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 5, 'GNG': 1, 'trialType': 'C.A', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2, 'trialDuration': 11.5})
        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 6, 'GNG': 1, 'trialType': 'C.B', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2, 'trialDuration':11.5})
        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 7, 'GNG': 1, 'trialType': 'D.B', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2, 'trialDuration':11.5})
        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 8, 'GNG': 1, 'trialType': 'D.C.A', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2, 'trialDuration':11.5})
        self.dataInst.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 9, 'GNG': 1, 'trialType': 'D.C.B', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
             'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
             'numOffB': 2, 'trialDuration':11.5})

        testMatrix = self.dataInst.saveBlockFile()
        assert len(testMatrix) == 6
        assert testMatrix[2]['trialType'] == 'C'
        assert testMatrix[5]['trialType'] == 'D.C'
        assert testMatrix[2]['sumOnA'] == 20.0
        assert testMatrix[2]['numOnA'] == 4
        assert testMatrix[2]['trialDuration'] == 23.0
        assert testMatrix[3]['sumOnA'] == 20.0
        assert testMatrix[3]['numOnA'] == 4
        assert testMatrix[3]['trialDuration'] == 23.0
        assert testMatrix[5]['sumOnA'] == 20.0
        assert testMatrix[5]['numOnA'] == 4
        assert testMatrix[5]['trialDuration'] == 23.0
        assert testMatrix[2]['stimName'] == 'movie1.mov+movie1.mov'
        assert testMatrix[3]['trial'] == 4
        assert testMatrix[5]['trial'] == 6

    def test_habSave(self):
        """
        For testing saving hab files

        :return:
        :rtype:
        """
        habMatrix = copy.deepcopy(self.testMatrix)
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'Hab1.A', 'stimName': 'movie1.mov',
                          'habCrit': 0,'habTrialNo':1, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'Hab1.B', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo':1, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 5, 'GNG': 1, 'trialType': 'Hab2.A', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 2, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 6, 'GNG': 1, 'trialType': 'Hab2.B', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 2, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 7, 'GNG': 1, 'trialType': 'Hab3.A', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 3, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 8, 'GNG': 1, 'trialType': 'Hab3.B', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 3, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})

        self.dataInst.dataMatrix = habMatrix  # We can actually use python's pointer thing to our advantage here: dataMatrix will update with habMatrix
        self.dataInst.badTrials = []
        self.dataInst.blockList['Hab'] = {'trialList': ['A','B'],
                                        'habituation': 1,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'First',
                                        'habThresh': 5.0,
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': ['A']}
        self.dataInst.blockList['secondHab'] = {'trialList': ['A','B'],
                                        'habituation': 1,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'First',
                                        'habThresh': 5.0,
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': ['A']}
        self.dataInst.habCount = {'Hab':3, 'secondHab':0}

        habSaveData = self.dataInst.saveHabFile()
        assert len(habSaveData) == 5  # 5 because it includes non-hab trials, of which there are 2 at the start
        assert habSaveData[3]['trialType'] == 'Hab'
        assert habSaveData[3]['sumOnA'] == 10.0

        self.dataInst.blockList['Hab']['calcHabOver'] = ['A', 'B']
        habSaveData = self.dataInst.saveHabFile()
        assert len(habSaveData) == 5
        assert habSaveData[3]['trialType'] == 'Hab'
        assert habSaveData[3]['sumOnA'] == 20.0
        assert habSaveData[3]['stimName'] == 'movie1.mov+movie1.mov'

        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 9, 'GNG': 1, 'trialType': 'secondHab1.A', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 1, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 10, 'GNG': 1, 'trialType': 'secondHab1.B', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 1, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 11, 'GNG': 1, 'trialType': 'secondHab2.A', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 2, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 12, 'GNG': 1, 'trialType': 'secondHab2.B', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 2, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 13, 'GNG': 1, 'trialType': 'secondHab3.A', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 3, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 14, 'GNG': 1, 'trialType': 'secondHab3.B', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 3, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})

        self.dataInst.habCount['secondHab'] = 3
        habSaveData = self.dataInst.saveHabFile()
        assert len(habSaveData) == 8  # 5 because it includes non-hab trials, of which there are 2 at the start
        assert habSaveData[6]['trialType'] == 'secondHab'
        assert habSaveData[6]['sumOnA'] == 10.0

        self.dataInst.blockList['secondHab']['calcHabOver'] = ['A', 'B']
        habSaveData = self.dataInst.saveHabFile()
        assert len(habSaveData) == 8
        assert habSaveData[6]['trialType'] == 'secondHab'
        assert habSaveData[6]['sumOnA'] == 20.0
        assert habSaveData[6]['stimName'] == 'movie1.mov+movie1.mov'


    def test_checkstop(self):
        """
        This one's a little trickier than the others because it requires creating fake hab data and testing all of the
        different modes!
        Default settings: Set first 3, divisor 2. Test moving window, 3, divisor 1. Maxhab 14

        :return:
        :rtype:
        """
        # Create an appropriate hab setting.
        self.dataInst.blockList = {'D': {'trialList': ['C'],
                                        'habituation': 1,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'First',
                                        'habThresh': 5.0,
                                        'maxHabSet': -1,
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': ['C']}}

        i='D'
        # These are settings which would normally happen during init, but we are doing here b/c hab is added late.
        self.dataInst.habCount[i] = 0
        self.dataInst.habCrit[i] = 0
        self.dataInst.habSetWhen[i] = -1
        self.dataInst.habMetWhen[i] = -1
        self.dataInst.maxHabIndex[i] = 0
        self.dataInst.habDataCompiled[i] = [0] * self.dataInst.blockList['D']['maxHabTrials']

        habMatrix = copy.deepcopy(self.testMatrix)
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'D1.C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})
        self.dataInst.dataMatrix = habMatrix  # We can actually use python's pointer thing to our advantage here: dataMatrix will update with habMatrix
        self.dataInst.badTrials = []
        self.dataInst.habDataCompiled['D'] = [0]*14
        self.dataInst.stimPres = True  # Temporary, so it doesn't try to play the end-hab sound.
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 0, 10
        self.dataInst.habCount['D'] = 1
        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 0
        assert self.dataInst.habSetWhen['D'] == -1

        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'D2.C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})

        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 1, 10
        self.dataInst.habCount['D'] = 2
        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 0
        assert self.dataInst.habSetWhen['D'] == -1

        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 5, 'GNG': 1, 'trialType': 'D3.C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})

        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 2, 10
        self.dataInst.habCount['D'] = 3
        assert self.dataInst.habCrit['D'] == 0
        assert self.dataInst.habSetWhen['D'] == -1
        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 15.0  # Check criteria set properly
        assert self.dataInst.habSetWhen['D'] == 3

        self.dataInst.habCount['D'] = 14
        assert self.dataInst.checkStop('D') == True

        self.dataInst.habCount['D'] = 3
        self.dataInst.habCrit['D'] = 0  # reset.
        self.dataInst.habSetWhen['D'] = -1
        self.dataInst.blockList['D']['setCritDivisor'] = 1
        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 30.0
        self.dataInst.habCrit['D'] = 0  # reset
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 6, 'GNG': 1, 'trialType': 'D4.C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] = habMatrix[-1]['sumOnA']  # 3, 10
        self.dataInst.habCount['D'] += 1 # 4
        self.dataInst.blockList['D']['setCritWindow'] = 4
        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 40.0 # HabSetWhen = 4

        self.dataInst.blockList['D']['setCritWindow'] = 3
        self.dataInst.blockList['D']['setCritType'] = 'Peak'  # require actualTrialOrder
        self.dataInst.actualTrialOrder = ['A', 'B']
        for i in range(0, 14):
            self.dataInst.actualTrialOrder.append('D'+str(i+1)+'*^.C')
        self.dataInst.actualTrialOrder.append('Test')
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 7, 'GNG': 1, 'trialType': 'D.5C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] = habMatrix[-1]['sumOnA']  # 4, 5
        self.dataInst.habCount['D'] += 1 # 5
        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 40.0  # should not change yet. HabSetWhen = 4
        assert self.dataInst.habSetWhen['D'] == 4

        self.dataInst.habDataCompiled['D'][4] = 25.0  # +20s.  10, 10, 25.
        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 45.0  # should change to peak now. HabSetWhen = 5
        assert self.dataInst.habSetWhen['D'] == 5


        self.dataInst.blockList['D']['setCritType'] = 'Max'
        habMatrix[3]['sumOnA'] = 15.0  # 25+15+10=50
        self.dataInst.habDataCompiled['D'][1] = 15.0  # nonconsec, 15+10+25
        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 50.0  # should change to max now
        assert self.dataInst.habSetWhen['D'] == 5


        habMatrix[2]['sumOnA'] = 15.0  # 25+15+15=55
        self.dataInst.habDataCompiled['D'][0] = 15.0  # 15, 15, 10, 10, 25, so should be 55.
        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 55.0  # should change to max now. HabSetWhen=5
        assert self.dataInst.habSetWhen['D'] == 5

        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 8, 'GNG': 1, 'trialType': 'D6.C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})  # At this point, most recent 3 should be 25+10+5=40

        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] = habMatrix[-1]['sumOnA'] # 5, 5
        self.dataInst.habCount['D'] += 1  # 6
        assert self.dataInst.habSetWhen['D'] == 5
        assert self.dataInst.checkStop('D') == False
        self.dataInst.habSetWhen['D'] = 3
        assert self.dataInst.checkStop('D') == True
        self.dataInst.habSetWhen['D'] = 5
        assert self.dataInst.habCrit['D'] == 55.0  # should not have changed.

        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 9, 'GNG': 1, 'trialType': 'D7.C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 10.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})

        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] = habMatrix[-1]['sumOnA']  # 6, 10
        self.dataInst.habCount['D'] += 1  # 7

        self.dataInst.blockList['D']['metCritWindow'] = 4  # 25+10+5+10 = 50
        assert self.dataInst.checkStop('D') == False
        self.dataInst.habSetWhen['D']= 3
        assert self.dataInst.checkStop('D') == True
        self.dataInst.habSetWhen['D'] = 5
        assert self.dataInst.habCrit['D'] == 55.0  # should not have changed.

        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 10, 'GNG': 1, 'trialType': 'D8.C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 5.1, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})

        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] = habMatrix[-1]['sumOnA']  # 7, 5.1
        self.dataInst.habCount['D'] += 1  # 8
        self.dataInst.blockList['D']['metCritWindow'] = 5  # 25+10+5+10+5.1  = 55.1
        assert self.dataInst.habCrit['D'] == 55.0  # should not have changed.
        assert self.dataInst.checkStop('D') == False
        self.dataInst.habSetWhen['D'] = 3
        assert self.dataInst.checkStop('D') == False
        self.dataInst.habSetWhen['D'] = 5

        self.dataInst.blockList['D']['metCritDivisor'] = 2
        assert self.dataInst.checkStop('D') == False
        self.dataInst.habSetWhen['D'] = 3 # Keeping this at 3 for the remaining tests.
        assert self.dataInst.checkStop('D') == True
        assert self.dataInst.habCrit['D'] == 55.0  # should not have changed.

        self.dataInst.blockList['D']['metCritWindow'] = 4
        self.dataInst.blockList['D']['metCritStatic'] = 'Fixed'  # Should not trip this time b/c setcritwindow is 3 + 4 = 7
        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 55.0  # should not have changed.

        self.dataInst.blockList['D']['metCritWindow'] = 5 # Should now trip because setcritwindow is 3 + 5 = 8
        assert self.dataInst.checkStop('D') == True
        assert self.dataInst.habCrit['D'] == 55.0  # should not have changed.

        # Test "last" hab criterion.
        self.dataInst.blockList['D']['setCritType'] = 'Last'
        self.dataInst.blockList['D']['metCritStatic'] = 'Moving'
        # Test requires that the hab-crit is reset so that the current set doesn't meet it..
        self.dataInst.habCrit['D'] = 0
        self.dataInst.blockList['D']['setCritWindow'] = 3
        self.dataInst.blockList['D']['metCritWindow'] = 3
        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 20.1 # 5+10+5.1, divisor = 1
        assert self.dataInst.habSetWhen['D'] == 8

        # add one more trials to ensure it tests correctly.
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 11, 'GNG': 1, 'trialType': 'D9.C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 5.1, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})

        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] = habMatrix[-1]['sumOnA']  # 8, 5.1
        self.dataInst.habCount['D'] += 1  # 9

        self.dataInst.blockList['D']['metCritDivisor'] = 2
        assert self.dataInst.checkStop('D') == True
        assert self.dataInst.habMetWhen['D'] == 9


        # Hab sub-trial tracking does not need its own tests here because data from habituation trials are recorded in
        # their own data structure, which is compiled during doTrial.

    def test_habthresh(self):
        """
        A further set of tests for CheckStop focusing on setting the criterion using HabThresh

        :return:
        :rtype:
        """
        # Create an appropriate hab setting.
        self.dataInst.blockList = {'D': {'trialList': ['C'],
                                        'habituation': 1,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'Threshold',
                                        'habThresh': 20.0, # Sum of 20s over 3 trials
                                        'maxHabSet': 6, # If not set by trial 6, end hab
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': ['C']}}

        i='D'
        # These are settings which would normally happen during init, but we are doing here b/c hab is added late.
        self.dataInst.habCount[i] = 0
        self.dataInst.habCrit[i] = 0
        self.dataInst.habSetWhen[i] = -1
        self.dataInst.habMetWhen[i] = -1
        self.dataInst.maxHabIndex[i] = 0
        self.dataInst.habDataCompiled[i] = [0] * self.dataInst.blockList['D']['maxHabTrials']

        habMatrix = copy.deepcopy(self.testMatrix)
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'D1.C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})
        self.dataInst.dataMatrix = habMatrix  # We can actually use python's pointer thing to our advantage here: dataMatrix will update with habMatrix
        self.dataInst.badTrials = []
        self.dataInst.habDataCompiled['D'] = [0] * 14
        self.dataInst.stimPres = True  # Temporary, so it doesn't try to play the end-hab sound.
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 0, 5
        self.dataInst.habCount['D'] = 1

        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'D2.C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})

        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 1, 5
        self.dataInst.habCount['D'] = 2
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 5, 'GNG': 1, 'trialType': 'D3.C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})

        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 2, 5
        self.dataInst.habCount['D'] = 3

        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 0 # B/c thresh not met
        assert self.dataInst.habSetWhen['D'] == -1 # b/c thresh not met

        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 6, 'GNG': 1, 'trialType': 'D4.C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 12.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})

        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 3, 12
        self.dataInst.habCount['D'] = 4

        # Now meets threshold with 22, crit should be 11
        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 11.0
        assert self.dataInst.habSetWhen['D'] == 4

        # Now revert so it fails again.
        habMatrix[-1]['sumOnA'] = 5.0
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']-1] -= 7 # Reduce
        self.dataInst.habCrit['D'] = 0
        self.dataInst.habSetWhen['D'] = -1
        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 0  # B/c thresh not met
        assert self.dataInst.habSetWhen['D'] == -1  # b/c thresh not met

        # now add two more trials and show it ends on 6.
        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 7, 'GNG': 1, 'trialType': 'D5.C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})

        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 4, 5
        self.dataInst.habCount['D'] = 5
        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 0  # B/c thresh not met
        assert self.dataInst.habSetWhen['D'] == -1  # b/c thresh not met

        habMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 8, 'GNG': 1, 'trialType': 'D6.C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                          'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5,
                          'numOffB': 2})

        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 5, 5
        self.dataInst.habCount['D'] = 6
        assert self.dataInst.checkStop('D') == True # Now that it has done the 'maxHabSet' number of trials it should end like it hit the max hab count
        assert self.dataInst.habCrit['D'] == 0  # B/c thresh not met
        assert self.dataInst.habSetWhen['D'] == -1  # b/c thresh not met

    def test_fixedtriallength(self):
        """
        Tests the new "fixed trial length" habituation type. Slightly complicated.
        :return:
        :rtype:
        """
        self.dataInst.blockList = {'D': {'trialList': ['C'],
                                         'habituation': 1,
                                         'habByDuration': 0,
                                         'maxHabTrials': 14,
                                         'setCritWindow': 0, # From start of experiment
                                         'setCritDivisor': 2.0,
                                         'setCritType': 'FixedTrialLength',
                                         'habThresh': 2.5, # 2.5 consec seconds look away
                                         'maxHabSet': -1,
                                         'metCritWindow': 3, # over 3 trials
                                         'metCritDivisor': 1.0,
                                         'metCritStatic': 'Moving',
                                         'calcHabOver': ['C']}}

        i = 'D'
        # These are settings which would normally happen during init, but we are doing here b/c hab is added late.
        self.dataInst.habCount[i] = 0
        self.dataInst.habCrit[i] = 0
        self.dataInst.habSetWhen[i] = -1
        self.dataInst.habMetWhen[i] = -1
        self.dataInst.maxHabIndex[i] = 0
        self.dataInst.habDataCompiled[i] = [0] * self.dataInst.blockList['D']['maxHabTrials']

        habMatrix = copy.deepcopy(self.testMatrix)
        self.dataInst.dataMatrix = habMatrix  # We can actually use python's pointer thing to our advantage here: dataMatrix will update with habMatrix
        # The main problem is that the relevant data are not from the hab matrix but from the verbose data in this case.
        habOn1_1= [{'trial': 3, 'trialType': 'D1.C', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                          {'trial': 3, 'trialType': 'D1.C', 'startTime': 3.0, 'endTime': 4.5,
                           'duration': 1.5}]
        habOff1_1 = [{'trial': 3, 'trialType': 'D1.C', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                           {'trial': 3, 'trialType': 'D1.C', 'startTime': 4.5, 'endTime': 7.5,
                            'duration': 3.0}]
        habOn2_1 = [{'trial': 3, 'trialType': 'D1.C', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                  {'trial': 3, 'trialType': 'D1.C', 'startTime': 3.0, 'endTime': 4.5,
                   'duration': 1.5}]
        habOff2_1 = [{'trial': 3, 'trialType': 'D1.C', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                   {'trial': 3, 'trialType': 'D1.C', 'startTime': 4.5, 'endTime': 7.5,
                    'duration': 3.0}]
        habOn1_2= [{'trial': 4, 'trialType': 'D2.C', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                          {'trial': 4, 'trialType': 'D2.C', 'startTime': 3.0, 'endTime': 4.5,
                           'duration': 1.5}]
        habOff1_2 = [{'trial': 4, 'trialType': 'D2.C', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                           {'trial': 4, 'trialType': 'D2.C', 'startTime': 4.5, 'endTime': 7.5,
                            'duration': 3.0}]
        habOn2_2 = [{'trial': 4, 'trialType': 'D2.C', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                  {'trial': 4, 'trialType': 'D2.C', 'startTime': 3.0, 'endTime': 4.5,
                   'duration': 1.5}]
        habOff2_2 = [{'trial': 4, 'trialType': 'D2.C', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                   {'trial': 4, 'trialType': 'D2.C', 'startTime': 4.5, 'endTime': 7.5,
                    'duration': 3.0}]
        habOn1_3= [{'trial': 5, 'trialType': 'D3.C', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                          {'trial': 5, 'trialType': 'D3.C', 'startTime': 3.0, 'endTime': 4.5,
                           'duration': 1.5}]
        habOff1_3 = [{'trial': 5, 'trialType': 'D3.C', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                           {'trial': 5, 'trialType': 'D3.C', 'startTime': 4.5, 'endTime': 7.5,
                            'duration': 3.0}]
        habOn2_3 = [{'trial': 5, 'trialType': 'D3.C', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                  {'trial': 5, 'trialType': 'D3.C', 'startTime': 3.0, 'endTime': 4.5,
                   'duration': 1.5}]
        habOff2_3 = [{'trial': 5, 'trialType': 'D3.C', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                   {'trial': 5, 'trialType': 'D3.C', 'startTime': 4.5, 'endTime': 7.5,
                    'duration': 3.0}]

        self.dataInst.dataRec(habOn1_1, habOff1_1, 3, 'D1.C', habOn2_1, habOff2_1, 'movie1.mov')
        self.dataInst.badTrials = []
        self.dataInst.habDataCompiled['D'] = [0] * 14
        self.dataInst.stimPres = True  # Temporary, so it doesn't try to play the end-hab sound.
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 0, 5
        self.dataInst.habCount['D'] = 1

        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 2.5
        assert self.dataInst.habSetWhen['D'] == 1


        self.dataInst.dataRec(habOn1_2, habOff1_2, 4, 'D2.C', habOn2_2, habOff2_2, 'movie1.mov')
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 1, 5
        self.dataInst.habCount['D'] = 2

        assert self.dataInst.checkStop('D') == False

        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 2, 5
        self.dataInst.habCount['D'] = 3
        self.dataInst.dataRec(habOn1_3, habOff1_3, 5, 'D3.C', habOn2_3, habOff2_3, 'movie1.mov')

        blockName = 'D'
        assert self.dataInst.habCount[blockName] >= self.dataInst.habSetWhen[blockName] + self.dataInst.blockList[blockName]['metCritWindow'] - 1
        habIndex = self.dataInst.habCount[blockName] - self.dataInst.blockList[blockName]['metCritWindow']

        targetTrials = []
        targetTrialNames = []
        for j in range(habIndex, self.dataInst.habCount[blockName]):
            for q in range(0, len(self.dataInst.blockList[blockName]['calcHabOver'])):
                matchName = blockName + str(j+1) + '.' + self.dataInst.blockList[blockName]['calcHabOver'][q]
                targetTrialNames.append(matchName)
        for i in range(0, len(self.dataInst.dataMatrix)):
            if self.dataInst.dataMatrix[i]['trialType'] in targetTrialNames:
                targetTrials.append(self.dataInst.dataMatrix[i]['trial'])

        assert targetTrials == [3,4,5]


        consecPostThreshold = [0 for x in range(self.dataInst.blockList[blockName]['metCritWindow'])]
        assert len(consecPostThreshold) == 3

        trialPerIter = len(targetTrials) / self.dataInst.blockList[blockName]['metCritWindow']  # Typically this will be 1
        assert trialPerIter == 1
        currIter = 0

        for n in range(0, len(targetTrials)):
            if n % trialPerIter == 0 and n > 0:
                currIter += 1
            for i in range(0, len(self.dataInst.verbDatList['verboseOff'])):
                if self.dataInst.verbDatList['verboseOff'][i]['trial'] == targetTrials[n]:
                    if self.dataInst.verbDatList['verboseOff'][i]['duration'] >= self.dataInst.habCrit[blockName]:
                        consecPostThreshold[currIter] = 1
        assert currIter == 2
        assert consecPostThreshold == [1,1,1]

        assert self.dataInst.checkStop('D') == True

    def test_fixedlength_complicated(self):
        """
        Testing the fixed trial length mode with a complex block that has three trials, two of which are
        counted for the purpose of habituation.

        :return:
        :rtype:
        """
        self.dataInst.blockList = {'D': {'trialList': ['C','A','B'],
                                         'habituation': 1,
                                         'habByDuration': 0,
                                         'maxHabTrials': 14,
                                         'setCritWindow': 0, # From start of experiment
                                         'setCritDivisor': 2.0,
                                         'setCritType': 'FixedTrialLength',
                                         'habThresh': 2.5, # 2.5 consec seconds look away
                                         'maxHabSet': -1,
                                         'metCritWindow': 3, # over 3 trials
                                         'metCritDivisor': 1.0,
                                         'metCritStatic': 'Moving',
                                         'calcHabOver': ['C','B']}} # I can't imagine a real study like this but it's a strong test.

        i = 'D'
        # These are settings which would normally happen during init, but we are doing here b/c hab is added late.
        self.dataInst.habCount[i] = 0
        self.dataInst.habCrit[i] = 0
        self.dataInst.habSetWhen[i] = -1
        self.dataInst.habMetWhen[i] = -1
        self.dataInst.maxHabIndex[i] = 0
        self.dataInst.habDataCompiled[i] = [0] * self.dataInst.blockList['D']['maxHabTrials']

        habMatrix = copy.deepcopy(self.testMatrix)
        self.dataInst.dataMatrix = habMatrix  # We can actually use python's pointer thing to our advantage here: dataMatrix will update with habMatrix
        # Clear verbose data
        self.dataInst.verbDatList = copy.deepcopy(self.testDatList)
        # The main problem is that the relevant data are not from the hab matrix but from the verbose data in this case.
        habOn1_1 = [{'trial': 3, 'trialType': 'D1.C', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                    {'trial': 3, 'trialType': 'D1.C', 'startTime': 3.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff1_1 = [{'trial': 3, 'trialType': 'D1.C', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                           {'trial': 3, 'trialType': 'D1.C', 'startTime': 4.5, 'endTime': 5.5,
                            'duration': 1.0}]
        habOn1_2 = [{'trial': 4, 'trialType': 'D1.A', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                    {'trial': 4, 'trialType': 'D1.A', 'startTime': 3.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff1_2 = [{'trial': 4, 'trialType': 'D1.A', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                     {'trial': 4, 'trialType': 'D1.A', 'startTime': 4.5, 'endTime': 7.5,
                      'duration': 3.0}]
        habOn1_3 = [{'trial': 5, 'trialType': 'D1.B', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                    {'trial': 5, 'trialType': 'D1.B', 'startTime': 3.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff1_3 = [{'trial': 5, 'trialType': 'D1.B', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                     {'trial': 5, 'trialType': 'D1.B', 'startTime': 4.5, 'endTime': 5.5,
                      'duration': 1.0}]
        #No after this.
        self.dataInst.dataRec(habOn1_1, habOff1_1, 3, 'D1.C', habOn1_1, habOff1_1, 'movie1.mov')
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 0, 5
        self.dataInst.dataRec(habOn1_2, habOff1_2, 4, 'D1.A', habOn1_2, habOff1_2, 'movie1.mov')
        self.dataInst.dataRec(habOn1_3, habOff1_3, 5, 'D1.B', habOn1_3, habOff1_3, 'movie1.mov')
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 0, 5

        self.dataInst.badTrials = []
        self.dataInst.stimPres = True  # Temporary, so it doesn't try to play the end-hab sound.
        self.dataInst.habCount['D'] = 1

        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 2.5
        assert self.dataInst.habSetWhen['D'] == 1

        habOn2_1 = [{'trial': 6, 'trialType': 'D2.C', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                    {'trial': 6, 'trialType': 'D2.C', 'startTime': 3.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff2_1 = [{'trial': 6, 'trialType': 'D2.C', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                           {'trial': 6, 'trialType': 'D2.C', 'startTime': 4.5, 'endTime': 5.5,
                            'duration': 1.0}]
        habOn2_2 = [{'trial': 7, 'trialType': 'D2.A', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                    {'trial': 7, 'trialType': 'D2.A', 'startTime': 3.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff2_2 = [{'trial': 7, 'trialType': 'D2.A', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                     {'trial': 7, 'trialType': 'D2.A', 'startTime': 4.5, 'endTime': 7.5,
                      'duration': 3.0}]
        habOn2_3 = [{'trial': 8, 'trialType': 'D2.B', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                    {'trial': 8, 'trialType': 'D2.B', 'startTime': 3.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff2_3 = [{'trial': 8, 'trialType': 'D2.B', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                     {'trial': 8, 'trialType': 'D2.B', 'startTime': 4.5, 'endTime': 7.5,
                      'duration': 3.0}]

        self.dataInst.dataRec(habOn2_1, habOff2_1, 6, 'D2.C', habOn2_1, habOff2_1, 'movie1.mov')
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 0, 5
        self.dataInst.dataRec(habOn2_2, habOff2_2, 7, 'D2.A', habOn2_2, habOff2_2, 'movie1.mov')
        self.dataInst.dataRec(habOn2_3, habOff2_3, 8, 'D2.B', habOn2_3, habOff2_3, 'movie1.mov')
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 0, 5
        self.dataInst.habCount['D'] += 1

        assert self.dataInst.checkStop('D') == False

        habOn3_1 = [{'trial': 9, 'trialType': 'D3.C', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                    {'trial': 9, 'trialType': 'D3.C', 'startTime': 3.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff3_1 = [{'trial': 9, 'trialType': 'D3.C', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                     {'trial': 9, 'trialType': 'D3.C', 'startTime': 4.5, 'endTime': 7.5,
                      'duration': 3.0}]
        habOn3_2 = [{'trial': 10, 'trialType': 'D3.A', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                    {'trial': 10, 'trialType': 'D3.A', 'startTime': 3.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff3_2 = [{'trial': 10, 'trialType': 'D3.A', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                     {'trial': 10, 'trialType': 'D3.A', 'startTime': 4.5, 'endTime': 7.5,
                      'duration': 3.0}]
        habOn3_3 = [{'trial': 11, 'trialType': 'D3.B', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                    {'trial': 11, 'trialType': 'D3.B', 'startTime': 3.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff3_3 = [{'trial': 11, 'trialType': 'D3.B', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                     {'trial': 11, 'trialType': 'D3.B', 'startTime': 4.5, 'endTime': 6.5,
                      'duration': 2.0}]

        self.dataInst.dataRec(habOn3_1, habOff3_1, 9, 'D3.C', habOn3_1, habOff3_1, 'movie1.mov')
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 0, 5
        self.dataInst.dataRec(habOn3_2, habOff3_2, 10, 'D3.A', habOn3_2, habOff3_2, 'movie1.mov')
        self.dataInst.dataRec(habOn3_3, habOff3_3, 11, 'D3.B', habOn3_3, habOff3_3, 'movie1.mov')
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 0, 5
        self.dataInst.habCount['D'] += 1

        blockName = 'D'
        assert self.dataInst.habCount[blockName] >= self.dataInst.habSetWhen[blockName] + self.dataInst.blockList[blockName]['metCritWindow'] - 1
        habIndex = self.dataInst.habCount[blockName] - self.dataInst.blockList[blockName]['metCritWindow']

        targetTrials = []
        targetTrialNames = []
        for j in range(habIndex, self.dataInst.habCount[blockName]):
            for q in range(0, len(self.dataInst.blockList[blockName]['calcHabOver'])):
                matchName = blockName + str(j+1) + '.' + self.dataInst.blockList[blockName]['calcHabOver'][q]
                targetTrialNames.append(matchName)
        for i in range(0, len(self.dataInst.dataMatrix)):
            if self.dataInst.dataMatrix[i]['trialType'] in targetTrialNames:
                targetTrials.append(self.dataInst.dataMatrix[i]['trial'])

        assert targetTrials == [3,5,6,8,9,11]


        consecPostThreshold = [0 for x in range(self.dataInst.blockList[blockName]['metCritWindow'])]
        assert len(consecPostThreshold) == 3

        trialPerIter = len(targetTrials) / self.dataInst.blockList[blockName]['metCritWindow']  # Typically this will be 1
        assert trialPerIter == 2
        currIter = 0

        for n in range(0, len(targetTrials)):
            if n % trialPerIter == 0 and n > 0:
                currIter += 1
            for i in range(0, len(self.dataInst.verbDatList['verboseOff'])):
                if self.dataInst.verbDatList['verboseOff'][i]['trial'] == targetTrials[n]:
                    if self.dataInst.verbDatList['verboseOff'][i]['duration'] >= self.dataInst.habCrit[blockName]:
                        consecPostThreshold[currIter] = 1
        assert currIter == 2
        assert consecPostThreshold == [0,1,1]

        assert self.dataInst.checkStop('D') == False

        habOn4_1 = [{'trial': 12, 'trialType': 'D4.C', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                    {'trial': 12, 'trialType': 'D4.C', 'startTime': 3.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff4_1 = [{'trial': 12, 'trialType': 'D4.C', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                     {'trial': 12, 'trialType': 'D4.C', 'startTime': 4.5, 'endTime': 5.5,
                      'duration': 1.0}]
        habOn4_2 = [{'trial': 13, 'trialType': 'D4.A', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                    {'trial': 13, 'trialType': 'D4.A', 'startTime': 3.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff4_2 = [{'trial': 13, 'trialType': 'D4.A', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                     {'trial': 13, 'trialType': 'D4.A', 'startTime': 4.5, 'endTime': 7.5,
                      'duration': 3.0}]
        habOn4_3 = [{'trial': 14, 'trialType': 'D4.B', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                    {'trial': 14, 'trialType': 'D4.B', 'startTime': 3.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff4_3 = [{'trial': 14, 'trialType': 'D4.B', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                     {'trial': 14, 'trialType': 'D4.B', 'startTime': 4.5, 'endTime': 7.5,
                      'duration': 3.0}]

        self.dataInst.dataRec(habOn4_1, habOff4_1, 12, 'D4.C', habOn4_1, habOff4_1, 'movie1.mov')
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 0, 5
        self.dataInst.dataRec(habOn4_2, habOff4_2, 13, 'D4.A', habOn4_2, habOff4_2, 'movie1.mov')
        self.dataInst.dataRec(habOn4_3, habOff4_3, 14, 'D4.B', habOn4_3, habOff4_3, 'movie1.mov')
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 0, 5
        self.dataInst.habCount['D'] += 1

        assert self.dataInst.habCount[blockName] >= self.dataInst.habSetWhen[blockName] + self.dataInst.blockList[blockName]['metCritWindow'] - 1
        habIndex = self.dataInst.habCount[blockName] - self.dataInst.blockList[blockName]['metCritWindow']

        targetTrials = []
        targetTrialNames = []
        for j in range(habIndex, self.dataInst.habCount[blockName]):
            for q in range(0, len(self.dataInst.blockList[blockName]['calcHabOver'])):
                matchName = blockName + str(j + 1) + '.' + self.dataInst.blockList[blockName]['calcHabOver'][q]
                targetTrialNames.append(matchName)
        for i in range(0, len(self.dataInst.dataMatrix)):
            if self.dataInst.dataMatrix[i]['trialType'] in targetTrialNames:
                targetTrials.append(self.dataInst.dataMatrix[i]['trial'])

        assert targetTrials == [6, 8, 9, 11,12, 14]

        consecPostThreshold = [0 for x in range(self.dataInst.blockList[blockName]['metCritWindow'])]
        assert len(consecPostThreshold) == 3

        trialPerIter = len(targetTrials) / self.dataInst.blockList[blockName]['metCritWindow']
        assert trialPerIter == 2
        currIter = 0

        for n in range(0, len(targetTrials)):
            if n % trialPerIter == 0 and n > 0:
                currIter += 1
            for i in range(0, len(self.dataInst.verbDatList['verboseOff'])):
                if self.dataInst.verbDatList['verboseOff'][i]['trial'] == targetTrials[n]:
                    if self.dataInst.verbDatList['verboseOff'][i]['duration'] >= self.dataInst.habCrit[blockName]:
                        consecPostThreshold[currIter] = 1
        assert currIter == 2
        assert consecPostThreshold == [1, 1, 1]

        assert self.dataInst.checkStop('D') == True

    def test_fixedlength_crosstrial(self):
        """
        Tests the "fixed trial length" hab type with the new "cross-trial" criterion mode
        :return:
        :rtype:
        """
        self.dataInst.blockList = {'D': {'trialList': ['C'],
                                         'habituation': 1,
                                         'habByDuration': 0,
                                         'maxHabTrials': 14,
                                         'setCritWindow': 0,  # From start of experiment
                                         'setCritDivisor': 2.0,
                                         'setCritType': 'FixedTrialLength',
                                         'habThresh': 5, # one five-second look-away bridging trials
                                         'maxHabSet': -1,
                                         'metCritWindow': 3,  # over 3 trials
                                         'metCritDivisor': 1.0,
                                         'metCritStatic': 'Cross-trial (fixed length only)',
                                         'calcHabOver': ['C']}}

        i = 'D'
        # These are settings which would normally happen during init, but we are doing here b/c hab is added late.
        self.dataInst.habCount[i] = 0
        self.dataInst.habCrit[i] = 0
        self.dataInst.habSetWhen[i] = -1
        self.dataInst.habMetWhen[i] = -1
        self.dataInst.maxHabIndex[i] = 0
        self.dataInst.habDataCompiled[i] = [0] * self.dataInst.blockList['D']['maxHabTrials']

        habMatrix = copy.deepcopy(self.testMatrix)
        self.dataInst.dataMatrix = habMatrix  # We can actually use python's pointer thing to our advantage here: dataMatrix will update with habMatrix
        # The main problem is that the relevant data are not from the hab matrix but from the verbose data in this case.
        self.dataInst.verbDatList = copy.deepcopy(self.testDatList)
        habOn1_1 = [{'trial': 3, 'trialType': 'D1.C', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                    {'trial': 3, 'trialType': 'D1.C', 'startTime': 3.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff1_1 = [{'trial': 3, 'trialType': 'D1.C', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                     {'trial': 3, 'trialType': 'D1.C', 'startTime': 4.5, 'endTime': 7.5,
                      'duration': 3.0}]
        habOn2_1 = [{'trial': 3, 'trialType': 'D1.C', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                    {'trial': 3, 'trialType': 'D1.C', 'startTime': 3.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff2_1 = [{'trial': 3, 'trialType': 'D1.C', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                     {'trial': 3, 'trialType': 'D1.C', 'startTime': 4.5, 'endTime': 7.5,
                      'duration': 3.0}]
        habOn1_2 = [{'trial': 4, 'trialType': 'D2.C', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                    {'trial': 4, 'trialType': 'D2.C', 'startTime': 3.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff1_2 = [{'trial': 4, 'trialType': 'D2.C', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                     {'trial': 4, 'trialType': 'D2.C', 'startTime': 4.5, 'endTime': 7.5,
                      'duration': 3.0}]
        habOn2_2 = [{'trial': 4, 'trialType': 'D2.C', 'startTime': 0, 'endTime': 1.5, 'duration': 1.5},
                    {'trial': 4, 'trialType': 'D2.C', 'startTime': 3.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff2_2 = [{'trial': 4, 'trialType': 'D2.C', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                     {'trial': 4, 'trialType': 'D2.C', 'startTime': 4.5, 'endTime': 7.5,
                      'duration': 3.0}]
        habOn1_3 = [{'trial': 5, 'trialType': 'D3.C', 'startTime': 2.5, 'endTime': 3.5, 'duration': 1.0},
                    {'trial': 5, 'trialType': 'D3.C', 'startTime': 4.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff1_3 = [{'trial': 5, 'trialType': 'D3.C', 'startTime': 0, 'endTime': 2.5, 'duration': 2.5},
                     {'trial': 5, 'trialType': 'D3.C', 'startTime': 3.5, 'endTime': 4.0, 'duration': 0.5},
                     {'trial': 5, 'trialType': 'D3.C', 'startTime': 4.5, 'endTime': 7.5,
                      'duration': 3.0}]
        habOn2_3 = [{'trial': 5, 'trialType': 'D3.C', 'startTime': 2.5, 'endTime': 3.5, 'duration': 1.0},
                    {'trial': 5, 'trialType': 'D3.C', 'startTime': 4.0, 'endTime': 4.5,
                     'duration': 1.5}]
        habOff2_3 = [{'trial': 5, 'trialType': 'D3.C', 'startTime': 0, 'endTime': 2.5, 'duration': 2.5},
                     {'trial': 5, 'trialType': 'D3.C', 'startTime': 3.5, 'endTime': 4.0, 'duration': 0.5},
                     {'trial': 5, 'trialType': 'D3.C', 'startTime': 4.5, 'endTime': 7.5,
                      'duration': 3.0}]

        self.dataInst.dataRec(habOn1_1, habOff1_1, 3, 'D1.C', habOn2_1, habOff2_1, 'movie1.mov')
        self.dataInst.badTrials = []
        self.dataInst.habDataCompiled['D'] = [0] * 14
        self.dataInst.stimPres = True  # Temporary, so it doesn't try to play the end-hab sound.
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 0, 5
        self.dataInst.habCount['D'] = 1

        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 5
        assert self.dataInst.habSetWhen['D'] == 1

        self.dataInst.dataRec(habOn1_2, habOff1_2, 4, 'D2.C', habOn2_2, habOff2_2, 'movie1.mov')
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 1, 5
        self.dataInst.habCount['D'] = 2

        assert self.dataInst.checkStop('D') == False

        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 2, 5
        self.dataInst.habCount['D'] = 3
        self.dataInst.dataRec(habOn1_3, habOff1_3, 5, 'D3.C', habOn2_3, habOff2_3, 'movie1.mov')

        blockName = 'D'
        assert self.dataInst.habCount[blockName] >= self.dataInst.habSetWhen[blockName] + self.dataInst.blockList[blockName]['metCritWindow'] - 1

        habIndex = self.dataInst.habCount[blockName] - self.dataInst.blockList[blockName]['metCritWindow']

        targetTrials = []
        targetTrialNames = []
        for j in range(habIndex, self.dataInst.habCount[blockName]):
            for q in range(0, len(self.dataInst.blockList[blockName]['calcHabOver'])):
                matchName = blockName + str(j + 1) + '.' + self.dataInst.blockList[blockName]['calcHabOver'][q]
                targetTrialNames.append(matchName)
        for i in range(0, len(self.dataInst.dataMatrix)):
            if self.dataInst.dataMatrix[i]['trialType'] in targetTrialNames:
                targetTrials.append(self.dataInst.dataMatrix[i]['trial'])

        assert targetTrials == [3, 4, 5]

        completeVerbose = []
        # Stitching together the verbose trials as is done at the end of the experiment.
        for n in range(0, len(targetTrials)):
            onIndex = -1
            offIndex = -1
            for x in range(0, len(self.dataInst.verbDatList['verboseOn'])):
                if self.dataInst.verbDatList['verboseOn'][x]['trial'] == targetTrials[n] and onIndex == -1:  # find the right index in the verbose matrices
                    onIndex = x
            for y in range(0, len(self.dataInst.verbDatList['verboseOff'])):
                if self.dataInst.verbDatList['verboseOff'][y]['trial'] == targetTrials[n] and offIndex == -1:
                    offIndex = y
            trialVerbose = []
            if onIndex >= 0:
                while onIndex < len(self.dataInst.verbDatList['verboseOn']):
                    if self.dataInst.verbDatList['verboseOn'][onIndex]['trial'] == targetTrials[n]:
                        tmpVerbose = copy.deepcopy(self.dataInst.verbDatList['verboseOn'][onIndex])
                        tmpVerbose['gazeOnOff'] = 1
                        trialVerbose.append(tmpVerbose)
                    onIndex += 1
            if offIndex >= 0:
                while offIndex < len(self.dataInst.verbDatList['verboseOff']):
                    if self.dataInst.verbDatList['verboseOff'][offIndex]['trial'] == targetTrials[n]:
                        tmpVerbose = copy.deepcopy(self.dataInst.verbDatList['verboseOff'][offIndex])
                        tmpVerbose['gazeOnOff'] = 0
                        trialVerbose.append(tmpVerbose)
                    offIndex += 1
            trialVerbose2 = sorted(trialVerbose, key=lambda trialVerbose: trialVerbose['startTime'])  # Sorts by "startTime" of each gaze event
            completeVerbose.extend(trialVerbose2)
        assert len(completeVerbose) == 13
        # Now cycle through the sorted verbose matrix and identify consecutive off events, extract their duration
        consecOffTimes = []
        m = 0
        while m < len(completeVerbose):
            if completeVerbose[m]['gazeOnOff'] == 0:
                if m < len(completeVerbose) - 1:
                    tempTotal = completeVerbose[m]['duration']
                    while m < len(completeVerbose) - 1 and completeVerbose[m + 1]['gazeOnOff'] == 0:
                        tempTotal += completeVerbose[m + 1]['duration']
                        m = m + 1
                    consecOffTimes.append(tempTotal)
                else:
                    consecOffTimes.append(completeVerbose[m]['duration'])
            m = m + 1
        assert 5.5 in consecOffTimes
        assert len([x for x in consecOffTimes if x >= self.dataInst.habCrit['D']]) >= self.dataInst.blockList['D']['metCritDivisor']
        assert self.dataInst.checkStop('D') == True

        # additional test for situation where there need to be N gaze-off events above threshold.
        self.dataInst.blockList['D']['metCritDivisor'] = 3
        assert self.dataInst.checkStop('D') == False
        self.dataInst.habCrit['D'] = 2.75
        assert self.dataInst.checkStop('D') == True


    def test_bugged_config(self):
        """
        Tests the new "fixed trial length" habituation type. Slightly complicated.
        :return:
        :rtype:
        """
        self.dataInst.blockList = {'D': {'trialList': ['C'],
                                         'habituation': 1,
                                         'habByDuration': 0,
                                         'maxHabTrials': 100,
                                         'setCritWindow': 3, # From start of experiment
                                         'setCritDivisor': 2.0,
                                         'setCritType': 'FixedTrialLength',
                                         'habThresh': 3.0, # 3 consec seconds look away
                                         'maxHabSet': -1,
                                         'metCritWindow': 3, # over 3 trials
                                         'metCritDivisor': 1.0,
                                         'metCritStatic': 'Moving',
                                         'calcHabOver': ['C']}}

        i = 'D'
        # These are settings which would normally happen during init, but we are doing here b/c hab is added late.
        self.dataInst.habCount[i] = 0
        self.dataInst.habCrit[i] = 0
        self.dataInst.habSetWhen[i] = -1
        self.dataInst.habMetWhen[i] = -1
        self.dataInst.maxHabIndex[i] = 0
        self.dataInst.habDataCompiled[i] = [0] * self.dataInst.blockList['D']['maxHabTrials']

        habMatrix = copy.deepcopy(self.testMatrix)
        self.dataInst.dataMatrix = habMatrix  # We can actually use python's pointer thing to our advantage here: dataMatrix will update with habMatrix
        # The main problem is that the relevant data are not from the hab matrix but from the verbose data in this case.
        habOn1_1= []
        habOff1_1 = [{'trial': 3, 'trialType': 'D1.C', 'startTime': 0.0, 'endTime': 5.0, 'duration': 5.0}]
        habOn2_1 = []
        habOff2_1 = [{'trial': 3, 'trialType': 'D1.C', 'startTime': 0.0, 'endTime': 5.0, 'duration': 5.0}]
        habOn1_2= []
        habOff1_2 = [{'trial': 4, 'trialType': 'D2.C', 'startTime': 0.0, 'endTime': 5.0, 'duration': 5.0}]
        habOn2_2 = []
        habOff2_2 = [{'trial': 4, 'trialType': 'D2.C', 'startTime': 0.0, 'endTime': 5.0, 'duration': 5.0}]
        habOn1_3= []
        habOff1_3 = [{'trial': 5, 'trialType': 'D3.C', 'startTime': 0, 'endTime': 5.0, 'duration': 5.0}]
        habOn2_3 = []
        habOff2_3 = [{'trial': 5, 'trialType': 'D3.C', 'startTime': 0, 'endTime': 5.0, 'duration': 5.0}]
        habOn1_4= []
        habOff1_4 = [{'trial': 6, 'trialType': 'D4.C', 'startTime': 0, 'endTime': 5.0, 'duration': 5.0}]
        habOn2_4 = []
        habOff2_4 = [{'trial': 6, 'trialType': 'D4.C', 'startTime': 0, 'endTime': 5.0, 'duration': 5.0}]
        habOn1_5 = []
        habOff1_5 = [{'trial': 7, 'trialType': 'D5.C', 'startTime': 0, 'endTime': 5.0, 'duration': 5.0}]
        habOn2_5 = []
        habOff2_5 = [{'trial': 7, 'trialType': 'D5.C', 'startTime': 0, 'endTime': 5.0, 'duration': 5.0}]
        habOn1_6 = []
        habOff1_6 = [{'trial': 8, 'trialType': 'D6.C', 'startTime': 0, 'endTime': 5.0, 'duration': 5.0}]
        habOn2_6 = []
        habOff2_6 = [{'trial': 8, 'trialType': 'D6.C', 'startTime': 0, 'endTime': 5.0, 'duration': 5.0}]

        self.dataInst.dataRec(habOn1_1, habOff1_1, 3, 'D1.C', habOn2_1, habOff2_1, 'movie1.mov')
        self.dataInst.badTrials = []
        self.dataInst.stimPres = True  # Temporary, so it doesn't try to play the end-hab sound.
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 0, 5
        self.dataInst.habCount['D'] = 1

        assert self.dataInst.checkStop('D') == False



        self.dataInst.dataRec(habOn1_2, habOff1_2, 4, 'D2.C', habOn2_2, habOff2_2, 'movie1.mov')
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 1, 5
        self.dataInst.habCount['D'] = 2

        assert self.dataInst.checkStop('D') == False

        self.dataInst.dataRec(habOn1_3, habOff1_3, 5, 'D3.C', habOn2_3, habOff2_3, 'movie1.mov')
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 2, 5
        self.dataInst.habCount['D'] = 3

        assert self.dataInst.checkStop('D') == False
        assert self.dataInst.habCrit['D'] == 3.0
        assert self.dataInst.habSetWhen['D'] == 3

        self.dataInst.dataRec(habOn1_4, habOff1_4, 6, 'D4.C', habOn2_4, habOff2_4, 'movie1.mov')
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 2, 5
        self.dataInst.habCount['D'] = 4

        assert self.dataInst.checkStop('D') == False

        self.dataInst.dataRec(habOn1_5, habOff1_5, 7, 'D5.C', habOn2_5, habOff2_5, 'movie1.mov')
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 2, 5
        self.dataInst.habCount['D'] = 5

        assert self.dataInst.checkStop('D') == False

        self.dataInst.dataRec(habOn1_6, habOff1_6, 8, 'D5.C', habOn2_6, habOff2_6, 'movie1.mov')
        self.dataInst.habDataCompiled['D'][self.dataInst.habCount['D']] += habMatrix[-1]['sumOnA']  # 2, 5
        self.dataInst.habCount['D'] = 6

        blockName = 'D'
        assert self.dataInst.habCount[blockName] >= self.dataInst.habSetWhen[blockName] + self.dataInst.blockList[blockName]['metCritWindow'] - 1
        habIndex = self.dataInst.habCount[blockName] - self.dataInst.blockList[blockName]['metCritWindow']
        targetTrials = []

        targetTrialNames = []
        for j in range(habIndex, self.dataInst.habCount[blockName]):
            for q in range(0, len(self.dataInst.blockList[blockName]['calcHabOver'])):
                matchName = blockName + str(j+1) + '.' + self.dataInst.blockList[blockName]['calcHabOver'][q]
                targetTrialNames.append(matchName)
        for i in range(0, len(self.dataInst.dataMatrix)):
            if self.dataInst.dataMatrix[i]['trialType'] in targetTrialNames:
                targetTrials.append(self.dataInst.dataMatrix[i]['trial'])

        assert targetTrials == [6,7,8]


        consecPostThreshold = [0 for x in range(self.dataInst.blockList[blockName]['metCritWindow'])]
        assert len(consecPostThreshold) == 3

        trialPerIter = len(targetTrials) / self.dataInst.blockList[blockName]['metCritWindow']  # Typically this will be 1
        assert trialPerIter == 1
        currIter = 0

        for n in range(0, len(targetTrials)):
            if n % trialPerIter == 0 and n > 0:
                currIter += 1
            for i in range(0, len(self.dataInst.verbDatList['verboseOff'])):
                if self.dataInst.verbDatList['verboseOff'][i]['trial'] == targetTrials[n]:
                    if self.dataInst.verbDatList['verboseOff'][i]['duration'] >= self.dataInst.habCrit[blockName]:
                        consecPostThreshold[currIter] = 1
        assert currIter == 2
        assert consecPostThreshold == [1,1,1]

        assert self.dataInst.checkStop('D') == True



class TestRunSetup(object):
    """
    Tests initialization functions that build the trial order and read participant info, calculate age, etc.
    """

    def setup_class(self):
        trial_settings = copy.deepcopy(base_settings)
        trial_settings['trialOrder'] = "['A','A','B','B','C','C','D']"

        self.trialInst = PH.PyHab(trial_settings, testMode=True)

    def teardown_class(self):
        del self.trialInst

    def test_setup(self):

        self.trialInst.run(testMode=testOne)

        assert self.trialInst.actualTrialOrder == ['A', 'A', 'B', 'B', 'C', 'C', 'D']
        assert self.trialInst.ageMo == 1
        assert self.trialInst.ageDay == 0

    def test_hab_one_trial_expansion(self):
        self.trialInst.trialOrder = ['A', 'A', 'B', 'B', 'C', 'D']
        # C is a hab block
        self.trialInst.blockList = {'C': {'trialList': ['F'],
                                        'habituation': 1,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'First',
                                        'habThresh': 5.0,
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': ['F']}}
        self.trialInst.blockStartIndexes['C'] = []
        self.trialInst.run(testMode=testOne)
        assert len(self.trialInst.actualTrialOrder) == 19
        assert len([x for x in self.trialInst.actualTrialOrder if '*' in x]) == 14
        assert len([x for x in self.trialInst.actualTrialOrder if '^' in x]) == 14
        assert len([x for x in self.trialInst.actualTrialOrder if '*^.F' in x]) == 14
        assert 'C14*^.F' in self.trialInst.actualTrialOrder
        assert self.trialInst.actualTrialOrder.index('C14*^.F') == self.trialInst.maxHabIndex['C']

    def test_hab_block_expansion(self):
        self.trialInst.trialOrder = ['A', 'A', 'B', 'B', 'C', 'D']
        self.trialInst.blockList = {'C': {'trialList': ['X', 'E', 'B'],
                                          'habituation': 1,
                                          'habByDuration': 0,
                                          'maxHabTrials': 10, # for easier math.
                                          'setCritWindow': 3,
                                          'setCritDivisor': 2.0,
                                          'setCritType': 'First',
                                          'habThresh': 5.0,
                                          'metCritWindow': 3,
                                          'metCritDivisor': 1.0,
                                          'metCritStatic': 'Moving',
                                          'calcHabOver': ['X','B']},
                                    'E': {'trialList': ['Z', 'Y', 'X'],
                                          'habituation': 0,
                                          'habByDuration': 0,
                                          'maxHabTrials': 14,
                                          'setCritWindow': 3,
                                          'setCritDivisor': 2.0,
                                          'setCritType': 'First',
                                          'habThresh': 5.0,
                                          'metCritWindow': 3,
                                          'metCritDivisor': 1.0,
                                          'metCritStatic': 'Moving',
                                          'calcHabOver': []}}
        self.trialInst.blockStartIndexes['C'] = []
        self.trialInst.blockStartIndexes['E'] = []
        self.trialInst.run(testMode=testOne)
        assert len(self.trialInst.actualTrialOrder) == 55
        assert len([x for x in self.trialInst.actualTrialOrder if '^' in x]) == 10
        assert len([x for x in self.trialInst.actualTrialOrder if '*' in x]) == 50
        assert self.trialInst.actualTrialOrder.index('C10*^.B') == self.trialInst.maxHabIndex['C']

    def test_block_expansion(self):
        self.trialInst.trialOrder = ['A', 'A', 'B', 'B', 'C', 'D']
        self.trialInst.blockList = {'C': {'trialList': ['X', 'E', 'B'],
                                        'habituation': 0,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'First',
                                        'habThresh': 5.0,
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': []},
                                    'E': {'trialList': ['Z', 'Y', 'X'],
                                        'habituation': 0,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'First',
                                        'habThresh': 5.0,
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': []}}
        self.trialInst.blockStartIndexes['C'] = []
        self.trialInst.blockStartIndexes['E'] = []
        self.trialInst.run(testMode=testOne)
        assert len(self.trialInst.actualTrialOrder) == 10
        assert self.trialInst.actualTrialOrder == ['A', 'A', 'B', 'B', 'C.X', 'C.E.Z','C.E.Y','C.E.X','C.B', 'D']

        # now let's try again with a block that starts with another block. Edge case.
        self.trialInst.actualTrialOrder = []
        self.trialInst.blockStartIndexes['C'] = []
        self.trialInst.blockStartIndexes['E'] = []
        self.trialInst.blockList['C']['trialList'] = ['E', 'X', 'B']
        self.trialInst.run(testMode=testOne)
        assert len(self.trialInst.actualTrialOrder) == 10
        assert self.trialInst.actualTrialOrder == ['A', 'A', 'B', 'B', 'C.E.Z', 'C.E.Y', 'C.E.X', 'C.X', 'C.B', 'D']

        # And with habituation
        self.trialInst.actualTrialOrder = []
        self.trialInst.blockList['Hab'] = {'trialList': ['B','C'],
                                        'habituation': 1,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'First',
                                        'habThresh': 5.0,
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': ['B']}
        self.trialInst.blockStartIndexes['Hab'] = []
        self.trialInst.trialOrder = ['A', 'A', 'B', 'B', 'Hab', 'D']
        self.trialInst.run(testMode=testOne)
        # Length is going to be...big...5+14+14*5 = 19+70=89. Recursion gets out of hand pretty quickly!
        assert len(self.trialInst.actualTrialOrder) == 89
        assert len([x for x in self.trialInst.actualTrialOrder if '^.C.B' in x]) == 14
        assert len(self.trialInst.actualTrialOrder)-2 == self.trialInst.maxHabIndex['Hab']



    def test_block_data_setup(self):
        self.trialInst.trialOrder = ['A', 'A', 'B', 'B', 'C', 'D']
        self.trialInst.blockList = {'C': {'trialList': ['X','E','B'],
                                        'habituation': 0,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'First',
                                        'habThresh': 5.0,
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': []},
                                    'E': {'trialList': ['Z','Y','X'],
                                        'habituation': 0,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'First',
                                        'habThresh': 5.0,
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': []}}
        self.trialInst.actualTrialOrder = []
        self.trialInst.blockStartIndexes['C'] = []
        self.trialInst.blockStartIndexes['E'] = []
        self.trialInst.blockDataList = ['E']
        self.trialInst.blockDataTags['E'] = []
        self.trialInst.run(testMode=testOne)
        assert self.trialInst.actualTrialOrder == ['A', 'A', 'B', 'B', 'C.X', 'C.E.Z','C.E.Y','C.E.X','C.B', 'D']
        assert self.trialInst.blockDataTags=={'E':[[6,7,8]]}
        self.trialInst.blockDataList=['C']
        self.trialInst.actualTrialOrder=[]
        self.trialInst.blockDataTags = {}
        self.trialInst.blockDataTags['C'] = []
        self.trialInst.blockStartIndexes['C'] = []
        self.trialInst.blockStartIndexes['E'] = []
        self.trialInst.run(testMode=testOne)
        assert self.trialInst.blockDataTags=={'C':[[5,6,7,8,9]]}
        self.trialInst.trialOrder = ['A', 'A', 'B', 'B', 'C', 'D','E']
        self.trialInst.actualTrialOrder = []
        self.trialInst.blockDataList = ['E']
        self.trialInst.blockDataTags={}
        self.trialInst.blockDataTags['E'] = []
        self.trialInst.blockStartIndexes['C'] = []
        self.trialInst.blockStartIndexes['E'] = []
        self.trialInst.run(testMode=testOne)
        assert self.trialInst.actualTrialOrder == ['A', 'A', 'B', 'B', 'C.X', 'C.E.Z','C.E.Y','C.E.X','C.B', 'D','E.Z','E.Y','E.X']
        assert self.trialInst.blockDataTags=={'E':[[6,7,8],[11,12,13]]}

    def test_multiyear_age(self):
        testTwo ={'snum':99, 'sID':'Test', 'sex':'NB', 'dob_m':'7', 'dob_d':'2', 'dob_y':'16', 'cond':'testcond',
                   'dot_m':'8', 'dot_d':'2', 'dot_y':'18'}
        self.trialInst.run(testMode=testTwo)

        assert self.trialInst.ageMo == 25
        assert self.trialInst.ageDay == 0

        testTwo ={'snum':99, 'sID':'Test', 'sex':'NB', 'dob_m':'7', 'dob_d':'2', 'dob_y':'16', 'cond':'testcond',
                   'dot_m':'8', 'dot_d':'1', 'dot_y':'18'}
        self.trialInst.run(testMode=testTwo)

        assert self.trialInst.ageMo == 24
        assert self.trialInst.ageDay == 30

    def test_four_digit_years(self):
        testTwo = {'snum': 99, 'sID': 'Test', 'sex': 'NB', 'dob_m': '7', 'dob_d': '2', 'dob_y': '2016',
                   'cond': 'testcond', 'dot_m': '8', 'dot_d': '2', 'dot_y': '18'}
        self.trialInst.run(testMode=testTwo)

        assert self.trialInst.ageMo == 25
        assert self.trialInst.ageDay == 0

        testTwo = {'snum': 99, 'sID': 'Test', 'sex': 'NB', 'dob_m': '7', 'dob_d': '2', 'dob_y': '16',
                   'cond': 'testcond', 'dot_m': '8', 'dot_d': '2', 'dot_y': '2018'}
        self.trialInst.run(testMode=testTwo)
        assert self.trialInst.ageMo == 25
        assert self.trialInst.ageDay == 0


    def test_condition_files(self):
        """
        To test condition files requires a condition file. The demo is handy here.

        :return:
        :rtype:
        """
        self.trialInst.condFile = 'PyHabDemo/conditions.csv'
        self.trialInst.stimNames = {'Test': ['3x2_2_2_1_1-converted.mp4', '3x2_2_3_1_1-converted.mp4'],
                                     'Intro': ['3x2_1_1_1-converted.mp4', '3x2_1_2_1_1-converted.mp4','Movie1','Movie2'],
                                     'Fam': ['3x2_1_3_1_1-converted.mp4', '3x2_2_1_1_1-converted.mp4']}
        self.trialInst.trialOrder = ['Intro', 'Fam', 'Test']
        self.trialInst.randPres = True
        self.trialInst.stimPres = True

        testTwo = {'snum':99, 'sID':'Test', 'sex':'NB', 'dob_m':'7', 'dob_d':'2', 'dob_y':'16', 'cond':'1'} # corresponds to {Intro:[1,2], Fam:[1,2], Test:[1,2]}
        self.trialInst.run(testMode=testTwo)

        # First make sure it won't go without condlist
        assert self.trialInst.stimNames['Intro'] == ['3x2_1_1_1-converted.mp4', '3x2_1_2_1_1-converted.mp4','Movie1','Movie2']
        self.trialInst.condList = ['1', '2', '3', '4','5','6','7','8']
        self.trialInst.run(testMode=testTwo)

        assert self.trialInst.stimNames['Intro'] == ['3x2_1_1_1-converted.mp4', '3x2_1_2_1_1-converted.mp4']
        assert self.trialInst.stimNames['Fam'] == ['3x2_1_3_1_1-converted.mp4', '3x2_2_1_1_1-converted.mp4']
        assert self.trialInst.stimNames['Test'] == ['3x2_2_2_1_1-converted.mp4']

class TestMultiHabBlock(object):
    """
    Tests various things that might come up with multiple habituation blocks.
    """

    def setup_class(self):
        mhab_settings = copy.deepcopy(base_settings)
        mhab_settings['blockList'] = "{'E':{'trialList': ['X'],'habituation': 1,'habByDuration': 0,'maxHabTrials': 14,'setCritWindow': 3,'setCritDivisor': 2.0,'setCritType': 'First','habThresh': 5.0,'metCritWindow': 3,'metCritDivisor': 1.0,'metCritStatic': 'Moving','calcHabOver': ['X']},'F':{'trialList': ['Z', 'Y', 'X'],'habituation': 1,'habByDuration': 0,'maxHabTrials': 14,'setCritWindow': 3,'setCritDivisor': 2.0,'setCritType': 'First','habThresh': 5.0,'metCritWindow': 3,'metCritDivisor': 1.0,'metCritStatic': 'Moving','calcHabOver': ['Y','X']}}"
        mhab_settings['trialOrder'] = "['A','A','E','B','F','C']"
        self.habInst = PH.PyHab(mhab_settings, testMode=True)
        mhab_settings2 = mhab_settings
        mhab_settings2['blockList'] = "{'E':{'trialList': ['X'],'habituation': 1,'habByDuration': 0,'maxHabTrials': 6,'setCritWindow': 3,'setCritDivisor': 2.0,'setCritType': 'First','habThresh': 5.0,'metCritWindow': 3,'metCritDivisor': 1.0,'metCritStatic': 'Moving','calcHabOver': ['X']},'F':{'trialList': ['Z', 'Y', 'X'],'habituation': 1,'habByDuration': 0,'maxHabTrials': 6,'setCritWindow': 3,'setCritDivisor': 2.0,'setCritType': 'First','habThresh': 5.0,'metCritWindow': 3,'metCritDivisor': 1.0,'metCritStatic': 'Moving','calcHabOver': ['Y','X']}}"
        self.habInst2 = PH.PyHab(mhab_settings2, testMode=True)

        self.testMatrix = [{'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                            'condLabel': 'dataTest', 'trial': 1, 'GNG': 1, 'trialType': 'A', 'stimName': 'movie1.mov',
                            'habCrit': 0, 'sumOnA': 3.0, 'numOnA': 2, 'sumOffA': 3.5,
                            'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                           {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                            'condLabel': 'dataTest', 'trial': 2, 'GNG': 1, 'trialType': 'A',
                            'stimName': 'movie2.mov', 'habCrit': 0, 'sumOnA': 3.0, 'numOnA': 2, 'sumOffA': 3.5,
                            'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}]

        # Data that can be added iteratively to simulate hab trials for the first hab block
        self.firstHabTrialsMatrix = [{'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                            'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'E.X', 'stimName': 'movie1.mov',
                            'habCrit': 0, 'sumOnA': 8.0, 'numOnA': 2, 'sumOffA': 3.5,
                            'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                             {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                              'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'E.X',
                              'stimName': 'movie2.mov', 'habCrit': 0, 'sumOnA': 8.0, 'numOnA': 2, 'sumOffA': 3.5,
                              'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                             {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                              'condLabel': 'dataTest', 'trial': 5, 'GNG': 1, 'trialType': 'E.X',
                              'stimName': 'movie2.mov', 'habCrit': 0, 'sumOnA': 8.0, 'numOnA': 2,'sumOffA': 3.5,
                              'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                             {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                              'condLabel': 'dataTest', 'trial': 6, 'GNG': 1, 'trialType': 'E.X',
                              'stimName': 'movie2.mov', 'habCrit': 12.0, 'sumOnA': 3.0, 'numOnA': 2,'sumOffA': 3.5,
                              'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                             {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                              'condLabel': 'dataTest', 'trial': 7, 'GNG': 1, 'trialType': 'E.X',
                              'stimName': 'movie2.mov', 'habCrit': 12.0, 'sumOnA': 3.0, 'numOnA': 2,'sumOffA': 3.5,
                              'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                             {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                              'condLabel': 'dataTest', 'trial': 8, 'GNG': 1, 'trialType': 'E.X',
                              'stimName': 'movie2.mov', 'habCrit': 12.0, 'sumOnA': 3.0, 'numOnA': 2,'sumOffA': 3.5,
                              'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}]

        self.firstTestTrialMatrix = [{'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                            'condLabel': 'dataTest', 'trial': 9, 'GNG': 1, 'trialType': 'B', 'stimName': 'movie2.mov',
                            'habCrit': 0, 'sumOnA': 15.0, 'numOnA': 2, 'sumOffA': 3.5,
                            'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}]

        self.secondHabTrialMatrix = [{'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                            'condLabel': 'dataTest', 'trial': 10, 'GNG': 1, 'trialType': 'F.Z', 'stimName': 'movie14.mov',
                            'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                            'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 11, 'GNG': 1, 'trialType': 'F.Y',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 0, 'sumOnA': 4.0, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 12, 'GNG': 1, 'trialType': 'F.X',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 0, 'sumOnA': 4.0, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 13, 'GNG': 1, 'trialType': 'F.Z',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 0, 'sumOnA': 8.0, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 14, 'GNG': 1, 'trialType': 'F.Y',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 0, 'sumOnA': 4.0, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 15, 'GNG': 1, 'trialType': 'F.X',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 0, 'sumOnA': 4.0, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 16, 'GNG': 1, 'trialType': 'F.Z',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 0, 'sumOnA': 8.0, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 17, 'GNG': 1, 'trialType': 'F.Y',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 0, 'sumOnA': 4.0, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 18, 'GNG': 1, 'trialType': 'F.X',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 0, 'sumOnA': 4.0, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 16, 'GNG': 1, 'trialType': 'F.Z',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 0, 'sumOnA': 8.0, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 17, 'GNG': 1, 'trialType': 'F.Y',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 0, 'sumOnA': 4.0, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 18, 'GNG': 1, 'trialType': 'F.X',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 0, 'sumOnA': 4.0, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 19, 'GNG': 1, 'trialType': 'F.Z',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 12.0, 'sumOnA': 8.0, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 20, 'GNG': 1, 'trialType': 'F.Y',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 12.0, 'sumOnA': 1.5, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 21, 'GNG': 1, 'trialType': 'F.X',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 12.0, 'sumOnA': 1.5, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 22, 'GNG': 1, 'trialType': 'F.Z',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 12.0, 'sumOnA': 8.0, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 23, 'GNG': 1, 'trialType': 'F.Y',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 12.0, 'sumOnA': 1.5, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 24, 'GNG': 1, 'trialType': 'F.X',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 12.0, 'sumOnA': 1.5, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 25, 'GNG': 1, 'trialType': 'F.Z',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 12.0, 'sumOnA': 8.0, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 26, 'GNG': 1, 'trialType': 'F.Y',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 12.0, 'sumOnA': 1.5, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2},
                                     {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                      'condLabel': 'dataTest', 'trial': 27, 'GNG': 1, 'trialType': 'F.X',
                                      'stimName': 'movie14.mov',
                                      'habCrit': 12.0, 'sumOnA': 1.5, 'numOnA': 2, 'sumOffA': 3.5,
                                      'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
                                     ]

    def teardown_class(self):
        del self.habInst
        del self.habInst2

    def test_initial_setup(self):
        self.habInst.run(testMode=testOne)

        assert 'E' in self.habInst.habCount.keys()
        assert 'E' in self.habInst.habCrit.keys()
        assert 'E' in self.habInst.habSetWhen.keys()
        assert 'E' in self.habInst.habMetWhen.keys()
        assert 'E' in self.habInst.maxHabIndex.keys()
        assert 'E' in self.habInst.habDataCompiled.keys()
        assert 'F' in self.habInst.habCount.keys()
        assert 'F' in self.habInst.habCrit.keys()
        assert 'F' in self.habInst.habSetWhen.keys()
        assert 'F' in self.habInst.habMetWhen.keys()
        assert 'F' in self.habInst.maxHabIndex.keys()
        assert 'F' in self.habInst.habDataCompiled.keys()

        assert len(self.habInst.actualTrialOrder) == 60 # 14+14*3+4 = 14*4+4 = 60

    def test_first_checkstop(self):
        # Simulate up to a set of circumstances that would result in checkstop being true.
        habMatrix = copy.deepcopy(self.testMatrix)
        habMatrix.append(self.firstHabTrialsMatrix[0])
        self.habInst.dataMatrix = habMatrix
        self.habInst.stimPres = True  # Temporary, so it doesn't try to play the end-hab sound.
        self.habInst.habDataCompiled['E'][self.habInst.habCount['E']] += self.habInst.dataMatrix[-1]['sumOnA']
        self.habInst.habCount['E'] += 1
        assert self.habInst.checkStop('E') == False

        self.habInst.dataMatrix.append(self.firstHabTrialsMatrix[1])
        self.habInst.habDataCompiled['E'][self.habInst.habCount['E']] += self.habInst.dataMatrix[-1]['sumOnA']
        self.habInst.habCount['E'] += 1
        self.habInst.dataMatrix.append(self.firstHabTrialsMatrix[2])
        self.habInst.habDataCompiled['E'][self.habInst.habCount['E']] += self.habInst.dataMatrix[-1]['sumOnA']
        self.habInst.habCount['E'] += 1
        assert self.habInst.checkStop('E') == False
        assert self.habInst.habCrit['E'] == 12.0 #24/2=12
        assert self.habInst.habSetWhen['E'] == 3

        self.habInst.dataMatrix.append(self.firstHabTrialsMatrix[3])
        self.habInst.habDataCompiled['E'][self.habInst.habCount['E']] += self.habInst.dataMatrix[-1]['sumOnA']
        self.habInst.habCount['E'] += 1
        self.habInst.dataMatrix.append(self.firstHabTrialsMatrix[4])
        self.habInst.habDataCompiled['E'][self.habInst.habCount['E']] += self.habInst.dataMatrix[-1]['sumOnA']
        self.habInst.habCount['E'] += 1
        self.habInst.dataMatrix.append(self.firstHabTrialsMatrix[5])
        self.habInst.habDataCompiled['E'][self.habInst.habCount['E']] += self.habInst.dataMatrix[-1]['sumOnA']
        self.habInst.habCount['E'] += 1
        assert self.habInst.checkStop('E') == True
        assert self.habInst.habMetWhen['E'] == 6

    def test_first_jump(self):
        self.habInst.stimNames = {'A': ['Movie1', 'Movie2', 'Movie3', 'Movie4'],
                                      'B': ['Movie5', 'Movie6', 'Movie7', 'Movie8'],
                                      'C': ['Movie1', 'Movie2', 'Movie3', 'Movie4'],
                                      'D': ['Movie9', 'Movie10'],
                                      'X': ['Movie12'],
                                      'Y': ['Movie13'],
                                      'Z': ['Movie14']}
        self.habInst.stimDict = {'A': ['Movie1', 'Movie2'],
                                     'B': ['Movie5', 'Movie6'],
                                     'C': ['Movie1', 'Movie2'],
                                     'D': ['Movie9', 'Movie10'],
                                     'X': ['Movie12'],
                                     'Y': ['Movie13'],
                                     'Z': ['Movie14']}

        self.habInst.counters = {'A':2, 'B':0,'C':0,'D':0, 'X':6, 'Y':0, 'Z':0}

        [x, y] = self.habInst.jumpToTest(9, 'E') # Because jumpToTest is being called from the trial AFTER habituation

        assert x == 'Movie5'
        assert y == 'B'
        assert self.habInst.actualTrialOrder[7] == 'E6*^.X'
        assert self.habInst.actualTrialOrder[8] == 'B'
        assert len(self.habInst.actualTrialOrder) == 52

    def test_insert_first(self):
        [x, y] = self.habInst.insertHab(9,'E')
        print(self.habInst.actualTrialOrder)
        assert x == 'Movie12'
        assert y == 'X'
        assert len(self.habInst.actualTrialOrder) == 53  # Up one from before.
        assert self.habInst.habCount['E'] == 6  # Something off in the hab counter?
        assert self.habInst.actualTrialOrder[7] == 'E6*^.X'  # Reconfirm previous trial.
        assert self.habInst.actualTrialOrder[8] == 'E7*^.X'  # Test that this is the right trial.
        assert self.habInst.actualTrialOrder[9] == 'B'  # Confirm the test trial hasn't moved.


    def test_second_checkstop(self):
        self.habInst.dataMatrix.append(self.firstTestTrialMatrix[0])
        for j in range(0, 6):
            self.habInst.dataMatrix.append(self.secondHabTrialMatrix[j])
            if self.habInst.dataMatrix[-1]['trialType'] in ['F.Y', 'F.X']:
                self.habInst.habDataCompiled['F'][self.habInst.habCount['F']] += self.habInst.dataMatrix[-1]['sumOnA']
            self.habInst.habCount['F'] = math.floor(j/3)+1
            assert self.habInst.checkStop('F') == False
            assert self.habInst.habSetWhen['F'] == -1
        for k in range(6,9):
            self.habInst.dataMatrix.append(self.secondHabTrialMatrix[k])
            if self.habInst.dataMatrix[-1]['trialType'] in ['F.Y', 'F.X']:
                self.habInst.habDataCompiled['F'][self.habInst.habCount['F']] += self.habInst.dataMatrix[-1]['sumOnA']

        self.habInst.habCount['F'] = 3
        assert self.habInst.checkStop('F') == False
        assert self.habInst.habSetWhen['F'] == 3
        assert self.habInst.habCrit['F'] == 12.0

        for a in range(9,12):
            self.habInst.dataMatrix.append(self.secondHabTrialMatrix[a])
            if self.habInst.dataMatrix[-1]['trialType'] in ['F.Y', 'F.X']:
                self.habInst.habDataCompiled['F'][self.habInst.habCount['F']] += self.habInst.dataMatrix[-1]['sumOnA']
        self.habInst.habCount['F'] = 4
        assert self.habInst.habDataCompiled['F'][3] == 8.0
        assert self.habInst.checkStop('F') == False
        assert self.habInst.habSetWhen['F'] == 3
        assert self.habInst.habCrit['F'] == 12.0

        for a in range(12,15):
            self.habInst.dataMatrix.append(self.secondHabTrialMatrix[a])
            if self.habInst.dataMatrix[-1]['trialType'] in ['F.Y', 'F.X']:
                self.habInst.habDataCompiled['F'][self.habInst.habCount['F']] += self.habInst.dataMatrix[-1]['sumOnA']
        self.habInst.habCount['F'] = 5
        assert self.habInst.habDataCompiled['F'][4] == 3.0
        assert self.habInst.checkStop('F') == False
        assert self.habInst.habSetWhen['F'] == 3
        assert self.habInst.habCrit['F'] == 12.0

        for a in range(15,18):
            self.habInst.dataMatrix.append(self.secondHabTrialMatrix[a])
            if self.habInst.dataMatrix[-1]['trialType'] in ['F.Y', 'F.X']:
                self.habInst.habDataCompiled['F'][self.habInst.habCount['F']] += self.habInst.dataMatrix[-1]['sumOnA']
        self.habInst.habCount['F'] = 6
        assert self.habInst.habDataCompiled['F'][5] == 3.0
        assert self.habInst.checkStop('F') == False
        assert self.habInst.habSetWhen['F'] == 3
        assert self.habInst.habCrit['F'] == 12.0

        for a in range(18,len(self.secondHabTrialMatrix)):
            self.habInst.dataMatrix.append(self.secondHabTrialMatrix[a])
            if self.habInst.dataMatrix[-1]['trialType'] in ['F.Y', 'F.X']:
                self.habInst.habDataCompiled['F'][self.habInst.habCount['F']] += self.habInst.dataMatrix[-1]['sumOnA']
        self.habInst.habCount['F'] = 7
        assert self.habInst.checkStop('F') == True
        assert self.habInst.habMetWhen['F'] == 7
        assert self.habInst.habSetWhen['F'] == 3
        assert self.habInst.habCrit['F'] == 12.0

    def test_second_jump(self):
        [x,y] = self.habInst.jumpToTest(28,'F')

        assert x == 'Movie1'
        assert y == 'C'
        assert len(self.habInst.actualTrialOrder) == 28

    def test_second_insert(self):
        [x, y] = self.habInst.insertHab(28, 'F')

        print(self.habInst.actualTrialOrder)

        assert x == 'Movie14'
        assert y == 'Z'
        assert len(self.habInst.actualTrialOrder) == 31  # Up three from before because it's a 3-trial block

    def test_short_hab(self):
        # A specialized test for an edge case involving a very low number of maxhabtrials
        self.habInst2.run(testMode=testOne)

        assert len(self.habInst2.actualTrialOrder) == 28  # 6+6*3+4 = 6*4+4 = 28
        assert self.habInst2.actualTrialOrder[0:6] == ['A', 'A', 'E1*^.X', 'E2*^.X', 'E3*^.X', 'E4*^.X']
        self.habInst2.stimPres = True
        self.habInst2.stimNames = {'A': ['Movie1', 'Movie2', 'Movie3', 'Movie4'],
                                  'B': ['Movie5', 'Movie6', 'Movie7', 'Movie8'],
                                  'C': ['Movie1', 'Movie2', 'Movie3', 'Movie4'],
                                  'D': ['Movie9', 'Movie10'],
                                  'X': ['Movie12'],
                                  'Y': ['Movie13'],
                                  'Z': ['Movie14']}
        self.habInst2.stimDict = {'A': ['Movie1', 'Movie2'],
                                 'B': ['Movie5', 'Movie6'],
                                 'C': ['Movie1', 'Movie2'],
                                 'D': ['Movie9', 'Movie10'],
                                 'X': ['Movie12'],
                                 'Y': ['Movie13'],
                                 'Z': ['Movie14']}

        self.habInst2.counters = {'A': 2, 'B': 0, 'C': 0, 'D': 0, 'X': 6, 'Y': 0, 'Z': 0}

        [x, y] = self.habInst2.jumpToTest(8, 'E')  # essentially from hab trial 5.
        assert x == 'Movie5'
        assert y == 'B'
        assert self.habInst2.actualTrialOrder[6] == 'E5*^.X'
        assert self.habInst2.actualTrialOrder[7] == 'B'
        assert len(self.habInst2.actualTrialOrder) == 27

class TestHabNaming(object):
    """
    Tests for what appears to be a strange edge case in the naming of a particular study.
    """
    def setup_class(self):
        hab3_settings = copy.deepcopy(base_settings)
        hab3_settings['blockList'] = "{'HAB_A': {'habituation': True, 'maxHabTrials': 6, 'setCritWindow': 3, 'setCritDivisor': 2.0, 'setCritType': 'First', 'habThresh': 5.0, 'maxHabSet':-1, 'metCritWindow': 3, 'metCritDivisor': 1.0, 'metCritStatic': 'Moving', 'habByDuration': 0, 'calcHabOver': 'Vid1', 'trialList': ['Vid1'], 'blockRedo': False}, 'HAB_B': {'habituation': True, 'maxHabTrials': 6, 'setCritWindow': 3, 'setCritDivisor': 2.0, 'setCritType': 'First', 'habThresh': 5.0, 'maxHabSet':-1, 'metCritWindow': 3, 'metCritDivisor': 1.0, 'metCritStatic': 'Moving', 'habByDuration': 0, 'calcHabOver': 'Vid2', 'trialList': ['Vid2'], 'blockRedo': False}}"
        hab3_settings['trialOrder'] = "['HAB_A', 'Test1', 'Test2', 'HAB_B', 'Test3', 'Test4']"
        hab3_settings['trialTypes'] = "['Test1', 'Test2', 'Test3', 'Test4', 'Vid1', 'Vid2', 'HAB_A', 'HAB_B']"
        hab3_settings['stimNames'] = "{'Test1': ['Asian_A_D_updated.png', 'Asian_B_C.png', 'Asian_C_B.png', 'Asian_D_A.png', 'Caucasian_A_D.png', 'Caucasian_B_C.png', 'Caucasian_C_B.png', 'Caucasian_D_A.png'], 'Test2': ['Asian_A_D_updated.png', 'Asian_B_C.png', 'Asian_C_B.png', 'Asian_D_A.png', 'Caucasian_A_D.png', 'Caucasian_B_C.png', 'Caucasian_C_B.png', 'Caucasian_D_A.png'], 'Test3': ['Asian_A_D_updated.png', 'Asian_B_C.png', 'Asian_C_B.png', 'Asian_D_A.png', 'Caucasian_A_D.png', 'Caucasian_B_C.png', 'Caucasian_C_B.png', 'Caucasian_D_A.png'], 'Test4': ['Asian_A_D_updated.png', 'Asian_B_C.png', 'Asian_C_B.png', 'Asian_D_A.png', 'Caucasian_A_D.png', 'Caucasian_B_C.png', 'Caucasian_C_B.png', 'Caucasian_D_A.png'], 'Vid1': ['Asian_A.mov', 'Asian_B.mov', 'Asian_C.mov', 'Asian_D.mov', 'Caucasian_A.mov', 'Caucasian_B.mov', 'Caucasian_C.mov', 'Caucasian_D.mov'], 'Vid2': ['Asian_A.mov', 'Asian_B.mov', 'Asian_C.mov', 'Asian_D.mov', 'Caucasian_A.mov', 'Caucasian_B.mov', 'Caucasian_C.mov', 'Caucasian_D.mov']}"
        hab3_settings['autoAdvance'] = "['Test4', 'Test2']"

        self.habInst3 = PH.PyHab(hab3_settings, testMode=True)

    def teardown_class(self):
        del self.habInst3

    def test_initial_setup(self):
        self.habInst3.run(testMode=testOne)

        assert 'HAB_A' in self.habInst3.habCount.keys()
        assert 'HAB_A' in self.habInst3.habCrit.keys()
        assert 'HAB_A' in self.habInst3.habSetWhen.keys()
        assert 'HAB_A' in self.habInst3.habMetWhen.keys()
        assert 'HAB_A' in self.habInst3.maxHabIndex.keys()
        assert 'HAB_B' in self.habInst3.habDataCompiled.keys()
        assert 'HAB_B' in self.habInst3.habCount.keys()
        assert 'HAB_B' in self.habInst3.habCrit.keys()
        assert 'HAB_B' in self.habInst3.habSetWhen.keys()
        assert 'HAB_B' in self.habInst3.habMetWhen.keys()
        assert 'HAB_B' in self.habInst3.maxHabIndex.keys()
        assert 'HAB_B' in self.habInst3.habDataCompiled.keys()

        assert len(self.habInst3.actualTrialOrder) == 16
        assert self.habInst3.actualTrialOrder[0] == 'HAB_A1*^.Vid1'
        assert self.habInst3.actualTrialOrder[8] == 'HAB_B1*^.Vid2'

class TestCommands(object):
    """
    Tests the setup and operation of redo, jump, insert hab, etc.
    """

    def setup_class(self):
        trial_settings = copy.deepcopy(base_settings)
        trial_settings['trialOrder'] = "['A','A','B','B','C','C','D']"

        self.commandInst = PH.PyHab(trial_settings, testMode=True)
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


        [x, y] = self.commandInst.redoSetup(2,self.commandInst.autoAdvance,'A')
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
        [x, y] = self.commandInst.redoSetup(3,['B'],'B')
        assert y == 2
        assert x == "Movie2"

        self.commandInst.verbDatList = copy.deepcopy(self.testDatList)
        self.commandInst.dataMatrix = copy.deepcopy(self.testMatrix)
        self.commandInst.autoAdvance = ['B']
        self.commandInst.counters = {'A': 2, 'B': 2, 'C': 0, 'D': 0}
        self.commandInst.dataMatrix.append(temp1)
        self.commandInst.dataMatrix.append(temp2)
        [x, y] = self.commandInst.redoSetup(4,['B'],'B')
        assert y == 2
        assert x == "Movie2"

    def test_jump_and_insert(self):
        self.commandInst.trialText = mock.MagicMock()
        self.commandInst.stimPres = True
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
        self.commandInst.blockList = {'Z': {'trialList': ['Hab'],
                                        'habituation': 1,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'First',
                                        'habThresh': 5.0,
                                        'maxHabSet': -1,
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': ['Hab']}}
        self.commandInst.blockStartIndexes['Z'] = []
        self.commandInst.trialOrder = ['A', 'A', 'B', 'B', 'Z', 'D']
        self.commandInst.counters = {'A': 2, 'B': 2, 'C': 0, 'D': 0,'Hab':2}
        self.commandInst.run(testMode=testOne)

        # Because hab counters and stuff are made on init rather than run, they need to be done manually here
        i='Z'
        self.commandInst.habCount[i] = 0
        self.commandInst.habCrit[i] = 0
        self.commandInst.habSetWhen[i] = -1
        self.commandInst.habMetWhen[i] = -1
        self.commandInst.maxHabIndex[i] = 0
        self.commandInst.habDataCompiled[i] = [0] * self.commandInst.blockList[i]['maxHabTrials']

        [x, y] = self.commandInst.jumpToTest(7,'Z')
        assert x == 'Movie9'
        assert y == 'D'
        assert self.commandInst.actualTrialOrder ==['A', 'A', 'B', 'B', 'Z1*^.Hab', 'Z2*^.Hab','D']

        self.commandInst.stimPres = False # Insert would require loading movies otherwise. Requires manual testing.
        self.commandInst.habCount['Z'] = 1
        [x,y] = self.commandInst.insertHab(7,'Z')
        assert x == 0
        assert y == 'Hab'

        self.commandInst.stimPres = True
        self.commandInst.blockList={'Hab': {'trialList': ['B','C'],
               'habituation': 1,
               'habByDuration': 0,
               'maxHabTrials': 14,
               'setCritWindow': 3,
               'setCritDivisor': 2.0,
               'setCritType': 'First',
               'habThresh': 5.0,
               'maxHabSet': -1,
               'metCritWindow': 3,
               'metCritDivisor': 1.0,
               'metCritStatic': 'Moving',
               'calcHabOver': ['B']}}
        self.commandInst.blockStartIndexes['Hab'] = []
        self.commandInst.trialOrder = ['A', 'A', 'B', 'B', 'Hab', 'D']
        self.commandInst.counters = {'A': 2, 'B': 2, 'C': 1, 'D': 0,'Hab':1}

        i = 'Hab'
        self.commandInst.habCount[i] = 0
        self.commandInst.habCrit[i] = 0
        self.commandInst.habSetWhen[i] = -1
        self.commandInst.habMetWhen[i] = -1
        self.commandInst.maxHabIndex[i] = 0
        self.commandInst.habDataCompiled[i] = [0] * self.commandInst.blockList[i]['maxHabTrials']
        self.commandInst.run(testMode=testOne)

        assert len(self.commandInst.actualTrialOrder) == 33
        assert self.commandInst.actualTrialOrder[32] == 'D'

        [x, y] = self.commandInst.jumpToTest(7,'Hab')
        assert x == 'Movie9'
        assert y == 'D'
        assert self.commandInst.actualTrialOrder == ['A', 'A', 'B', 'B', 'Hab1*.B', 'Hab1*^.C', 'D']

        self.commandInst.stimPres = False
        self.commandInst.habCount['Hab'] = 1
        [x, y] = self.commandInst.insertHab(7,'Hab')
        assert x == 0
        assert y == 'B'
        assert self.commandInst.actualTrialOrder == ['A', 'A', 'B', 'B', 'Hab1*.B', 'Hab1*^.C','Hab2*.B','Hab2*^.C','D']

        # Test something down the line!
        self.commandInst.stimPres = True
        [x, y] = self.commandInst.insertHab(9,'Hab', 2)
        assert x == 0
        assert y == 'B'
        assert self.commandInst.actualTrialOrder == ['A', 'A', 'B', 'B', 'Hab1*.B', 'Hab1*^.C','Hab2*.B','Hab2*^.C','Hab3*.B','Hab3*^.C','D']


    def test_setupredo_hab(self):
        """
        Specifically for testing redos of hab trials, which can get...complicated.
        :return:
        :rtype:
        """
        self.commandInst.trialText = mock.MagicMock()
        self.commandInst.stimPres = True
        self.commandInst.stimNames = {'A': ['Movie1', 'Movie2', 'Movie3', 'Movie4'],
                                      'B': ['Movie5', 'Movie6', 'Movie7', 'Movie8'],
                                      'C': ['Movie1', 'Movie2', 'Movie3', 'Movie4'],
                                      'D': ['Movie9', 'Movie10'],
                                      'H': ['Movie11']}
        self.commandInst.stimDict = {'A': ['Movie1', 'Movie2'],
                                     'B': ['Movie5', 'Movie6'],
                                     'C': ['Movie1', 'Movie2'],
                                     'D': ['Movie9', 'Movie10'],
                                     'H': ['Movie11']}
        self.commandInst.trialOrder = ['A', 'A', 'B', 'B', 'Hab', 'C']
        self.commandInst.autoAdvance = ['B','C']
        self.commandInst.blockList = {'Hab': {'trialList': ['H','C'],
               'habituation': 1,
               'habByDuration': 0,
               'maxHabTrials': 14,
               'setCritWindow': 3,
               'setCritDivisor': 2.0,
               'setCritType': 'First',
               'habThresh': 5.0,
               'maxHabSet': -1,
               'metCritWindow': 3,
               'metCritDivisor': 1.0,
               'metCritStatic': 'Moving',
               'calcHabOver': ['H','C']}}
        self.commandInst.blockStartIndexes['Hab'] = []
        i = 'Hab'
        self.commandInst.habCount[i] = 0
        self.commandInst.habCrit[i] = 0
        self.commandInst.habSetWhen[i] = -1
        self.commandInst.habMetWhen[i] = -1
        self.commandInst.maxHabIndex[i] = 0
        self.commandInst.habDataCompiled[i] = [0] * self.commandInst.blockList[i]['maxHabTrials']

        self.commandInst.counters = {'A': 2, 'B': 2, 'C': 0, 'D': 0, 'H': 0}
        self.commandInst.run(testMode=testOne)
        self.commandInst.habMetWhen['Hab'] = -1 # Resetting after the jump tests above on principle.
        self.commandInst.verbDatList = copy.deepcopy(self.testDatList)
        self.commandInst.dataMatrix = copy.deepcopy(self.testMatrix)





        temp0 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'B', 'stimName': 'Movie12.mov',
                 'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        tempA = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'B', 'stimName': 'Movie12.mov',
                 'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}

        self.commandInst.dataMatrix.append(temp0)
        self.commandInst.dataMatrix.append(tempA)

        temp1 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 5, 'GNG': 1, 'trialType': 'Hab.H', 'stimName': 'Movie12.mov',
                 'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        temp2 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 6, 'GNG': 1, 'trialType': 'Hab.C',
                 'stimName': 'Movie1.mov', 'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        self.commandInst.dataMatrix.append(temp1)
        self.commandInst.dataMatrix.append(temp2)
        temp3 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 7, 'GNG': 1, 'trialType': 'Hab.H', 'stimName': 'movie5.mov',
                 'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        temp4 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 8, 'GNG': 1, 'trialType': 'Hab.C',
                 'stimName': 'movie2.mov', 'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        temp5 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 9, 'GNG': 1, 'trialType': 'Hab.H', 'stimName': 'movie5.mov',
                 'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        temp6 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 10, 'GNG': 1, 'trialType': 'Hab.C',
                 'stimName': 'movie2.mov', 'habCrit': 15.0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        self.commandInst.dataMatrix.append(temp3)
        self.commandInst.dataMatrix.append(temp4)
        self.commandInst.dataMatrix.append(temp5)
        self.commandInst.dataMatrix.append(temp6)
        self.commandInst.habDataCompiled['Hab'] = [0]*self.commandInst.blockList['Hab']['maxHabTrials']
        self.commandInst.habDataCompiled['Hab'][0:2] = [10,10,10]  # Need to set this manually too because it's all handled by doTrial.
        self.commandInst.habCount['Hab'] = 3

        assert self.commandInst.checkStop('Hab') == False
        assert self.commandInst.habSetWhen['Hab'] == 3
        assert self.commandInst.habCrit['Hab'] == 15
        # OK, assuming all that got set up properly, lets get messy.
        [x,y] = self.commandInst.redoSetup(11, ['B','C'], 'Hab')
        assert y == 9  # The start of the last hab block iteration, in principle.
        assert self.commandInst.habDataCompiled['Hab'][2] == 0
        assert self.commandInst.habSetWhen['Hab'] == -1
        assert self.commandInst.habMetWhen['Hab'] == -1
        assert self.commandInst.habCrit['Hab'] == 0
        assert self.commandInst.habCount['Hab'] == 2

        self.commandInst.dataMatrix.append(temp5)
        self.commandInst.dataMatrix.append(temp6)
        self.commandInst.habDataCompiled['Hab'][2] = 10
        self.commandInst.habCount['Hab'] = 3
        assert self.commandInst.checkStop('Hab') == False # Reset
        assert self.commandInst.habSetWhen['Hab'] == 3
        assert self.commandInst.habMetWhen['Hab'] == -1

        # Now things get a little wild.
        temp7 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 11, 'GNG': 1, 'trialType': 'hab.H', 'stimName': 'movie5.mov',
                 'habCrit': 15.0, 'sumOnA': 1.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        temp8 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 12, 'GNG': 1, 'trialType': 'hab.C',
                 'stimName': 'movie2.mov', 'habCrit': 15.0, 'sumOnA': 1.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        self.commandInst.dataMatrix.append(temp7)
        self.commandInst.dataMatrix.append(temp8)
        self.commandInst.habDataCompiled['Hab'][3] = 2
        self.commandInst.habCount['Hab'] = 4
        temp9 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 13, 'GNG': 1, 'trialType': 'Hab.H', 'stimName': 'movie5.mov',
                 'habCrit': 15.0, 'sumOnA': 1.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        temp10 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 14, 'GNG': 1, 'trialType': 'Hab.C',
                 'stimName': 'movie2.mov', 'habCrit': 15.0, 'sumOnA': 1.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        self.commandInst.dataMatrix.append(temp9)
        self.commandInst.dataMatrix.append(temp10)
        self.commandInst.habDataCompiled['Hab'][4] = 2
        self.commandInst.habCount['Hab'] = 5
        temp11 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 15, 'GNG': 1, 'trialType': 'Hab.H', 'stimName': 'movie5.mov',
                 'habCrit': 15.0, 'sumOnA': 1.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        temp12 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                  'condLabel': 'dataTest', 'trial': 16, 'GNG': 1, 'trialType': 'Hab.C',
                  'stimName': 'movie2.mov', 'habCrit': 15.0, 'sumOnA': 1.0, 'numOnA': 2, 'sumOffA': 3.5,
                  'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        self.commandInst.dataMatrix.append(temp11)
        self.commandInst.dataMatrix.append(temp12)
        self.commandInst.habDataCompiled['Hab'][5] = 2
        self.commandInst.habCount['Hab'] = 6

        assert len(self.commandInst.actualTrialOrder) == 33  # check initial
        assert self.commandInst.checkStop('Hab') == True
        assert self.commandInst.habMetWhen['Hab'] == 6
        self.commandInst.jumpToTest(17,'Hab')
        assert len(self.commandInst.actualTrialOrder) == 17
        assert self.commandInst.actualTrialOrder[16] == 'C'
        self.commandInst.redoSetup(17,['B','C'],'Hab') # Because C is auto-redo, it should go back one step.
        assert self.commandInst.checkStop('Hab') == False
        assert self.commandInst.habMetWhen['Hab'] == -1
        assert len(self.commandInst.actualTrialOrder) == 33
        assert self.commandInst.habCount['Hab'] == 5
        assert len(self.commandInst.dataMatrix) == 14

        self.commandInst.blockList['Hab']['setCritType'] = 'Max'
        self.commandInst.redoSetup(15,['B','C'],'Hab') # This is actually something that would never come up - you can't redo twice in a row
        assert self.commandInst.habCount['Hab'] == 4
        assert len(self.commandInst.actualTrialOrder) == 33
        assert self.commandInst.habCrit['Hab'] == 15 # Should as yet be unchanged

        temp10['sumOnA'] = 12
        self.commandInst.dataMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 13, 'GNG': 1, 'trialType': 'Hab.H', 'stimName': 'movie5.mov',
                 'habCrit': 15.0, 'sumOnA': 1.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2})
        self.commandInst.dataMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 14, 'GNG': 1, 'trialType': 'Hab.C',
                 'stimName': 'movie2.mov', 'habCrit': 15.0, 'sumOnA': 12, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2})
        self.commandInst.habDataCompiled['Hab'][4] = 12
        self.commandInst.habCount['Hab'] = 5
        assert self.commandInst.checkStop('Hab') == False
        assert self.commandInst.habCrit['Hab'] == 16
        assert self.commandInst.habSetWhen['Hab'] == 5
        self.commandInst.redoSetup(15,['B','C'],'Hab')
        assert self.commandInst.checkStop('Hab') == False
        assert self.commandInst.habCrit['Hab'] == 15
        assert self.commandInst.habSetWhen['Hab'] == 3  # Because of new habSetWhen calculation.


        self.commandInst.blockList['Hab']['setCritType'] = 'Peak' # Really need to go back and set this initially!
        self.commandInst.habDataCompiled['Hab'][3] = 12  # peak window hab 2/3/4
        self.commandInst.dataMatrix[3]['sumOnA'] = 12
        assert self.commandInst.checkStop('Hab') == False
        assert self.commandInst.habCrit['Hab'] == 16
        assert self.commandInst.habSetWhen['Hab'] == 4

        temp10['sumOnA'] = 2
        self.commandInst.dataMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 13, 'GNG': 1, 'trialType': 'Hab.H', 'stimName': 'movie5.mov',
                 'habCrit': 15.0, 'sumOnA': 1.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2})
        self.commandInst.dataMatrix.append({'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 14, 'GNG': 1, 'trialType': 'Hab.C',
                 'stimName': 'movie2.mov', 'habCrit': 15.0, 'sumOnA': 2, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2})
        self.commandInst.habDataCompiled['Hab'][4] = 2
        self.commandInst.habCount['Hab'] = 5
        assert self.commandInst.checkStop('Hab') == False
        assert self.commandInst.habCrit['Hab'] == 16
        assert self.commandInst.habSetWhen['Hab'] == 4
        self.commandInst.redoSetup(15, ['B', 'C'],'Hab')
        assert self.commandInst.checkStop('Hab') == False
        assert self.commandInst.habCrit['Hab'] == 16
        assert self.commandInst.habSetWhen['Hab'] == 4  # Verifying unchanged.

    def test_blockredo(self):
        self.commandInst.blockList = {'C': {'trialList': ['X', 'E', 'B'],
                                            'habituation': 0,
                                            'habByDuration': 0,
                                            'maxHabTrials': 14,
                                            'setCritWindow': 3,
                                            'setCritDivisor': 2.0,
                                            'setCritType': 'First',
                                            'habThresh': 5.0,
                                            'maxHabSet': -1,
                                            'metCritWindow': 3,
                                            'metCritDivisor': 1.0,
                                            'metCritStatic': 'Moving',
                                            'calcHabOver': []},
                                      'E': {'trialList': ['A', 'Y', 'X'],
                                            'habituation': 0,
                                            'habByDuration': 0,
                                            'maxHabTrials': 14,
                                            'setCritWindow': 3,
                                            'setCritDivisor': 2.0,
                                            'setCritType': 'First',
                                            'habThresh': 5.0,
                                            'maxHabSet': -1,
                                            'metCritWindow': 3,
                                            'metCritDivisor': 1.0,
                                            'metCritStatic': 'Moving',
                                            'calcHabOver': []}}
        self.commandInst.blockStartIndexes['C'] = []
        self.commandInst.blockStartIndexes['E'] = []

        self.commandInst.stimNames = {'A': ['Movie1', 'Movie2', 'Movie3', 'Movie4'],
                                      'B': ['Movie5', 'Movie6', 'Movie7', 'Movie8'],
                                      'X': ['Movie1', 'Movie2', 'Movie3', 'Movie4'],
                                      'Y': ['Movie9', 'Movie10']}
        self.commandInst.stimDict = {'A': ['Movie1', 'Movie2'],
                                     'B': ['Movie5', 'Movie6'],
                                     'X': ['Movie1', 'Movie2'],
                                     'Y': ['Movie9', 'Movie10']}

        self.commandInst.trialOrder = ['A', 'A', 'C', 'C', 'C', 'D']
        self.commandInst.counters = {'A': 3, 'B': 2, 'X': 2, 'Y': 2}
        self.commandInst.run(testMode=testOne)

        # Reset data objects too
        self.commandInst.verbDatList = copy.deepcopy(self.testDatList)
        self.commandInst.dataMatrix = copy.deepcopy(self.testMatrix)

        # Append two rounds of trial C.
        temp1 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'C.X', 'stimName': 'Movie1.mov',
                 'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        temp2 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'C.E.A',
                 'stimName': 'Movie3.mov', 'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        temp3 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 5, 'GNG': 1, 'trialType': 'C.E.Y', 'stimName': 'Movie9.mov',
                 'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        temp4 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 6, 'GNG': 1, 'trialType': 'C.E.X',
                 'stimName': 'Movie2.mov', 'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        temp5 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 7, 'GNG': 1, 'trialType': 'C.B', 'stimName': 'Movie5.mov',
                 'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}

        self.commandInst.dataMatrix.append(temp1)
        self.commandInst.dataMatrix.append(temp2)
        self.commandInst.dataMatrix.append(temp3)
        self.commandInst.dataMatrix.append(temp4)
        self.commandInst.dataMatrix.append(temp5)

        temp6 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 8, 'GNG': 1, 'trialType': 'C.X', 'stimName': 'Movie1.mov',
                 'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        temp7 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 9, 'GNG': 1, 'trialType': 'C.E.A',
                 'stimName': 'Movie4.mov', 'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        temp8 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 10, 'GNG': 1, 'trialType': 'C.E.Y', 'stimName': 'Movie10.mov',
                 'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        temp9 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 11, 'GNG': 1, 'trialType': 'C.E.X',
                 'stimName': 'Movie2.mov', 'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        temp10 = {'sNum': 99, 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                 'condLabel': 'dataTest', 'trial': 12, 'GNG': 1, 'trialType': 'C.B', 'stimName': 'Movie6.mov',
                 'habCrit': 0, 'sumOnA': 5.0, 'numOnA': 2, 'sumOffA': 3.5,
                 'numOffA': 2, 'sumOnB': 3.0, 'numOnB': 2, 'sumOffB': 3.5, 'numOffB': 2}
        self.commandInst.dataMatrix.append(temp6)
        self.commandInst.dataMatrix.append(temp7)
        self.commandInst.dataMatrix.append(temp8)
        self.commandInst.dataMatrix.append(temp9)
        self.commandInst.dataMatrix.append(temp10)

        # This would put us at the start of trial number 13
        # First, let's try one step back withou block redo
        [x, y] = self.commandInst.redoSetup(13,[],'C')
        assert y == 12
        assert x == 'Movie6'

        # Now let's do that again, with blockRedo. This should rewind to trial 8
        [x, y] = self.commandInst.redoSetup(12,[],'C',blockRedo=True)
        assert y == 8
        assert x == 'Movie1'

        # Now let's reappend and pretend we aborted on trial 12
        self.commandInst.dataMatrix.append(temp6)
        self.commandInst.dataMatrix.append(temp7)
        self.commandInst.dataMatrix.append(temp8)
        self.commandInst.dataMatrix.append(temp9)
        [x, y] = self.commandInst.redoSetup(12,[],'C',blockRedo=True,fromAbort=True)
        assert y == 8
        assert x == 'Movie1'



class TestPrefLook(object):
    """
    Tests preferential-looking-specific functions that can be tested, basically just the data functions + end exp.
    """
    def setup_class(self):
        self.dataInstPL = PHL.PyHabPL(base_settings, testMode=True)
        # Set values for things that are usually set in the experimenter dialog
        self.dataInstPL.sNum = 99
        self.dataInstPL.sID = 'TEST'
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
        self.testMatrixPL = [{'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                            'condLabel': 'dataTest', 'trial': 1, 'GNG': 1, 'trialType': 'A', 'stimName': 'movie1.mov',
                            'habCrit': 0, 'habTrialNo':'', 'sumOnL': 3.0, 'numOnL': 2, 'sumOnR': 3.0, 'numOnR': 2, 'sumOff': 3.5,
                            'numOff': 2, 'trialDuration': 9.5, 'firstLookL':1.5, 'firstLookR':1.5},
                                            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                                            'condLabel': 'dataTest', 'trial': 2, 'GNG': 1, 'trialType': 'B',
                                            'stimName': 'movie2.mov',
                                            'habCrit': 0, 'habTrialNo':'', 'sumOnL': 3.0, 'numOnL': 2, 'sumOnR': 3.0, 'numOnR': 2,
                                            'sumOff': 3.5, 'numOff': 2, 'trialDuration': 9.5}]
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
        del self.testMatrixPL

    def test_PLabort(self):
        self.dataInstPL.abortTrial(self.trialVOn1, self.trialVOff1, 1, 'A', self.trialVOn2, 'movie1.mov')

        assert self.dataInstPL.badTrials[0]['trial'] == self.trialVOn1[0]['trial']
        assert self.dataInstPL.badTrials[0]['trialType'] == self.trialVOn1[0]['trialType']
        assert self.dataInstPL.badTrials[0]['GNG'] == 0
        assert self.dataInstPL.badTrials[0]['habCrit'] == 0.0
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
        assert self.dataInstPL.dataMatrix[0] == self.testMatrixPL[0]
        assert len(self.dataInstPL.badTrials) == 0

    def test_PLBlockSave(self):
        self.dataInstPL.dataMatrix = copy.deepcopy(self.testMatrixPL)
        self.dataInstPL.verbDatList = copy.deepcopy(self.testDatList)
        self.dataInstPL.badTrials = []
        self.dataInstPL.blockList = {'C': {'trialList': ['A','B'],
                                        'habituation': 0,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'First',
                                        'habThresh': 5.0,
                                        'maxHabSet': -1,
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': []}}
        self.dataInstPL.actualTrialOrder = ['A', 'B', 'C.A', 'C.B', 'C.A', 'C.B']
        self.dataInstPL.blockDataList = ['C']
        self.dataInstPL.blockDataTags = {'C': [[3, 4], [5, 6]]}
        self.dataInstPL.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'C.A', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnL': 5.0, 'numOnL': 2, 'sumOnR': 5.0, 'numOnR': 2, 'sumOff': 3.5,
             'numOff': 2, 'trialDuration': 11.5})
        self.dataInstPL.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'C.B', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnL': 5.0, 'numOnL': 2, 'sumOnR': 5.0, 'numOnR': 2, 'sumOff': 3.5,
             'numOff': 2, 'trialDuration': 11.5})
        self.dataInstPL.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 5, 'GNG': 1, 'trialType': 'C.A', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnL': 5.0, 'numOnL': 2, 'sumOnR': 3.0, 'numOnR': 1, 'sumOff': 3.5,
             'numOff': 2, 'trialDuration': 9.5})
        self.dataInstPL.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 6, 'GNG': 1, 'trialType': 'C.B', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnL': 5.0, 'numOnL': 2, 'sumOnR': 5.0, 'numOnR': 2, 'sumOff': 3.5,
             'numOff': 2, 'trialDuration': 11.5})

        blockMatrix = self.dataInstPL.saveBlockFile()
        assert len(blockMatrix) == 4
        assert blockMatrix[2]['trialType'] == 'C'
        assert blockMatrix[2]['sumOnL'] == 10.0
        assert blockMatrix[2]['numOnL'] == 4
        assert blockMatrix[2]['sumOnR'] == 10.0
        assert blockMatrix[2]['numOnR'] == 4
        assert blockMatrix[2]['trialDuration'] == 23.0

        assert blockMatrix[3]['sumOnL'] == 10.0
        assert blockMatrix[3]['numOnL'] == 4
        assert blockMatrix[3]['sumOnR'] == 8.0
        assert blockMatrix[3]['numOnR'] == 3
        assert blockMatrix[3]['trialDuration'] == 21.0

        assert blockMatrix[2]['stimName'] == 'movie1.mov+movie1.mov'
        assert blockMatrix[3]['trial'] == 4

    def test_PLhabSave(self):
        self.dataInstPL.dataMatrix = copy.deepcopy(self.testMatrixPL)
        self.dataInstPL.dataMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'D.B', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 1, 'sumOnL': 3.5, 'numOnL': 2,
                          'sumOnR': 3.0, 'numOnR': 2, 'sumOff': 3.5,'numOff': 2})
        self.dataInstPL.dataMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'D.C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 1, 'sumOnL': 3.5, 'numOnL': 2,
                          'sumOnR': 3.0, 'numOnR': 2, 'sumOff': 3.5,'numOff': 2})
        self.dataInstPL.dataMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 5, 'GNG': 1, 'trialType': 'D.B', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 2, 'sumOnL': 3.5, 'numOnL': 2,
                          'sumOnR': 3.0, 'numOnR': 2, 'sumOff': 3.5,'numOff': 2})
        self.dataInstPL.dataMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 6, 'GNG': 1, 'trialType': 'D.C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 2, 'sumOnL': 3.5, 'numOnL': 2,
                          'sumOnR': 3.0, 'numOnR': 2, 'sumOff': 3.5,'numOff': 2})
        self.dataInstPL.dataMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 7, 'GNG': 1, 'trialType': 'D.B', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 3, 'sumOnL': 3.5, 'numOnL': 2,
                          'sumOnR': 3.0, 'numOnR': 2, 'sumOff': 3.5,'numOff': 2})
        self.dataInstPL.dataMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 8, 'GNG': 1, 'trialType': 'D.C', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 3, 'sumOnL': 3.5, 'numOnL': 2,
                          'sumOnR': 3.0, 'numOnR': 2, 'sumOff': 3.5,'numOff': 2})

        self.dataInstPL.badTrials = []
        self.dataInstPL.blockList={'D': {'trialList': ['B', 'C'],
               'habituation': 1,
               'habByDuration': 0,
               'maxHabTrials': 14,
               'setCritWindow': 3,
               'setCritDivisor': 2.0,
               'setCritType': 'First',
               'habThresh': 5.0,
               'maxHabSet':-1,
               'metCritWindow': 3,
               'metCritDivisor': 1.0,
               'metCritStatic': 'Moving',
               'calcHabOver': ['B']}}

        habSaveData = self.dataInstPL.saveHabFile()
        assert len(habSaveData) == 5
        assert habSaveData[3]['trialType'] == 'D'
        assert habSaveData[3]['sumOnL'] == 3.5
        assert habSaveData[3]['sumOnR'] == 3.0

        self.dataInstPL.blockList['D']['calcHabOver'] = ['B','C']
        habSaveData = self.dataInstPL.saveHabFile()
        assert len(habSaveData) == 5
        assert habSaveData[3]['trialType'] == 'D'
        assert habSaveData[3]['sumOnL'] == 7.0
        assert habSaveData[3]['sumOnR'] == 6.0
        assert habSaveData[3]['stimName'] == 'movie1.mov+movie1.mov'


class TestHPP(object):
    """Tests for HPP-specific functions that can be tested, basically data and endexp."""
    def setup_class(self):
        self.dataInstHPP = PHPP.PyHabHPP(base_settings, testMode=True)
        # Set values for things that are usually set in the experimenter dialog
        self.dataInstHPP.sNum = 99
        self.dataInstHPP.sID = 'TEST'
        self.dataInstHPP.ageMo = 5
        self.dataInstHPP.ageDay = 15
        self.dataInstHPP.sex = 'm'
        self.dataInstHPP.cond = 'dataTest'
        self.dataInstHPP.condLabel = 'dataTest'
        # Create base mock data structures to tinker with
        self.trialVOnL1 = [{'trial': 1, 'trialType': 'A', 'startTime': 0.0, 'endTime': 1.5, 'duration': 1.5},
                          {'trial': 1, 'trialType': 'A', 'startTime': 6.5, 'endTime': 8.0, 'duration': 1.5}]  # VerboseOnL
        self.trialVOff1 = [{'trial': 1, 'trialType': 'A', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                           {'trial': 1, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5, 'duration': 2.0}]  # VerboseOff
        self.trialVOnR1 = [{'trial': 1, 'trialType': 'A', 'startTime': 3.0, 'endTime': 4.5, 'duration': 1.5},
                          {'trial': 1, 'trialType': 'A', 'startTime': 8.5, 'endTime': 9.0,'duration': 0.5}]  # VerboseOnR
        self.trialVOnC1 = [{'trial': 1, 'trialType': 'A', 'startTime': 8.0, 'endTime': 8.5, 'duration': 0.5},
                          {'trial': 1, 'trialType': 'A', 'startTime': 9.0, 'endTime': 10.5, 'duration': 1.5}]  # VerboseOnC
        self.testMatrixHPP = [{'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                            'condLabel': 'dataTest', 'trial': 1, 'GNG': 1, 'trialType': 'A', 'stimName': 'movie1.mov',
                            'habCrit': 0.0, 'habTrialNo':'', 'sumOnL': 3.0, 'numOnL': 2, 'sumOnC': 2.0, 'numOnC': 2,
                            'sumOnR': 2.0, 'numOnR': 2, 'sumOff': 3.5, 'numOff': 2, 'trialDuration': 10.5, 'firstLookC':0.5, 'firstLookL':1.5,'firstLookR':1.5},
                                {'sNum': 99, 'sID': 'TEST',
                                'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest', 'condLabel': 'dataTest',
                                'trial': 2, 'GNG': 1, 'trialType': 'B', 'stimName': 'movie2.mov',
                                'habCrit': 0, 'habTrialNo':'', 'sumOnL': 3.0, 'numOnL': 2, 'sumOnC': 2.0, 'numOnC': 2,
                                'sumOnR': 3.0, 'numOnR': 2, 'sumOff': 3.5, 'numOff': 2, 'trialDuration': 10.5}]
        self.testDatList = {'verboseOnL': [{'trial': 1, 'trialType': 'A', 'startTime': 0.0, 'endTime': 1.5, 'duration': 1.5},
                           {'trial': 1, 'trialType': 'A', 'startTime': 6.5, 'endTime': 8.0, 'duration': 1.5},
                           {'trial': 2, 'trialType': 'A', 'startTime': 0.0, 'endTime': 1.5, 'duration': 1.5},
                           {'trial': 2, 'trialType': 'A', 'startTime': 6.5, 'endTime': 8.0,'duration': 1.5}],
             'verboseOff': [{'trial': 1, 'trialType': 'A', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                            {'trial': 1, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5, 'duration': 2.0},
                            {'trial': 2, 'trialType': 'A', 'startTime': 1.5, 'endTime': 3.0, 'duration': 1.5},
                            {'trial': 2, 'trialType': 'A', 'startTime': 4.5, 'endTime': 6.5, 'duration': 2.0}],
             'verboseOnR': [{'trial': 1, 'trialType': 'A', 'startTime': 3.0, 'endTime': 4.5, 'duration': 1.5},
                            {'trial': 1, 'trialType': 'A', 'startTime': 8.5, 'endTime': 9.0,'duration': 0.5},
                            {'trial': 2, 'trialType': 'A', 'startTime': 3.0, 'endTime': 4.5, 'duration': 1.5},
                            {'trial': 2, 'trialType': 'A', 'startTime': 8.5, 'endTime': 9.0, 'duration': 0.5}],
             'verboseOnC': [{'trial': 1, 'trialType': 'A', 'startTime': 8.0, 'endTime': 8.5, 'duration': 0.5},
                            {'trial': 1, 'trialType': 'A', 'startTime': 9.0, 'endTime': 10.5, 'duration': 1.5},
                            {'trial': 1, 'trialType': 'A', 'startTime': 8.0, 'endTime': 8.5, 'duration': 0.5},
                            {'trial': 1, 'trialType': 'A', 'startTime': 9.0, 'endTime': 10.5, 'duration': 1.5}]}


    def teardown_class(self):
        del self.dataInstHPP
        del self.trialVOnL1
        del self.trialVOff1
        del self.trialVOnR1
        del self.trialVOnC1
        del self.testMatrixHPP

    def test_HPPabort(self):
        self.dataInstHPP.abortTrial(self.trialVOnC1, self.trialVOff1, 1, 'A', self.trialVOnL1, self.trialVOnR1, 'movie1.mov')

        assert self.dataInstHPP.badTrials[0]['trial'] == self.trialVOnC1[0]['trial']
        assert self.dataInstHPP.badTrials[0]['trialType'] == self.trialVOnC1[0]['trialType']
        assert self.dataInstHPP.badTrials[0]['GNG'] == 0
        assert self.dataInstHPP.badTrials[0]['habCrit'] == 0
        assert self.dataInstHPP.badTrials[0]['sumOnC'] == self.trialVOnC1[0]['duration'] + self.trialVOnC1[1]['duration']
        assert self.dataInstHPP.badTrials[0]['sumOff'] == self.trialVOff1[0]['duration'] + self.trialVOff1[1]['duration']
        assert self.dataInstHPP.badTrials[0]['numOnC'] == len(self.trialVOnC1)
        assert self.dataInstHPP.badTrials[0]['numOff'] == len(self.trialVOff1)
        assert self.dataInstHPP.badTrials[0]['sumOnL'] == self.trialVOnL1[0]['duration'] + self.trialVOnL1[1]['duration']
        assert self.dataInstHPP.badTrials[0]['numOnL'] == len(self.trialVOnL1)
        assert self.dataInstHPP.badTrials[0]['sumOnR'] == self.trialVOnR1[0]['duration'] + self.trialVOnR1[1]['duration']
        assert self.dataInstHPP.badTrials[0]['numOnR'] == len(self.trialVOnR1)

    def test_HPPdatarec(self):
        self.dataInstHPP.dataMatrix = []
        self.dataInstHPP.badTrials = []

        self.dataInstHPP.dataRec(self.trialVOnC1, self.trialVOff1, 1, 'A', self.trialVOnL1, self.trialVOnR1, 'movie1.mov')

        assert len(self.dataInstHPP.dataMatrix) == 1
        assert self.dataInstHPP.dataMatrix[0] == self.testMatrixHPP[0]
        assert len(self.dataInstHPP.badTrials) == 0

    def test_HPPBlockSave(self):
        self.dataInstHPP.dataMatrix = copy.deepcopy(self.testMatrixHPP)
        self.dataInstHPP.verbDatList = copy.deepcopy(self.testDatList)
        self.dataInstHPP.badTrials = []
        self.dataInstHPP.blockList = {'C': {'trialList': ['A','B'],
                                        'habituation': 0,
                                        'habByDuration': 0,
                                        'maxHabTrials': 14,
                                        'setCritWindow': 3,
                                        'setCritDivisor': 2.0,
                                        'setCritType': 'First',
                                        'habThresh': 5.0,
                                        'maxHabSet': -1,
                                        'metCritWindow': 3,
                                        'metCritDivisor': 1.0,
                                        'metCritStatic': 'Moving',
                                        'calcHabOver': []}}
        self.dataInstHPP.actualTrialOrder = ['A', 'B', 'C.A', 'C.B', 'C.A', 'C.B']
        self.dataInstHPP.blockDataList = ['C']
        self.dataInstHPP.blockDataTags = {'C': [[3, 4], [5, 6]]}
        self.dataInstHPP.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'C.A', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnL': 5.0, 'numOnL': 2, 'sumOnC': 2.0, 'numOnC': 2, 'sumOnR': 5.0, 'numOnR': 2,
             'sumOff': 3.5, 'numOff': 2, 'trialDuration': 13.5})
        self.dataInstHPP.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'C.B', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnL': 5.0, 'numOnL': 2, 'sumOnC': 5.0, 'numOnC': 2, 'sumOnR': 5.0, 'numOnR': 2,
             'sumOff': 3.5, 'numOff': 2, 'trialDuration': 16.5})
        self.dataInstHPP.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 5, 'GNG': 1, 'trialType': 'C.A', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnL': 5.0, 'numOnL': 2, 'sumOnC': 5.0, 'numOnC': 2, 'sumOnR': 3.0, 'numOnR': 1,
             'sumOff': 3.5, 'numOff': 2, 'trialDuration': 13.5})
        self.dataInstHPP.dataMatrix.append(
            {'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
             'condLabel': 'dataTest', 'trial': 6, 'GNG': 1, 'trialType': 'C.B', 'stimName': 'movie1.mov',
             'habCrit': 0, 'sumOnL': 5.0, 'numOnL': 2, 'sumOnC': 5.0, 'numOnC': 2, 'sumOnR': 5.0, 'numOnR': 2,
             'sumOff': 3.5, 'numOff': 2, 'trialDuration': 16.5})

        blockMatrix = self.dataInstHPP.saveBlockFile()
        assert len(blockMatrix) == 4
        assert blockMatrix[2]['trialType'] == 'C'
        assert blockMatrix[2]['sumOnL'] == 10.0
        assert blockMatrix[2]['numOnL'] == 4
        assert blockMatrix[2]['sumOnC'] == 7.0
        assert blockMatrix[2]['numOnC'] == 4
        assert blockMatrix[2]['sumOnR'] == 10.0
        assert blockMatrix[2]['numOnR'] == 4
        assert blockMatrix[2]['trialDuration'] == 30.0

        assert blockMatrix[3]['sumOnL'] == 10.0
        assert blockMatrix[3]['numOnL'] == 4
        assert blockMatrix[2]['sumOnC'] == 7.0
        assert blockMatrix[2]['numOnC'] == 4
        assert blockMatrix[3]['sumOnR'] == 8.0
        assert blockMatrix[3]['numOnR'] == 3
        assert blockMatrix[3]['trialDuration'] == 30.0

        assert blockMatrix[2]['stimName'] == 'movie1.mov+movie1.mov'
        assert blockMatrix[3]['trial'] == 4

    def test_HPPhabSave(self):

        self.dataInstHPP.dataMatrix = copy.deepcopy(self.testMatrixHPP)  # Should get two trials!

        self.dataInstHPP.dataMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 3, 'GNG': 1, 'trialType': 'D.A', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 1, 'sumOnL': 3.5, 'numOnL': 2, 'sumOnC': 3.5, 'numOnC': 2,
                          'sumOnR': 3.0, 'numOnR': 2, 'sumOff': 3.5,'numOff': 2})
        self.dataInstHPP.dataMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 4, 'GNG': 1, 'trialType': 'D.B', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 1, 'sumOnL': 3.5, 'numOnL': 2, 'sumOnC': 3.5, 'numOnC': 2,
                          'sumOnR': 3.0, 'numOnR': 2, 'sumOff': 3.5,'numOff': 2})
        self.dataInstHPP.dataMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 5, 'GNG': 1, 'trialType': 'D.A', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 2, 'sumOnL': 3.5, 'numOnL': 2, 'sumOnC': 3.5, 'numOnC': 2,
                          'sumOnR': 3.0, 'numOnR': 2, 'sumOff': 3.5,'numOff': 2})
        self.dataInstHPP.dataMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 6, 'GNG': 1, 'trialType': 'D.B', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 2, 'sumOnL': 3.5, 'numOnL': 2, 'sumOnC': 3.5, 'numOnC': 2,
                          'sumOnR': 3.0, 'numOnR': 2, 'sumOff': 3.5,'numOff': 2})
        self.dataInstHPP.dataMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 7, 'GNG': 1, 'trialType': 'D.A', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 3, 'sumOnL': 3.5, 'numOnL': 2, 'sumOnC': 3.5, 'numOnC': 2,
                          'sumOnR': 3.0, 'numOnR': 2, 'sumOff': 3.5,'numOff': 2})
        self.dataInstHPP.dataMatrix.append({'sNum': 99, 'sID': 'TEST', 'months': 5, 'days': 15, 'sex': 'm', 'cond': 'dataTest',
                          'condLabel': 'dataTest', 'trial': 8, 'GNG': 1, 'trialType': 'D.B', 'stimName': 'movie1.mov',
                          'habCrit': 0, 'habTrialNo': 3, 'sumOnL': 3.5, 'numOnL': 2, 'sumOnC': 3.5, 'numOnC': 2,
                          'sumOnR': 3.0, 'numOnR': 2, 'sumOff': 3.5,'numOff': 2})

        self.dataInstHPP.badTrials = []
        self.dataInstHPP.blockList = {'D': {'trialList': ['B', 'C'],
                                           'habituation': 1,
                                           'habByDuration': 0,
                                           'maxHabTrials': 14,
                                           'setCritWindow': 3,
                                           'setCritDivisor': 2.0,
                                           'setCritType': 'First',
                                           'habThresh': 5.0,
                                           'maxHabSet': -1,
                                           'metCritWindow': 3,
                                           'metCritDivisor': 1.0,
                                           'metCritStatic': 'Moving',
                                           'calcHabOver': ['B']}}


        habSaveData = self.dataInstHPP.saveHabFile()
        assert len(habSaveData) == 5
        assert habSaveData[3]['trialType'] == 'D'
        assert habSaveData[3]['sumOnC'] == 3.5
        assert habSaveData[3]['sumOnL'] == 3.5
        assert habSaveData[3]['sumOnR'] == 3.0

        self.dataInstHPP.blockList['D']['calcHabOver'] = ['A', 'B']
        habSaveData = self.dataInstHPP.saveHabFile()
        assert len(habSaveData) == 5
        assert habSaveData[3]['trialType'] == 'D'
        assert habSaveData[3]['sumOnC'] == 7.0
        assert habSaveData[3]['sumOnL'] == 7.0
        assert habSaveData[3]['sumOnR'] == 6.0
        assert habSaveData[3]['stimName'] == 'movie1.mov+movie1.mov'