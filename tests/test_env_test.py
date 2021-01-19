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

import sys
import os
import pathlib
import imp

test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'open-ce'))

open_ce = imp.load_source('open_ce', os.path.join(test_dir, '..', 'open-ce', 'open-ce'))
import test_env

def test_test_env(mocker):
    '''
    This is a test for test_env. Since test_env is a wrapper for build_env, we are mainly relying
    on the tests for build_env.
    '''
    def validate_build_env(args):
        assert args.skip_build_packages == True
        assert args.run_tests == True

    mocker.patch('build_env.build_env', side_effect=validate_build_env)

    open_ce._main(["test", test_env.COMMAND, "some_env_file.yaml"])
