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

import build_env
from inputs import Argument

COMMAND = 'env'
DESCRIPTION = 'Test Open-CE Environment'
ARGUMENTS = [Argument.CONDA_BUILD_CONFIG, Argument.OUTPUT_FOLDER,
             Argument.CHANNELS, Argument.ENV_FILE,
             Argument.PACKAGES,
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
