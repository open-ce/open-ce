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

import helpers
import open_ce.build_image as build_image
from open_ce.errors import OpenCEError, Error

def test_build_image_positive_case(mocker):
    '''
    Simple test for build_runtime_image
    '''
    intended_image_name = build_image.REPO_NAME + ":" + build_image.IMAGE_NAME

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=["docker build",
                                                               "-t " + intended_image_name])))

    arg_strings = ["build", build_image.COMMAND, "--local_conda_channel", "tests/testcondabuild", "--conda_env_file", "tests/test-conda-env.yaml"]
    opence._main(arg_strings)

def test_not_existing_local_conda_channel():
    '''
    Test for not existing local conda channel
    '''
    # Local conda channel dir passed doesn't exist
    arg_strings = ["build", build_image.COMMAND, "--local_conda_channel", "tests/not-existing-dir", "--conda_env_file", "tests/test-conda-env.yaml"]
    with pytest.raises(OpenCEError) as exc:
        opence._main(arg_strings)
    assert Error.INCORRECT_INPUT_PATHS.value[1] in str(exc.value)

def test_not_existing_env_file():
    '''
    Test for not existing conda environment file
    '''

    # Conda environment file passed doesn't exist
    arg_strings = ["build", build_image.COMMAND, "--local_conda_channel", "tests/testcondabuild", "--conda_env_file", "tests/non-existing-env.yaml"]
    with pytest.raises(OpenCEError) as exc:
        opence._main(arg_strings)
    assert Error.INCORRECT_INPUT_PATHS.value[1] in str(exc.value)

def test_out_of_context_local_channel():
    '''
    Test for local conda channel not being in the build context
    '''

    # Local conda channel dir passed isn't within the build context
    TEST_CONDA_CHANNEL_DIR = "../testcondabuild-pytest"

    if not os.path.exists(os.path.abspath(TEST_CONDA_CHANNEL_DIR)):
        os.mkdir(TEST_CONDA_CHANNEL_DIR)

    arg_strings = ["build", build_image.COMMAND, "--local_conda_channel", TEST_CONDA_CHANNEL_DIR, "--conda_env_file", "tests/test-conda-env.yaml"]
    with pytest.raises(OpenCEError) as exc:
        opence._main(arg_strings)
    assert Error.LOCAL_CHANNEL_NOT_IN_CONTEXT.value[1] in str(exc.value)

    os.rmdir(TEST_CONDA_CHANNEL_DIR)

def test_local_conda_channel_with_absolute_path(mocker):
    '''
    Test for build_runtime_image with local conda channel with its absolute path
    '''
    intended_image_name = build_image.REPO_NAME + ":" + build_image.IMAGE_NAME

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=["docker build",
                                                               "-t " + intended_image_name])))

    arg_strings = ["build", build_image.COMMAND, "--local_conda_channel", os.path.join(test_dir, "testcondabuild"), "--conda_env_file", "tests/test-conda-env.yaml"]
    opence._main(arg_strings)

def test_for_failed_docker_build_cmd(mocker):
    '''
    Simple test for build_runtime_image being failed due to some error in building the image
    '''
    mocker.patch('os.system', return_value=1)

    arg_strings = ["build", build_image.COMMAND, "--local_conda_channel", "tests/testcondabuild", "--conda_env_file", "tests/test-conda-env.yaml"]
    with pytest.raises(OpenCEError) as exc:
        opence._main(arg_strings)
    assert "Failure building image" in str(exc.value)

def test_modified_file_removed(mocker):
    '''
    Make sure the copied conda env file was deleted afterwards
    '''

    intended_image_name = build_image.REPO_NAME + ":" + build_image.IMAGE_NAME

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=["docker build",
                                                               "-t " + intended_image_name])))
    arg_strings = ["build", build_image.COMMAND, "--local_conda_channel", "tests/testcondabuild", "--conda_env_file", "tests/test-conda-env.yaml"]
    opence._main(arg_strings)

    assert not os.path.exists("tests/testcondabuild/test-conda-env-runtime.yaml")
