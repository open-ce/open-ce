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

def test_test_feedstock(mocker, capsys):
    '''
    This is a complete test of `test_feedstock`.
    '''

    test_file = {"tests":
                    [{"name" : "Test 1", "command" : "echo Test 1"},
                    {"name" : "Test 2", "command" : "echo Test 2a\necho Test2b"}]}

    mocker.patch('yaml.safe_load', return_value=test_file)
    mocker.patch('builtins.open', side_effect=None)

    assert test_feedstock.test_feedstock(["--conda_env_file", "tests/test-conda-env2.yaml"]) == 0
    captured = capsys.readouterr()
    assert "Running: Create conda environment open-ce-conda-env-" in captured.out
    assert "Running: Test 1" in captured.out
    assert "Running: Test 2" in captured.out
    assert "Running: Remove conda environment open-ce-conda-env-" in captured.out

def test_test_feedstock_failed_tests(mocker, capsys):
    '''
    Test that failed tests work correctly.
    '''

    test_file = {"tests":
                    [{"name" : "Test 1", "command" : "[ 1 -eq 2 ]"},
                    {"name" : "Test 2", "command" : "[ 1 -eq 1 ]"},
                    {"name" : "Test 3", "command" : "[ 1 -eq 3 ]"}]}

    mocker.patch('yaml.safe_load', return_value=test_file)
    mocker.patch('builtins.open', side_effect=None)

    assert test_feedstock.test_feedstock(["--conda_env_file", "tests/test-conda-env2.yaml"]) == 2
    captured = capsys.readouterr()
    assert "Failed test: Test 1" in captured.out
    assert "Failed test: Test 3" in captured.out
    assert not "Failed test: Test 2" in captured.out
