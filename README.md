# PyHab
Looking time and stimulus presentation script for PsychoPy.
<h2>What is PyHab?</h2>
<p>Research with human infants (and some non-human animals) often relies on measuring looking times. Infant eye-tracking is still expensive, imprecise, and relatively unreliable, so manual looking time coding is still very common. Currently, they are only a handful of programs built for this purpose, especially for live coding of looking times (during the experiment), and those programs are old, opaque, and difficult to integrate with stimulus presentation. Many studies that control stimulus presentation on the basis of infant's looking (starting a trial when they look at the display, ending it when they look away for a given period of time) still require two experimenters, one to control the stimuli and one to code the looking times.</p>
<p>I felt that it was time for an update, so I built a script that runs in PsychoPy (freely available from <a href="http://psychopy.org">psychopy.org</a>) that can both replace older looking-time coding software with something open-source, and also control stimulus presentation directly.</p>
<h2>Important notes</h2>
<ul>
<li>PyHab is not a stand-alone program. It is a script that runs in PsychoPy. You open the .py files in PsychoPy's coder view and run them from there.</li>
<li>To make your own experiment in PyHab requires changing a few lines of options in the script. They are clearly marked and the manual explains everything they do, but don't expect a slick GUI for building experiments (yet, anyways)</li>
<li>PyHab is still very much in development! Right now it can be used for habituation/dishabituation designs and some violation of expectation designs, but it is currently limited in a lot of ways. Don't be shy about contacting me for feature requests! Right now it is very specifically geared towards my own projects, but I would like to make it into a tool that is flexible enough to be used by anyone conducting this kind of research, because the field has needed a tool like this for a while.</li>
<li>If you do use PyHab for a study that you then submit for publication, please cite <b>both PsychoPy and PyHab</b>. PyHab relies very heavily on PsychoPy (but is not directly affiliated with or developed by the makers of PsychoPy), so credit is due as much to them as it is to me.</li>
</ul>
<h2>"Installing" PyHab</h2>
<p>Simply download all of the files above (including DemoMaterials) into a single folder. Open the scripts in PsychoPy's coder view, and if you've downloaded everything you should be able to simply hit "run" and get a fully functional demo of either version.</p>
<p>The upchime1.wav file is the only one that <b>MUST</b> always be in the same folder as the MovieStim script in order for the script to work. Future versions will hopefully change that.</p>
<p>For some movie files, you may need to have VLC media player installed on your computer, because PsychoPy uses some of its code to play movie files. VLC is free.</p>
<p>As of March 23, 2017, there is an issue with movies that have an audio component that is due to a but in PsychoPy itself that I cannot fix from the script. I have submitted a fix to the PsychoPy developers, and hopefully future versions of PsychoPy will incorporate it, but until then movies with audio may not play consistently.</p>
<h2>Citing PyHab and PsychoPy</h2>
<p>Note that I do not have a formal article for PyHab yet, but I may at some point in the future. For the time being, please cite the following:</p>
<ul>
<li>Follow the guidelines for citing PsychoPy, here: http://psychopy.org/about/index.html#citingpsychopy</li>
<li>Kominsky, J. F. (2017) PyHab: Looking time and stimulus presentation script for PsychoPy. [Computer software]. Retrieved from https://github.com/jfkominsky/PyHab on {DATE}</li>
</ul>
