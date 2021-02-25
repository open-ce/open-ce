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

import sys
import os
import pathlib
import pytest
import imp
import shutil

test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'open-ce'))
open_ce = imp.load_source('open_ce', os.path.join(test_dir, '..', 'open_ce', 'open-ce'))
import open_ce.get_licenses as get_licenses
import open_ce.utils as utils
from open_ce.errors import OpenCEError

def test_get_licenses():
    '''
    This is a complete test of `get_licenses`.
    '''
    output_folder = "get_licenses_output"
    open_ce._main(["get", get_licenses.COMMAND, "--conda_env_file", "tests/test-conda-env2.yaml", "--output_folder", output_folder])

    output_file = os.path.join(output_folder, utils.DEFAULT_LICENSES_FILE)
    assert os.path.exists(output_file)
    with open(output_file) as file_stream:
        license_contents = file_stream.read()

    print(license_contents)
    assert "pytest	6.2.2	https://github.com/pytest-dev/pytest/	MIT" in license_contents

    shutil.rmtree(output_folder)

def test_get_licenses_failed_conda_create(mocker):
    '''
    This tests that an exception is thrown when `conda env create` fails.
    '''
    output_folder = "get_licenses_output"
    mocker.patch('utils.run_command_capture', side_effect=[(False, "", "")])

    with pytest.raises(OpenCEError) as err:
        open_ce._main(["get", get_licenses.COMMAND, "--conda_env_file", "tests/test-conda-env2.yaml", "--output_folder", output_folder])

    assert "Error generating licenses file." in str(err.value)

def test_get_licenses_failed_conda_remove(mocker):
    '''
    This tests that an exception is thrown when `conda env remove` is called.
    '''
    output_folder = "get_licenses_output"
    mocker.patch('utils.run_command_capture', side_effect=[(True, "", ""), (False, "", "")])
    mocker.patch('get_licenses.LicenseGenerator._add_licenses_from_environment', return_value=[])

    with pytest.raises(OpenCEError) as err:
        open_ce._main(["get", get_licenses.COMMAND, "--conda_env_file", "tests/test-conda-env2.yaml", "--output_folder", output_folder])

    assert "Error generating licenses file." in str(err.value)

def test_get_licenses_no_conda_env():
    '''
    This test ensures that an exception is thrown when no conda environment is provided.
    '''
    with pytest.raises(OpenCEError) as err:
        open_ce._main(["get", get_licenses.COMMAND])

    assert "The \'--conda_env_file\' argument is required." in str(err.value)
