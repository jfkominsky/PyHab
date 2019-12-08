from psychopy import gui,core
from PyHab import PyHabClass as PH
from PyHab import PyHabClassPL as PHL
from PyHab import PyHabClassHPP as PHPP
from PyHab import PyHabBuilder as PB
import csv, os

setName = "PyHabDemoSettings.csv"
#Created in PsychoPy version 3.1.2

def run():
    setFile=csv.reader(open(setName,'rU'))
    setArr=[]
    for row in setFile:
        setArr.append(row)
    setDict = dict(setArr) 
    launcherDlg = gui.Dlg(title="PyHab Launcher",labelButtonCancel=u'Exit')
    launcherDlg.addText('Current settings file: ' + setName)
    launcherDlg.addField('Run study or open builder?', choices=['Run','Builder'])
    tempOrd = eval(setDict['trialOrder'])
    stPres = checkIfStim(setDict, tempOrd)
    if stPres:
        ch = ['On','Off']
        launcherDlg.addField('Stimulus presentation mode (Run only): ', choices=ch)
    launcherDlg.show()
    if launcherDlg.OK:
        launcher = launcherDlg.data
        if launcher[0] == 'Run':
            if stPres:
                if launcher[1] == 'On':
                    setDict['stimPres'] = '1'
                else:
                    setDict['stimPres'] = '0'
            if setDict['prefLook'] in ['0',0,'False',False]:
                experiment = PH.PyHab(setDict)
            elif setDict['prefLook'] in [1,'1',True,'True']:
                experiment = PHL.PyHabPL(setDict)
            elif setDict['prefLook'] in [2,'2']:
                experiment = PHPP.PyHabHPP(setDict)
            experiment.run()
        else:
            builder = PB.PyHabBuilder(loadedSaved=True, settingsDict=setDict)
            builder.run()
        #After you're done: Relaunch launcher!
        run()
    else:
        core.quit()

def checkIfStim(setDict, tempOrd):
    """
    Checks recursively if there are stimuli associated with everything in the study flow. If anything in the flow
    does not have stimuli associated with it, return false.
    :param setDict: The settings dictionary, for reading off the relevant lists
    :type setDict: dict
    :param tempOrd: The current trial order being evaluated (block or overall)
    :type tempOrd: list
    :return: False if anything in the study flow has no stimuli associated with it, True otherwise.
    :rtype: bool
    """
    tempMovs = eval(setDict['stimNames'])
    tempBlocks = eval(setDict['blockList'])
    tempHabList = eval(setDict['habTrialList'])
    stPres = True
    if len(tempMovs) > 0:
        for i in tempOrd:
            if i in tempMovs:
                if len(tempMovs[i]) == 0:
                    stPres = False
            elif i == 'Hab' and len(tempHabList) > 0:
                if not checkIfStim(setDict, tempHabList):
                    stPres = False
            elif i in tempBlocks.keys():
                if not checkIfStim(setDict, tempBlocks[i]):
                    stPres = False
    return stPres


run()





