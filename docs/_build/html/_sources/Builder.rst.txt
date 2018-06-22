=======
Builder
=======

The builder code uses PsychoPy's visual library to create a rudimentary GUI for creating PyHab studies. The GUI itself
mostly consists of clickable shapes that open dialog boxes. The only notable exception is the system for creating
conditions, which creates an entire new UI in the window.

When the builder's save functions are called, they create a complete, self-contained folder which includes the experiment
setitngs file (a csv), a launcher script, the PyHab module folder with PyHabClass, PyHabClassPL, and PyHabBuilder, and
copies of all of the stimuli and attention-getters to a stimuli folder.

.. autoclass:: PyHab.PyHabBuilder.PyHabBuilder
    :members:
