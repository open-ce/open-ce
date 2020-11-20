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
import pytest
import imp

test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'open-ce'))

open_ce = imp.load_source('open_ce', os.path.join(test_dir, '..', 'open-ce', 'open-ce'))
import test_feedstock
import utils
from errors import OpenCEError

orig_load_test_file = test_feedstock.load_test_file
def mock_load_test_file(x, y):
    return orig_load_test_file(x, y)

def test_test_feedstock(mocker, capsys):
    '''
    This is a complete test of `test_feedstock`.
    '''

    mocker.patch('test_feedstock.load_test_file', side_effect=(lambda x, y: mock_load_test_file(os.path.join(test_dir, "open-ce-tests1.yaml"), y)))

    open_ce._main(["test", test_feedstock.COMMAND, "--conda_env_file", "tests/test-conda-env2.yaml"])
    captured = capsys.readouterr()
    assert "Running: Create conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out
    assert "Running: Test 1" in captured.out
    assert not "Running: Test 2" in captured.out
    assert "Running: Remove conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out

def test_test_feedstock_failed_tests(mocker, capsys):
    '''
    Test that failed tests work correctly.
    '''

    mocker.patch('test_feedstock.load_test_file', side_effect=(lambda x, y: mock_load_test_file(os.path.join(test_dir, "open-ce-tests2.yaml"), y)))
    mocker.patch('conda_env_file_generator.get_variant_string', return_value=None)

    with pytest.raises(OpenCEError) as exc:
        open_ce._main(["test", test_feedstock.COMMAND, "--conda_env_file", "tests/test-conda-env2.yaml"])
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
    mocker.patch('test_feedstock.load_test_file', side_effect=(lambda x, y: mock_load_test_file(os.path.join(test_dir, "open-ce-tests1.yaml"), my_variants)))

    assert not os.path.exists(working_dir)
    open_ce._main(["test", test_feedstock.COMMAND, "--conda_env_file", "tests/test-conda-env2.yaml", "--test_working_dir", working_dir])
    assert os.path.exists(working_dir)
    os.rmdir(working_dir)
    captured = capsys.readouterr()
    assert "Running: Create conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out
    assert "Running: Test 1" in captured.out
    assert "Running: Test 2" in captured.out
    assert "Running: Remove conda environment " + utils.CONDA_ENV_FILENAME_PREFIX in captured.out
