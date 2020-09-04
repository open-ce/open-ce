# *****************************************************************
#
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2020. All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# *****************************************************************

import os

class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def validate_cli(cli_string, expect=[], reject=[], retval=0, *args, **kwargs):
    """
    Used to mock os.system with the assumption that it is making a call to 'conda-build'.

    Args:
        cli_string: The placeholder argument for the system command.
        expect: A list of strings that must occur in the 'cli_string' arg.
        reject: A list of strings that cannot occur in the 'cli_string' arg.
        retval: The mocked value to return from 'os.system'.
    Returns:
        retval
    """
    for term in expect:
        assert term in cli_string
    for term in reject:
        assert term not in cli_string
    return retval

current_dir = os.getcwd()
chdir_count = 0
def validate_chdir(arg1, expected_dirs=[]):
    """
    Used to mock os.chdir. Each time a directory is changed, the global counter ch_dir is incremented,
    and each change is validated against the expected_dirs list.
    The current directory is tracked in `current_dir` and used by `mocked_getcwd`.

    Args:
        arg1: The placeholder argumentfor the chdir command.
        expected_dirs: The list of directories that are expected to be chdired during execution..
    Returns:
        0
    """
    global current_dir
    global chdir_count
    if expected_dirs and chdir_count < len(expected_dirs):
        assert arg1 == expected_dirs[chdir_count]
    current_dir = arg1
    chdir_count+=1
    return 0

def mocked_getcwd():
    global current_dir
    return current_dir