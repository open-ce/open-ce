#!/usr/bin/env python

"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************

*******************************************************************************
Script: envlint.py

Summary:
  Performs syntactic validation on environment files used by build_env.py from
  the open-ce project.

Description:
  This script will take a YAML build env file and will check that file and all
  dependencies for syntactic errors.

Usage:
   $ envlint.py env_files [env_files ...]
For usage description of arguments, this script supports use of --help:
   $ envlint.py --help

*******************************************************************************
"""

import argparse
import sys
import builder.build_env as build_env

variants = { 'python' : ['3.6','3.7'], 'build_type' : ['cpu', 'cuda'] }

def make_parser():
    ''' Parser input arguments '''
    parser = argparse.ArgumentParser(
        description = 'Lint Environment Files',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        'env_files',
        nargs='+',
        type=str,
        help="""Files to Lint.""")

    return parser

def main(arg_strings=None):
    parser = make_parser()
    args = parser.parse_args(arg_strings)

    retval,_ = build_env.load_env_config_files(args.env_files, variants)

    return retval

if __name__ == '__main__':
    sys.exit(main())
