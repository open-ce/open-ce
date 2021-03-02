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
import pytest
import imp
import shutil

test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'open_ce'))
import open_ce
opence = imp.load_source('open_ce', os.path.join(test_dir, '..', 'open_ce', 'open-ce'))
import test_feedstock
import utils
from open_ce.errors import OpenCEError

orig_load_test_file = test_feedstock.load_test_file
def mock_load_test_file(x, y):
    return orig_load_test_file(x, y)

def test_test_feedstock(mocker, capsys):
    '''
    This is a complete test of `test_feedstock`.
    '''

    mocker.patch('open_ce.test_feedstock.load_test_file', side_effect=(lambda x, y: mock_load_test_file(os.path.join(test_dir, "open-ce-tests1.yaml"), y)))

    opence._main(["test", test_feedstock.COMMAND, "--conda_env_file", "tests/test-conda-env2.yaml"])
    captured = capsys.readouterr()
    assert "Running: Create conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out
    assert "Running: Test 1" in captured.out
    assert not "Running: Test 2" in captured.out
    assert "Running: Remove conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out

def test_test_feedstock_failed_tests(mocker, capsys):
    '''
    Test that failed tests work correctly.
    '''

    mocker.patch('open_ce.test_feedstock.load_test_file', side_effect=(lambda x, y: mock_load_test_file(os.path.join(test_dir, "open-ce-tests2.yaml"), y)))
    mocker.patch('open_ce.conda_env_file_generator.get_variant_string', return_value=None)

    with pytest.raises(OpenCEError) as exc:
        opence._main(["test", test_feedstock.COMMAND, "--conda_env_file", "tests/test-conda-env2.yaml"])
    assert "There were 2 test failures" in str(exc.value)
    captured = capsys.readouterr()
    assert "Failed test: Test 1" in captured.out
    assert "Failed test: Test 3" in captured.out
    assert not "Failed test: Test 2" in captured.out

def test_test_feedstock_working_dir(mocker, capsys):
    '''
    This tests that the working_dir arg works correctly.
    Also sets a different build_type variant than what is in `test_test_feedstock`.
    '''

    working_dir = "./my_working_dir"
    my_variants = {'build_type' : 'cpu'}
    mocker.patch('open_ce.test_feedstock.load_test_file', side_effect=(lambda x, y: mock_load_test_file(os.path.join(test_dir, "open-ce-tests1.yaml"), my_variants)))

    assert not os.path.exists(working_dir)
    opence._main(["test", test_feedstock.COMMAND, "--conda_env_file", "tests/test-conda-env2.yaml", "--test_working_dir", working_dir])
    assert os.path.exists(working_dir)
    shutil.rmtree(working_dir)
    captured = capsys.readouterr()
    assert "Running: Create conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out
    assert "Running: Test 1" in captured.out
    assert "Running: Test 2" in captured.out
    assert "Running: Remove conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out

def test_test_feedstock_labels(mocker, capsys):
    '''
    Test that labels work correctly.
    '''

    mocker.patch('open_ce.test_feedstock.load_test_file', side_effect=(lambda x, y: mock_load_test_file(os.path.join(test_dir, "open-ce-tests3.yaml"), y)))

    opence._main(["test", test_feedstock.COMMAND, "--conda_env_file", "tests/test-conda-env2.yaml"])
    captured = capsys.readouterr()
    assert not "Running: Create conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out
    assert not "Running: Test Long" in captured.out
    assert not "Running: Test Distributed" in captured.out
    assert not "Running: Test Long and Distributed" in captured.out
    assert not "Running: Remove conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out

    opence._main(["test", test_feedstock.COMMAND, "--conda_env_file", "tests/test-conda-env2.yaml", "--test_labels", "long"])
    captured = capsys.readouterr()
    assert "Running: Create conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out
    assert "Running: Test Long" in captured.out
    assert not "Running: Test Distributed" in captured.out
    assert not "Running: Test Long and Distributed" in captured.out
    assert "Running: Remove conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out

    opence._main(["test", test_feedstock.COMMAND, "--conda_env_file", "tests/test-conda-env2.yaml", "--test_labels", "distributed"])
    captured = capsys.readouterr()
    assert "Running: Create conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out
    assert not "Running: Test Long" in captured.out
    assert "Running: Test Distributed" in captured.out
    assert not "Running: Test Long and Distributed" in captured.out
    assert "Running: Remove conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out

    opence._main(["test", test_feedstock.COMMAND, "--conda_env_file", "tests/test-conda-env2.yaml", "--test_labels", "long,distributed"])
    captured = capsys.readouterr()
    assert "Running: Create conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out
    assert "Running: Test Long" in captured.out
    assert "Running: Test Distributed" in captured.out
    assert "Running: Test Long and Distributed" in captured.out
    assert "Running: Remove conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out

def test_test_feedstock_invalid_test_file(mocker,):
    '''
    Test that labels work correctly.
    '''

    mocker.patch('open_ce.test_feedstock.load_test_file', side_effect=(lambda x, y: mock_load_test_file(os.path.join(test_dir, "open-ce-tests4.yaml"), y)))

    with pytest.raises(OpenCEError) as exc:
        opence._main(["test", test_feedstock.COMMAND, "--conda_env_file", "tests/test-conda-env2.yaml"])
    assert "Unexpected Error: ['Test 1'] is not of expected type <class 'str'>" in str(exc.value)
