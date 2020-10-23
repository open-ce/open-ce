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
from utils import OpenCEError

def make_parser():
    ''' Parser for input arguments '''
    arguments = [utils.Argument.ENV_FILE, utils.Argument.PYTHON_VERSIONS,
                 utils.Argument.BUILD_TYPES, utils.Argument.MPI_TYPES]
    parser = utils.make_parser(arguments,
                               description = 'Lint Environment Files')
    return parser

def validate_env(arg_strings=None):
    '''
    Entry function.
    '''
    parser = make_parser()
    args = parser.parse_args(arg_strings)
    variants = utils.make_variants(args.python_versions, args.build_types, args.mpi_types)

    for variant in variants:
        try:
            env_config.load_env_config_files(args.env_config_file, variant)
        except OpenCEError as exc:
            raise OpenCEError("Error validating \"{}\" for variant {}\n{}".format(args.env_config_file,
                                                                                  str(variant),
                                                                                  exc.msg)) from exc

if __name__ == '__main__':
    try:
        validate_env()
    except OpenCEError as err:
        print(err.msg, file=sys.stderr)
        sys.exit(1)

    sys.exit(0)
