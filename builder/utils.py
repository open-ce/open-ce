"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""

import os
import argparse

DEFAULT_CONDA_BUILD_CONFIG = os.path.join(os.path.dirname(__file__),
                                          "..", "conda_build_config.yaml")

class OpenCEError(Exception):
    """
    Exception class for errors that occur in an Open-CE tool.
    """
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

def make_common_parser(*args, **kwargs):
    '''
    Make the parser arguments that are common between other files.
    '''
    parser = argparse.ArgumentParser(*args, **kwargs)

    parser.add_argument(
        '--conda_build_config',
        type=str,
        default=DEFAULT_CONDA_BUILD_CONFIG,
        help='Location of conda_build_config.yaml file.')

    parser.add_argument(
        '--output_folder',
        type=str,
        default='condabuild',
        help='Path where built conda packages will be saved.')

    parser.add_argument(
        '--channels',
        dest='channels_list',
        action='append',
        type=str,
        default=list(),
        help='Conda channels to be used.')

    return parser

def parse_arg_list(arg_list):
    ''' Turn a comma delimited string into a python list'''
    if isinstance(arg_list, list):
        return arg_list
    return arg_list.split(",") if not arg_list is None else list()

def remove_version(package):
    '''Remove conda version from dependency.'''
    return package.split()[0].split("=")[0]
