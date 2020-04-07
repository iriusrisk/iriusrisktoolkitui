============================================
Instructions on running the Django support
============================================

Also see:
http://www.davekuhlman.org/generateDS.html#django-generating-models-and-forms

Although, there are likely other configurations that will work, one
reasonably simple way is the following:

1. Download the source distribution of generateDS with the
   following::

       $ hg clone https://dkuhlman@bitbucket.org/dkuhlman/generateds

   Alternatively, you can download a Zip file from here:
   https://bitbucket.org/dkuhlman/generateds/downloads/

   Or, a tar file from here:
   https://pypi.python.org/pypi/generateDS

   And, then unroll it.

2. Change directory to the ``django`` directory (i.e. the directory
   containing this file)::

       $ cd generateds/django

3. In that directory, either, (a) create, a symbolic link to
   ``generateDS.py``::

       $ ln -s ../generateDS.py

   Or, (b) copy ``generateDS.py`` to that directory::

       $ cp ../generateDS.py .

4. In that directory, Run ``gends_run_gen_django.py``.  For
   example::

       $ cp ../tests/people.xsd .
       $ ./gends_run_gen_django.py -f -v people.xsd

If the above ran successfully, it should have created these files::

    models.py
    forms.py
    admin.py


.. vim:ft=rst:
