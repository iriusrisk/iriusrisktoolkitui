============
Unit Tests
============

How to run the unit test
==========================

To run the unit tests, do::

    $ cd tests/         # this directory
    $ python test.py

You will need to use Python 2.7 and not Python 3 to run the unit
tests.  The unit tests will run under Python 3, but the tests fail.
That's because of (1) differences in the comments at the
top of generated files; (2) some ordering differences, possibly
because of dicts; etc. all of which do not matter when you actually
run the generated code, I believe.

