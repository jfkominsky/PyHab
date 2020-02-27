#For making PyHab studies from a blank slate. 
#Simply hit the green running-silhouette button to begin! 
#(You can also press CTRL-R or Command-R)
from PyHab import PyHabBuilder as PB
import os
os.chdir(os.path.dirname(os.path.realpath(__file__))) # require for PsychoPy3 2020.1.0 and later (for now)

builder = PB.PyHabBuilder()
builder.run()
