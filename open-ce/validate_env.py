#!/usr/bin/env python

"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************

*******************************************************************************
Script: validate_env.py

Summary:
  Performs syntactic validation on environment files used by build_env.py from
  the open-ce project.

Description:
  This script will take a YAML build env file and will check that file and all
  dependencies for syntactic errors.

*******************************************************************************
"""

import sys
import env_config
import utils

def make_parser():
    ''' Parser for input arguments '''
    arguments = [utils.Argument.ENV_FILE, utils.Argument.PYTHON_VERSIONS,
                 utils.Argument.BUILD_TYPES]
    parser = utils.make_parser(arguments,
                               description = 'Lint Environment Files')
    return parser

def validate_env(arg_strings=None):
    '''
    Entry function.
    '''
    parser = make_parser()
    args = parser.parse_args(arg_strings)
    variants = [{ 'python' : py_vers, 'build_type' : build_type } for py_vers in utils.parse_arg_list(args.python_versions)
                                                                  for build_type in utils.parse_arg_list(args.build_types)]
    retval = 0
    for variant in variants:
        result,_ = env_config.load_env_config_files(args.env_config_file, variant)
        retval += result

    return retval

if __name__ == '__main__':
    sys.exit(validate_env())
