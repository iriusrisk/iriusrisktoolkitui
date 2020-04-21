======================
A generateDS.py demo
======================

Running the example
=====================

This directory contains a simple example of the use of
generateDS.py.

On Linux, you can run a test with the shell script
`run-full-test.sh` as follows:

    $ ./run-full-test.sh test

The above shell script will use `people.xsd` to produce `testsup.py`
(with the "-o" command line option) and `testsub.py` (with the "-s"
command line option).  It then runs the generated subclass
(`testsub.py`) file to parse and export `people.xml`.


Generating validator bodies
=============================

You can generate code containing validator bodies by running
`run-full-test-validators.sh`.  After running that shell script, the
code in `Validators/FlowType.py` will have been copying into the
method `validate_FlowType`.  (`Validators/percent.py` is not used in
this example.)


.. vim:ft=rst:
