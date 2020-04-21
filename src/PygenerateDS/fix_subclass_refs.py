#!/usr/bin/env python

"""
synopsis:
    Fix up subclass references so that the classes in the superclass
    module refer to classes in a specified submodule.
    The superclass module was generated with the generateDS.py "-o"
    command line option; the subclass module was generated with "-s".
    The intended use is to be able to switch between different versions
    of submodules generated from the same XML schema.
usage:
    python fix_subclass_refs.py <supermodname> <submodname1> <submodname2>
examples:
    From the command line for testing purposes:
        python fix_subclass_refs.py datalib datasub1 datasub2
    From within an application -- Suppose we want to switch between the use
    of submodule_1 and submodule_2 while our application is running:
        import fix_subclass_refs
        import supermodule
        import submodule_1
        import submodule_2
            ...
        fix_subclass_refs.fix_up_refs(supermodule, submodule_1)
        submodule_1.parse('data.xml')
            ...
        fix_subclass_refs.fix_up_refs(supermodule, submodule_2)
        submodule_2.parse('data.xml')
"""


from __future__ import print_function
import sys
import importlib


def fix_up_refs(supermod, submod):
    """Change the value of class variable "subclass" so that it refers
    to the subclass in "submod".
    """
    count = 0
    for superclassname in supermod.__all__:
        superclass = getattr(supermod, superclassname)
        if superclass.subclass is None:
            # never happens?
            print('*** {} missing subclass'.format(superclassname))
            pass
        else:
            subclassname = superclass.subclass.__name__
            subclass = getattr(submod, subclassname)
            superclass.subclass = subclass
            count += 1
    return count


def show(supermod):
    count = 0
    for superclassname in supermod.__all__:
        superclass = getattr(supermod, superclassname)
        print('subclass: {}'.format(superclass.subclass))
        count += 1
    return count


def test(supermodname, submodname1, submodname2):
    supermod = importlib.import_module(supermodname)
    submod1 = importlib.import_module(submodname1)
    importlib.import_module(submodname2)
    count = show(supermod)
    print('count: {}'.format(count))
    count = fix_up_refs(supermod, submod1)
    print('fix-up count: {}'.format(count))
    raw_input('Press Enter to continue ')
    print('-' * 50)
    count = show(supermod)
    print('count: {}'.format(count))


def main():
    args = sys.argv[1:]
    if len(args) != 3:
        sys.exit(__doc__)
    supermodname = args[0]
    submodname1 = args[1]
    submodname2 = args[2]
    test(supermodname, submodname1, submodname2)


if __name__ == '__main__':
    main()
