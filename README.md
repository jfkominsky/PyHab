
# PyHab
<a href='https://pyhab.readthedocs.io/en/latest/?badge=latest'>
    <img src='https://readthedocs.org/projects/pyhab/badge/?version=latest' alt='Documentation Status' />
</a>
<a href='https://travis-ci.org/jfkominsky/PyHab'>
    <img src='https://travis-ci.org/jfkominsky/PyHab.svg?branch=master'>
</a><br />
Looking time and stimulus presentation system for PsychoPy.
<h2>What is PyHab?</h2>
<p>Research with human infants (and some non-human animals) often relies on measuring looking times. Infant eye-tracking is still expensive, imprecise, and relatively unreliable, so manual looking time coding is still very common. Currently, they are only a handful of programs built for this purpose, especially for live coding of looking times (during the experiment), and those programs are old, opaque, and difficult to integrate with stimulus presentation. Many studies that control stimulus presentation on the basis of infant's looking (starting a trial when they look at the display, ending it when they look away for a given period of time) still require two experimenters, one to control the stimuli and one to code the looking times.</p>
<p>I felt that it was time for an update, so I built a script that runs in PsychoPy (freely available from <a href="http://psychopy.org">psychopy.org</a>) that can both replace older looking-time coding software with something open-source, and also control stimulus presentation directly.</p>
<h2>Important notes</h2>
<ul>
<li>PyHab is not a stand-alone program. It is a script that runs in PsychoPy. You will need to install PsychoPy. The latest stable version, as of this writing, is 3.0.6</li>
<li>PyHab has a rudimentary graphical interface for building new studies, but you will still need to open the program initially in PsychoPy's coder view. <b>Read the manual before your begin!</b></li>
<li>PyHab is still very much in development! Don't be shy about contacting me for feature requests. It is now much more flexible than it was, but there are still some designs it cannot produce I'm sure, and I would love to hear about them.</li>
<li>If you do use PyHab for a study that you then submit for publication, please cite <b>both PsychoPy and PyHab</b>. PyHab relies very heavily on PsychoPy (but is not directly affiliated with or developed by the makers of PsychoPy), so credit is due as much to them as it is to me.</li>
<li><a href="https://groups.google.com/d/forum/pyhab-announcements/join">Please join the Pyhab announcements mailing list for news about updates and important technical information</a></li>
<li><b>KNOWN ISSUES:</b> There may be an issue with multi-monitor displays where one of them is a Mac Retina display, starting with MacOS 10.13.5 (High Sierra June 2018). I am investigating the problem, but non-Retina displays or earlier versions of MacOS should be unaffected. Non-Macs are obviously unaffected.</li>
</ul>
<h2>"Installing" PyHab</h2>
<p>Click the big green button, hit "download as zip" (or go to releases and select "source code.zip"), unzip the file into a folder, and put the folder wherever you want. Make sure you do not move anything around inside the folder.</p>
<p>Then, just open PsychoPy, go to coder view (found in the 'view' dropwdown menu or with the shortcuts control-L or command-L), open "NewPyHabProject.py" from there, and hit the big green "Run" button.</p>
<p>You will need VLC media player installed on your computer in order to use PsychoPy to present movie stimuli. VLC is free, and <a href="https://www.videolan.org/vlc/index.html">you can download it here</a>.</p>
<h2>Citing PyHab and PsychoPy</h2>
<p>If you use PyHab, please cite both of the following:</p>
<ul>
<li><b>Follow the guidelines for citing PsychoPy</b>: http://psychopy.org/about/index.html#citingpsychopy</li>
<li>Kominsky, J. F. (2019) PyHab: Open-Source Real Time Infant Gaze Coding and Stimulus Presentation Software. <em>Infant Behavior & Development, 54</em>, 114-119. doi:10.1016/j.infbeh.2018.11.006</li>
</ul>
