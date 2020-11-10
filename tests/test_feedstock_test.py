# *****************************************************************
#
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2020. All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# *****************************************************************

import sys
import os
import pathlib

test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'open-ce'))

import test_feedstock
import utils

def test_test_feedstock(mocker, capsys):
    '''
    This is a complete test of `test_feedstock`.
    '''

    test_file = {"tests":
                    [{"name" : "Test 1", "command" : "echo Test 1"},
                    {"name" : "Test 2", "command" : "echo Test 2a\necho Test2b"}]}

    mocker.patch('os.path.exists', side_effect=(lambda x: x in (utils.DEFAULT_TEST_CONFIG_FILE, './')))
    mocker.patch('yaml.safe_load', return_value=test_file)
    mocker.patch('builtins.open', side_effect=None)

    assert test_feedstock.test_feedstock(["--conda_env_file", "tests/test-conda-env2.yaml"]) == 0
    captured = capsys.readouterr()
    assert "Running: Create conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out
    assert "Running: Test 1" in captured.out
    assert "Running: Test 2" in captured.out
    assert "Running: Remove conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out

def test_test_feedstock_failed_tests(mocker, capsys):
    '''
    Test that failed tests work correctly.
    '''

    test_file = {"tests":
                    [{"name" : "Test 1", "command" : "[ 1 -eq 2 ]"},
                    {"name" : "Test 2", "command" : "[ 1 -eq 1 ]"},
                    {"name" : "Test 3", "command" : "[ 1 -eq 3 ]"}]}

    mocker.patch('os.path.exists', side_effect=(lambda x: x in (utils.DEFAULT_TEST_CONFIG_FILE, './')))
    mocker.patch('yaml.safe_load', return_value=test_file)
    mocker.patch('builtins.open', side_effect=None)

    assert test_feedstock.test_feedstock(["--conda_env_file", "tests/test-conda-env2.yaml"]) == 2
    captured = capsys.readouterr()
    assert "Failed test: Test 1" in captured.out
    assert "Failed test: Test 3" in captured.out
    assert not "Failed test: Test 2" in captured.out

def test_test_feedstock_working_dir(mocker, capsys):
    '''
    This tests that the working_dir arg works correctly.
    '''

    test_file = {"tests":
                    [{"name" : "Test 1", "command" : "echo Test 1"},
                    {"name" : "Test 2", "command" : "echo Test 2a\necho Test2b"}]}

    working_dir = "./my_working_dir"

    mocker.patch('os.path.exists', side_effect=(lambda x: x == utils.DEFAULT_TEST_CONFIG_FILE or (x == working_dir and pathlib.Path(x).exists())))
    mocker.patch('yaml.safe_load', return_value=test_file)
    mocker.patch('builtins.open', side_effect=None)

    assert not os.path.exists(working_dir)
    assert test_feedstock.test_feedstock(["--conda_env_file", "../tests/test-conda-env2.yaml", "--test_working_dir", working_dir]) == 0
    assert os.path.exists(working_dir)
    os.rmdir(working_dir)
    captured = capsys.readouterr()
    assert "Running: Create conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out
    assert "Running: Test 1" in captured.out
    assert "Running: Test 2" in captured.out
    assert "Running: Remove conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out
