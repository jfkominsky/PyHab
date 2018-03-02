from psychopy import gui,core
import PyHabClass as PH
import PyHabClassPL as PHL
import PyHabBuilder as PB
import csv, os

setName = "PyHabDemoSettings.csv"

def run():
    setFile=csv.reader(open(setName,'rU'))
    setArr=[]
    for row in setFile:
        setArr.append(row)
    setDict = dict(setArr) 
    launcherDlg = gui.Dlg(title="PyHab Launcher",labelButtonCancel=u'Exit')
    launcherDlg.addText('Current setings file: ' + setName)
    launcherDlg.addField('Run study or open builder?', choices=['Run','Builder'])
    if len(setDict['movieNames'])>0:
        ch = ['On','Off']
    else:
        ch = ['Off','On']
    launcherDlg.addField('Stimulus presentation mode (Run only): ', choices=ch)
    launcherDlg.show()
    if launcherDlg.OK:
        launcher = launcherDlg.data
        if launcher[0] == 'Run':
            if launcher[1] == 'On':
                setDict['stimPres'] = '1'
            else:
                setDict['stimPres'] = '0'
            if setDict['prefLook'] in['0',0,'False',False]:
                experiment = PH.pyHab(setDict)
            else:
                experiment=PHL.pyHabPL(setDict)
            experiment.run()
        else:
            builder = PB.pyHabBuilder(loadedSaved = True, settingsDict=setDict)
        #After you're done: Relaunch launcher!
        run()
    else:
        core.quit()

run()





