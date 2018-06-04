from types import NoneType

from psychopy import core, data, gui, monitors, tools
import wx, random, csv, os
from math import *
from datetime import *


def WPA(timewarp, timewarp2):
    """
    Calculates weighted percentage agreement, computed as number of agreement frames over total frames.

    :param timewarp: List of every individual frame's gaze-on/gaze-off code for coder A
    :type timewarp: list
    :param timewarp2: As above for coder B
    :type timewarp2: list
    :return: Weighted Percentage Agreement
    :rtype: float
    """
    a = 0
    d = 0
    for (i, j) in zip(timewarp, timewarp2):
        if i[0] == j[0]:
            if i[1] == j[1]:
                a += 1
            else:
                d += 1
        else:
            d += 1
    wpagreement = float(a) / float(a + d)
    return wpagreement

def pearsonR(verboseMatrix, verboseMatrix2):
    """
    Computes Pearson's R

    :param verboseMatrix: Verbose data, coder A
    :type verboseMatrix: list
    :param verboseMatrix2: Verboase data, coder B
    :type verboseMatrix2: list
    :return: Pearson's R
    :rtype: float
    """
    trialA = []
    trialB = []
    avA = 0
    avB = 0
    # loop to construct trial array, zeroed out.
    for k in range(0, verboseMatrix[-1][7]):
        trialA.append(0)
        trialB.append(0)
    # separate loops for computing total on time per trial for each coder, must be done separately from verbose data files
    # b/c no longer access to summary data
    for i in verboseMatrix:
        if i[5] != 0:  # Good trials only
            if i[6] != 0:  # We only care about total on-time.
                tn = i[7] - 1
                trialA[tn] += i[11]  # add the looking time to the appropriate trial index.
    for i in verboseMatrix2:
        if i[5] != 0:  # Good trials only
            if i[6] != 0:  # We only care about total on-time.
                tn = i[7] - 1
                trialB[tn] += i[11]  # add the looking time to the appropriate trial index.
    for j in range(0, len(trialA)):
        avA += trialA[j]
        avB += trialB[j]
    avA = avA / verboseMatrix[-1][7]  # final trial number.
    avB = avB / verboseMatrix2[-1][7]  # in point of fact should be the same last trial # but eh.
    xy = []
    for i in range(0, len(trialA)):
        trialA[i] -= avA
        trialB[i] -= avB
        xy.append(trialA[i] * trialB[i])
    for i in range(0, len(trialA)):  # square the deviation arrays
        trialA[i] = trialA[i] ** 2
        trialB[i] = trialB[i] ** 2
    r = float(sum(xy) / sqrt(sum(trialA) * sum(trialB)))
    return r

def cohensKappa(timewarp, timewarp2):
    """
    Computes Cohen's Kappa
    :param timewarp: List of every individual frame's gaze-on/gaze-off code for coder A
    :type timewarp: list
    :param timewarp2: As above for coder B
    :type timewarp2: list
    :return: Kappa
    :rtype: float
    """
    wpa = WPA(timewarp, timewarp2)
    coderBon = 0
    coderAon = 0
    for i in range(0, len(timewarp)):#are the 2 timewarps equal? - when can one be bigger?
        if timewarp[i][1] == 1:
            coderAon += 1
        if timewarp2[i][1] == 1:
            coderBon += 1
    pe = (float(coderAon)/len(timewarp))*(float(coderBon)/len(timewarp2))+(float(len(timewarp)-coderAon)/len(timewarp))*(float(len(timewarp2)-coderBon)/len(timewarp2))
    k = float(wpa-pe)/float(1-pe)
    return k

def avgObsAgree(timewarp, timewarp2):
    """
    Computes average observer agreement as agreement in each trial, divided by number of trials.
    :param timewarp: List of every individual frame's gaze-on/gaze-off code for coder A
    :type timewarp: list
    :param timewarp2: As above for coder B
    :type timewarp2: list
    :return: average observer agreement or N/A if no valid data
    :rtype: float
    """

    finalTrial = timewarp[-1][0] #0 is trial number.

    tg = 0
    if finalTrial > 0: #if there are NO good trials, well it's probably crashed already, but JIC
        for i in range(0, finalTrial): #need contingency if last trial is bad trial?
            a=0
            d=0
            for (m, l) in zip(timewarp, timewarp2):
                if m[0]==i+1 and l[0]==i+1:
                    if m[1]==l[1]:
                        a+=1
                    else:
                        d+=1
            tg = tg + float(a)/(a+d)
        aoagreement = float(tg)/finalTrial
        return aoagreement
    else:
        return 'N/A'

