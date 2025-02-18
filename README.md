
# PyHab
<a href='https://pyhab.readthedocs.io/en/latest/?badge=latest'>
    <img src='https://readthedocs.org/projects/pyhab/badge/?version=latest' alt='Documentation Status' />
</a>
<br />
Looking time and stimulus presentation system for PsychoPy.
<h2>What is PyHab?</h2>
<p>Research with human infants (and some non-human animals) often relies on measuring looking times. Manual looking time coding is still very common. Currently, they are only a handful of programs built for this purpose, especially for live coding of looking times (during the experiment), and those programs are old, opaque, and difficult to integrate with stimulus presentation. Many studies that control stimulus presentation on the basis of infant's looking (starting a trial when they look at the display, ending it when they look away for a given period of time) still require two experimenters, one to control the stimuli and one to code the looking times.</p>
<p>I felt that it was time for an update, so I built a script that runs in PsychoPy (freely available from <a href="http://psychopy.org">psychopy.org</a>) that can both replace older looking-time coding software with something open-source, and also control stimulus presentation directly.</p>
<h2>Important notes</h2>
<ul>
<li>PyHab is not a stand-alone program. It is a script that runs in PsychoPy. You will need to install PsychoPy. The latest stable version can be found at <a href="https://www.psychopy.org/download.html">psychopy.org/download.html</a></li>
<li><b>I strongly recommend using PsychoPy version 2024.2.0 or later</b> (as of January 2025).</li>
<li>PyHab has a graphical interface for building new studies, but you will still need to open the program initially in PsychoPy's coder view. <b>Read the manual before your begin!</b></li>
<li>PyHab is still very much in development! Don't be shy about contacting me for feature requests. It is now much more flexible than it was, but there are still some designs it cannot produce I'm sure, and I would love to hear about them.</li>
<li>If you do use PyHab for a study that you then submit for publication, please cite <b>both PsychoPy and PyHab</b>. PyHab relies very heavily on PsychoPy (but is not directly affiliated with or developed by the makers of PsychoPy), so credit is due as much to them as it is to me.</li>
<li><a href="https://groups.google.com/forum/#!forum/pyhab-announcements">Please join the Pyhab announcements mailing list for news about updates and important technical information</a></li>
<li><b>KNOWN ISSUES:</b></li>
<li>Multi-monitor setups where one of the monitors is a Mac Retina display can sometimes offset the location of the stimulus window or distort the contents of the coder window. There may be a work-around but it depends on what version of MacOS you're using.</li>
<li>There were several issues with the sound system prior to PsychoPy 2023.2.0, but the newest version of PsychoPy seems to have fixed all of them. Hooray!</li>
</ul>
<h2>Installing PyHab and Getting Started</h2>
<p><a href="https://pyhab.readthedocs.io/en/latest/?badge=latest" target="_blank">Click here for the installation and quick-start guides</a></p>
<h2>Citing PyHab and PsychoPy</h2>
<p>If you use PyHab, please cite <em>both</em> of the following:</p>
<ul>
<li><b>Follow the guidelines for citing PsychoPy</b>: http://psychopy.org/about/index.html#citingpsychopy</li>
<li>Kominsky, J. F. (2019) PyHab: Open-Source Real Time Infant Gaze Coding and Stimulus Presentation Software. <em>Infant Behavior & Development, 54</em>, 114-119. doi:10.1016/j.infbeh.2018.11.006</li>
</ul>
