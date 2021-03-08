#!/usr/bin/env python

"""
# *****************************************************************
# (C) Copyright IBM Corp. 2020, 2021. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# *****************************************************************
"""

from open_ce import env_config
from open_ce import utils
from open_ce.inputs import Argument
from open_ce.errors import OpenCEError, Error

COMMAND = 'env'

DESCRIPTION = 'Lint Environment Files'

ARGUMENTS = [Argument.ENV_FILE, Argument.PYTHON_VERSIONS,
             Argument.BUILD_TYPES, Argument.MPI_TYPES, Argument.CUDA_VERSIONS]

def validate_env(args):
    '''Entry Function'''
    variants = utils.make_variants(args.python_versions, args.build_types,
                                   args.mpi_types, args.cuda_versions)

    for variant in variants:
        try:
            env_config.load_env_config_files(args.env_config_file, variant)
        except OpenCEError as exc:
            raise OpenCEError(Error.VALIDATE_ENV, args.env_config_file, str(variant), exc.msg) from exc

ENTRY_FUNCTION = validate_env
