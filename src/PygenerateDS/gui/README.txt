======================================
Internationalizing generateds_gui.py
======================================

Overview
==========

This document describes the procedure for translating the strings
used in ``generateds_gui.py`` to another language.

In summary, the procedure is the following:

1. Run ``forgui.py`` with the "-c" command line option to create a
   translation (dictionary) file.

2. Edit the new translation (dictionary) file and add translations
   of the strings in it.

3. Run ``forgui.py`` with the "-d" command line option to create a
   new glade file.

Users can now run ``generateds_gui.py`` with the "--impl-gui" option
to reference the new glade file so as to use the new translation.


Details
=========

Run "forgui.py -c"
--------------------

This will produce a new dictionary (translation) file that you will
use to specify your translations.

For example, the following will the file ``fr.dictionary``::

    $ python forgui.py generateds_gui.glade -c fr.dictionary

Edit the new translation
--------------------------

In the new dictionary (translation) file, you will find lines of the
form::

    an english language string<-|->an english language string

Replace the characters to the right of ``<-|->`` with the equivalent
phrase in the target language.


Run "forgui.py -d"
--------------------

This will produce a new glade file containing your translations.

For example, the following will produce the file
``generateds_gui_fr.glade``::

    $ python forgui.py generateds_gui.py -d fr.dictionary


Using the new translation
---------------------------

Users will use the new translation by running ``generateds_gui.py``
with the "--impl-gui" command line option.

For example, the translation created in the above example can be run
as follows::

    $ python generateds_gui.py --impl-gui=generateds_gui_fr.glade


.. vim:ft=rst:
