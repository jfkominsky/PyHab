# PyHab
Looking time and stimulus presentation script for PsychoPy.
<h2>What is PyHab?</h2>
<p>Research with human infants (and some non-human animals) often relies on measuring looking times. Infant eye-tracking is still expensive, imprecise, and relatively unreliable, so manual looking time coding is still very common. Currently, they are only a handful of programs built for this purpose, especially for live coding of looking times (during the experiment), and those programs are old, opaque, and difficult to integrate with stimulus presentation. Many studies that control stimulus presentation on the basis of infant's looking (starting a trial when they look at the display, ending it when they look away for a given period of time) still require two experimenters, one to control the stimuli and one to code the looking times.</p>
<p>I felt that it was time for an update, so I built a script that runs in PsychoPy (freely available from <a href="http://psychopy.org">psychopy.org</a>) that can both replace older looking-time coding software with something open-source, and also control stimulus presentation directly.</p>
<h2>Important notes</h2>
<ul>
<li>PyHab is not a stand-alone program. It is a script that runs in PsychoPy.</li>
<li>To make your own experiment in PsychoPy requires changing a few lines of options in the script. They are clearly marked and the manual explains everything they do, but don't expect a slick GUI for building experiments (yet, anyways)</li>
<li>PyHab is still very much in development. Right now it can be used for habituation/dishabituation designs and some violation of expectation designs, but it is currently limited in a lot of ways. If there are things you need it to do that it currently can't do, let me know! Right now it is very specifically geared towards my own projects, but I would like to make it into a tool that is flexible enough to be used by anyone conducting this kind of study.</li>
<li>If you do use it for a study that you then submit for publication, please cite <b>both PsychoPy and PyHab</b>. PyHab relies very heavily on PsychoPy (but is not directly affiliated with or developed by the makers of PsychoPy), so credit is due as much to them as it is to me.</li>
</ul>
<h2>"Installing" PyHab</h2>
Working on it.
<h2>Citing PyHab and PsychoPy</h2>
<p>Note that I do not have a formal article for PyHab yet, but I may at some point in the future. For the time being, please cite the following:</p>
<ul>
<li>Follow the guidelines for citing PsychoPy, here: http://psychopy.org/about/index.html#citingpsychopy</li>
<li>Kominsky, J. F. (2017) PyHab: Looking time and stimulus presentation script for PsychoPy. [Computer software]. Retrieved from https://github.com/jfkominsky/PyHab on {DATE}</li>
</ul>
