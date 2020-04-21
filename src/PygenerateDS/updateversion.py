#!/usr/bin/env python

"""
Usage:
    python updateversion.py [options]
Options:
    -h, --help          Display this help message.
    -v x.xx, --version=x.xx
                        New version.  Required.
    --verbose           Print extra info.
Example:
    python updateversion.py -v 1.17c
"""


#
# Imports

from __future__ import print_function
import sys
import getopt
import re
import shutil


#
# Globals and constants

VERBOSE = False

REPL_SPEC = [
    {
        'filename': 'setup.py',
        'pattern': r'(##VERSION##\s*version=")([\w\.\-]*)(",\s*##VERSION##)',
    },
    {
        'filename': 'generateDS.py',
        'pattern': r"(##VERSION##\s*VERSION = ')([\w\.\-]*)('\s*##VERSION##)",
    },
    {
        'filename': 'process_includes.py',
        'pattern': r"(##VERSION##\s*VERSION = ')([\w\.\-]*)('\s*##VERSION##)",
    },
    {
        'filename': 'generateDS.txt',
        'pattern': r"(.. version\s*:revision: )([\w\.\-]*)(\s*.. version)",
    },
    {
        'filename': 'generateds_gui_notes.txt',
        'pattern': r"(.. version\s*:revision: )([\w\.\-]*)(\s*.. version)",
    },
    {
        'filename': 'librarytemplate_howto.txt',
        'pattern': r"(.. version\s*:revision: )([\w\.\-]*)(\s*.. version)",
    },
    {
        'filename': 'tutorial/generateds_tutorial.txt',
        'pattern': r"(.. version\s*:revision: )([\w\.\-]*)(\s*.. version)",
    },
    {
        'filename': 'gui/generateds_gui.py',
        'pattern': r"(##VERSION##\s*VERSION = ')([\w\.\-]*)('\s*##VERSION##)",
    },
]


#
# Functions for external use

def updateversion(version):
    replfunc = replfuncmaker(version)
    for spec in REPL_SPEC:
        targetfilename = spec['filename']
        if VERBOSE:
            print('updating: "%s"' % (targetfilename, ))
        targetfile = open(targetfilename, 'r')
        content = targetfile.read()
        targetfile.close()
        content1 = re.sub(
            spec['pattern'],
            replfunc,
            content)
        update1file(targetfilename, content1)


# Classes


#
# Functions for internal use and testing

def update1file(targetfilename, content):
    backupfilename = targetfilename + '.bak'
    shutil.copy2(targetfilename, backupfilename)
    targetfile = open(targetfilename, 'w')
    targetfile.write(content)
    targetfile.close()
    #shutil.copymode(backupfilename, targetfilename)


def replfuncmaker(version):
    def replfunc(matchobj):
        if VERBOSE:
            print('(replfunc) matchobj.groups()', matchobj.groups())
        return matchobj.group(1) + version + matchobj.group(3)
    return replfunc


USAGE_TEXT = __doc__


def usage():
    print(USAGE_TEXT)
    sys.exit(1)


def main():
    global VERBOSE
    args = sys.argv[1:]
    try:
        opts, args = getopt.getopt(args, 'hv:', [
            'help', 'version=', 'verbose', ])
    except:
        usage()
    version = None
    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-v', '--version'):
            version = val
        elif opt in ('--verbose', ):
            VERBOSE = True
    if len(args) != 0 or version is None:
        usage()
    updateversion(version)


if __name__ == '__main__':
    #import pdb; pdb.set_trace()
    main()
