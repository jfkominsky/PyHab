==============
Backwards compatibility in PsychoPy3 2020.1.0 and 2020.1.1
==============

**Note: This has been fixed as of PsychoPy 2020.1.3, it is strongly recommended you update to that version of PsychoPy**

Versions 2020.1.0 and 2020.1.1 of PsychoPy have a quirk that will break PyHab experiments made in versions prior to 0.9. The good news is that it is easily fixed. The short explanation is that these two versions of PsychoPy (but not those before and probably not those after) change the “working directory” of the script when you run it. Whereas PyHab expects the working directory to be the experiment folder, 2020.1.0 and 2020.1.1 move it somewhere else. The solution is simply to tell PsychoPy to put it back in the same folder as the experiment launcher.
In order to do this, open your experiment’s launcher file. On line 7 (the line after "import csv, os"), paste the following:

os.chdir(os.path.dirname(os.path.realpath(__file__)))

Save the launcher, and you’re good to go. Experiments made in version 0.9 have this built in, and versions of PsychoPy after 2020.1.1 should change this behavior back to the way it was before, but in this very narrow window, if you need to make a pre-0.9 experiment run in PsychoPy3 2020.1.0 or 2020.1.1, this is what you need.