
# *****************************************************************
# (C) Copyright IBM Corp. 2021. All Rights Reserved.
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

import os
import pathlib
import pytest
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

test_dir = pathlib.Path(__file__).parent.absolute()

spec = spec_from_loader("opence", SourceFileLoader("opence", os.path.join(test_dir, '..', 'open_ce', 'open-ce')))
opence = module_from_spec(spec)
spec.loader.exec_module(opence)

from open_ce.inputs import make_parser, _create_env_config_paths, Argument

def test_create_env_config_paths(mocker):
    '''
    Test the _create_env_config_paths function.
    '''
    mocker.patch('os.path.exists', return_value=0)
    envs_repo = "open-ce-environments"

    parser = make_parser([Argument.ENV_FILE, Argument.GIT_LOCATION, Argument.GIT_TAG_FOR_ENV])

    args = parser.parse_args(["test-env.yaml"])
    _create_env_config_paths(args)
    assert args.env_config_file[0] == "https://raw.githubusercontent.com/open-ce/" + envs_repo + "/main/envs/test-env.yaml"

    args = parser.parse_args(["test-env"])
    _create_env_config_paths(args)
    assert args.env_config_file[0] == "https://raw.githubusercontent.com/open-ce/" + envs_repo + "/main/envs/test-env.yaml"

    args = parser.parse_args(["test-env", "--git_tag_for_env", "my_tag"])
    _create_env_config_paths(args)
    assert args.env_config_file[0] == "https://raw.githubusercontent.com/open-ce/" + envs_repo + "/my_tag/envs/test-env.yaml"

    args = parser.parse_args(["test-env", "--git_location", "https://github.com/my_org"])
    _create_env_config_paths(args)
    assert args.env_config_file[0] == "https://raw.githubusercontent.com/my_org/" + envs_repo + "/main/envs/test-env.yaml"
