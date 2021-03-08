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

import os
import pathlib
import pytest
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

test_dir = pathlib.Path(__file__).parent.absolute()

spec = spec_from_loader("opence", SourceFileLoader("opence", os.path.join(test_dir, '..', 'open_ce', 'open-ce')))
opence = module_from_spec(spec)
spec.loader.exec_module(opence)

import open_ce.validate_env as validate_env
from open_ce.errors import OpenCEError

def test_validate_env():
    '''
    Positive test for validate_env.
    '''
    env_file = os.path.join(test_dir, 'test-env2.yaml')
    opence._main(["validate", validate_env.COMMAND, env_file])

def test_validate_env_negative():
    '''
    Negative test for validate_env.
    '''
    env_file = os.path.join(test_dir, 'test-env-invalid1.yaml')
    with pytest.raises(OpenCEError) as exc:
        opence._main(["validate", validate_env.COMMAND, env_file])
    assert "Unexpected key chnnels was found in " in str(exc.value)

def test_validate_env_wrong_external_deps(mocker,):
    '''
    Test that validate env correctly handles invalid data for external dependencies.
    '''
    unused_env_for_arg = os.path.join(test_dir, 'test-env-invalid1.yaml')
    env_file = { 'packages' : [{ 'feedstock' : 'test1' }], 'external_dependencies' : 'ext_dep' }
    mocker.patch('conda_build.metadata.MetaData.get_rendered_recipe_text', return_value=env_file)

    with pytest.raises(OpenCEError) as exc:
        opence._main(["validate", validate_env.COMMAND, unused_env_for_arg])
    assert "ext_dep is not of expected type <class 'list'>" in str(exc.value)

def test_validate_env_dict_for_external_deps(mocker,):
    '''
    Test that validate env correctly handles erroneously passing a dict for external dependencies.
    '''
    unused_env_for_arg = os.path.join(test_dir, 'test-env-invalid1.yaml')
    env_file = { 'packages' : [{ 'feedstock' : 'test1' }], 'external_dependencies' : [{ 'feedstock' : 'ext_dep'}] }
    mocker.patch('conda_build.metadata.MetaData.get_rendered_recipe_text', return_value=env_file)

    with pytest.raises(OpenCEError) as exc:
        opence._main(["validate", validate_env.COMMAND, unused_env_for_arg])
    assert "{'feedstock': 'ext_dep'} is not of expected type <class 'str'>" in str(exc.value)
