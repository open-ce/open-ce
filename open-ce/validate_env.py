#!/usr/bin/env python

"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""

import env_config
import utils
from inputs import Argument
from errors import OpenCEError, Error

COMMAND = 'env'

DESCRIPTION = 'Lint Environment Files'

ARGUMENTS = [Argument.ENV_FILE, Argument.PYTHON_VERSIONS,
             Argument.BUILD_TYPES, Argument.MPI_TYPES]

def validate_env(args):
    '''Entry Function'''
    variants = utils.make_variants(args.python_versions, args.build_types, args.mpi_types)

    for variant in variants:
        try:
            env_config.load_env_config_files(args.env_config_file, variant)
        except OpenCEError as exc:
            raise OpenCEError(Error.VALIDATE_ENV, args.env_config_file, str(variant), exc.msg) from exc

ENTRY_FUNCTION = validate_env
