==============
Windows-specific troubleshooting
==============

There are a couple of issues you may run into on Windows specifically, but they all have relatively straightforward solutions.

Universal suggestions::
    Always run PsychoPy as an administrator. Otherwise you may get "permissions errors" whenever it tries to do anything, but especially when it tries to save files.

    You can set PsychoPy to always run as administrator by right-clicking on the program icon and going into its properties.

    Running PyHab off a network drive is not recommended. Some labs have reported that even when running as administrator, it will not save files correctly if it is not running from a local drive.


============
Problems playing movies
============

There are two major classes of errors you are likely to run into:

Problem #1: Crashes on "Loading Movies" with errors that mention "Memory" or "Overflow", or no error messages at all. This means you don't have enough RAM for the movies you are trying to play::
    Explanation: The way PsychoPy plays media on Windows is extraordinarily inefficient, for some reason. Even if you have a lot of RAM, long experiments with long movie files can sometimes exceed your computer's capacity.

    Try re-encoding your movies in different formats that are more memory efficient (h.264, MPEG-4), making them lower-resolution, or cutting down their framerate.

Problem #2: Crashes on "Loading Movies" with errors that include “imageio.core.fetching.NeedDownloadError: Need ffmpeg exe.”::
    Explanation: This is a codec which needs to be install into PsychoPy directly, but it can be done from the coder interface relatively easily and only needs to be done once per computer.

    1. Make sure you are running PsychoPy as an administrator.

    2. In the lower part of the PsychoPy coder window, there are two tabs, “Output” and “Shell”. Click “Shell” and you should see something like this:
        .. image:: ShellTab.png

    3. At the >>>, type (without quotes): “import imageio” and hit return.

    4. At the >>>, type (without quotes) “imageio.plugins.ffmpeg.download()” and hit return. This will cause a bunch of text to appear. Let it do its thing, it may take a few seconds.

    5. When it gets back to the >>> prompt, go back to the “Output” tab, and then try running the experiment again. It should now work. If not, it failed to install the codec, and you’ll need to try the above steps again (make sure the commands are entered properly, and if it gives you a “permissions error”, make sure you are running as an administrator).
