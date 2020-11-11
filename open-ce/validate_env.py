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

import env_config
import utils
from errors import OpenCEError, Error

COMMAND = 'validate_env'

DESCRIPTION = 'Lint Environment Files'

ARGUMENTS = [utils.Argument.ENV_FILE, utils.Argument.PYTHON_VERSIONS,
             utils.Argument.BUILD_TYPES, utils.Argument.MPI_TYPES]

def validate_env(args):
    '''Entry Function'''
    variants = utils.make_variants(args.python_versions, args.build_types, args.mpi_types)

    for variant in variants:
        try:
            env_config.load_env_config_files(args.env_config_file, variant)
        except OpenCEError as exc:
            raise OpenCEError(Error.VALIDATE_ENV, args.env_config_file, str(variant), exc.msg) from exc