def reliability(verboseMatrix, verboseMatrix2):
    """
    A function that computes four different types of reliability statistics (Weighted % agreement,
    Average observer agreement, Cohen's Kappa, and Pearson's R) based on two pre-existing PyHab
    verbose data files selected by the user. This is nearly identical to the reliability function
    in the PyHab live-run script when you have two live looking-time coders, but without requiring
    you to have simultaneous coding.

    :param verboseMatrix: A 2d list read from an existing verbose data file
    :type verboseMatrix: list
    :param verboseMatrix2: A 2d list read from an existing verbose data file
    :type verboseMatrix2: list
    :return: A dict of four stats (weighted % agreement, average observer agreement, Cohen's Kappa, and Pearson's R)
    :rtype: dict
    """


    timewarp=[]#frame by frame arrays
    timewarp2=[]
    #Chages: To run post-hoc, when the overall duration will not be equal, it is necessary to make sure each individual
    #trial starts at the same point in the timewarp arrays
    finalTrial = verboseMatrix[-1][7]
    for j in range(0, finalTrial):  
        for i in verboseMatrix:
            if i[5]!=0 and i[7]==j+1:#check for it not to be a bad gaze
                for k in range(0, int(round(i[11]*60))):
                    timewarp.append([i[7],i[6]])#6 being On or Off and 7 the trial no.
        for i in verboseMatrix2:
            if i[5]!=0 and i[7]==j+1:
                for k in range(0, int(round(i[11]*60))):
                    timewarp2.append([i[7],i[6]])
        if len(timewarp)>len(timewarp2):#making sure the frame by frame arrays are of equal length for that trial.
            diff=len(timewarp)-len(timewarp2)
            for s in range(0, diff):
                timewarp2.append([verboseMatrix2[-1][7], 0])
        elif len(timewarp)<len(timewarp2):
            diff=len(timewarp2)-len(timewarp)
            for s in range(0, diff):
                timewarp.append([verboseMatrix[-1][7], 0])

    stats = {'WeightedPercentageAgreement': WPA(timewarp, timewarp2), 'CohensKappa': cohensKappa(timewarp, timewarp2),
             'AverageObserverAgreement': avgObsAgree(timewarp, timewarp2), 'PearsonsR': pearsonR(verboseMatrix, verboseMatrix2)}
    return stats

ready = False
startDlg = gui.Dlg(title='PyHab reliability calculator')
startDlg.addText('Subject info')
startDlg.addField('Subject Number: ')
startDlg.addField('Subject ID: ')
startDlg.addText('Click OK to select the two verbose files (the file select window may take a while to load)')
startDlg.show()
if startDlg.OK:
    dlg1 = gui.fileOpenDlg()
    print(dlg1)
    if type(dlg1) is not 'NoneType':
        dlg2 = gui.fileOpenDlg()
        if type(dlg2) is not 'NoneType':
            ready = True
if ready:
    thisInfo = startDlg.data
    VF1 = csv.reader(open(dlg1[0], 'rU')) 
    VF2 = csv.reader(open(dlg2[0], 'rU'))
    Verb1=[]
    Verb2=[]
    for row in VF1:
        Verb1.append(row)
    for row in VF2:
        Verb2.append(row)
    #now we need to trim off the headers.
    del(Verb1[0])
    del(Verb2[0])
    #and make all the numerical values into floats
    for i in range(0,len(Verb1)):
        for k in range(5, 8):
            Verb1[i][k]=int(Verb1[i][k]) #convert trial #, GNG, gaze on/off to int
        for j in range(9, 12):
            Verb1[i][j] = float(Verb1[i][j]) #convert ontime, offtime, & duration to float
    for i in range(0,len(Verb2)):
        for k in range(5, 8):
            Verb2[i][k] = int(Verb2[i][k]) 
        for j in range(9, 12):
            Verb2[i][j] = float(Verb2[i][j])
    relstats = reliability(Verb1, Verb2)
    doneDlg = gui.Dlg(title="Calculations complete!",labelButtonOK="Yes", labelButtonCancel="No")
    doneDlg.addText("Weighted percentage agreement: " + str(relstats['WeightedPercentageAgreement']))
    doneDlg.addText("Cohen's Kappa: " + str(relstats['CohensKappa']))
    doneDlg.addText("Average observer agreement: " + str(relstats['AverageObserverAgreement']))
    doneDlg.addText("Pearson's R: " + str(relstats['PearsonsR']))
    doneDlg.addText("Save output?")
    doneDlg.show()
    if doneDlg.OK:
        sDlg = gui.fileSaveDlg(initFilePath=os.getcwd(), initFileName=str(thisInfo[0])+'_'+str(thisInfo[1])+'_Stats.csv')
        if type(sDlg) is not NoneType:
            headers3=['WeightedPercentageAgreement', 'CohensKappa','AverageObserverAgreement','PearsonsR']
            outputWriter4 = csv.DictWriter(open(sDlg,'w'),
                                           fieldnames=headers3, extrasaction='ignore',lineterminator ='\n')
            outputWriter4.writeheader()
            outputWriter4.writerow(relstats)