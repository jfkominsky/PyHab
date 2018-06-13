from psychopy import gui,core
from PyHab import PyHabClass as PH
from PyHab import PyHabClassPL as PHL
from PyHab import PyHabBuilder as PB
import csv, os

setName = 'DUMMY FILENAME'

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
    tempMovs = eval(setDict['movieNames'])
    stPres = True
    if len(tempMovs) > 0:
        for i in tempOrd:
            if len(tempMovs[i]) == 0:
                stPres = False
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
            if setDict['prefLook'] in['0',0,'False',False]:
                experiment = PH.pyHab(setDict)
            else:
                experiment = PHL.pyHabPL(setDict)
            experiment.run()
        else:
            builder = PB.pyHabBuilder(loadedSaved = True, settingsDict=setDict)
            builder.run()
        #After you're done: Relaunch launcher!
        run()
    else:
        core.quit()

run()





