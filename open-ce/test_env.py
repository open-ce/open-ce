"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""

import build_env
from inputs import Argument

COMMAND = 'env'
DESCRIPTION = 'Test Open-CE Environment'
ARGUMENTS = [Argument.CONDA_BUILD_CONFIG, Argument.OUTPUT_FOLDER,
             Argument.CHANNELS, Argument.ENV_FILE,
             Argument.REPOSITORY_FOLDER, Argument.PYTHON_VERSIONS,
             Argument.BUILD_TYPES, Argument.MPI_TYPES,
             Argument.CUDA_VERSIONS, Argument.DOCKER_BUILD,
             Argument.GIT_LOCATION, Argument.GIT_TAG_FOR_ENV,
             Argument.TEST_LABELS]

def test_env(args):
    '''Entry Function'''
    args.skip_build_packages = True
    args.run_tests = True
    build_env.build_env(args)

ENTRY_FUNCTION = test_env
