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

test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'open-ce'))
import validate_env
from utils import OpenCEError

def test_validate_env():
    '''
    Positive test for validate_env.
    '''
    env_file = os.path.join(test_dir, 'test-env2.yaml')
    validate_env.validate_env([env_file])

def test_validate_env_negative(capsys):
    '''
    Negative test for validate_env.
    '''
    env_file = os.path.join(test_dir, 'test-env-invalid1.yaml')
    with pytest.raises(OpenCEError) as err:
        validate_env.validate_env([env_file])
    captured = capsys.readouterr()
    assert "Unexpected key chnnels was found in " in captured.err

def test_validate_env_wrong_external_deps(mocker, capsys):
    '''
    Test that validate env correctly handles invalid data for external dependencies.
    '''
    unused_env_for_arg = os.path.join(test_dir, 'test-env-invalid1.yaml')
    env_file =b'''
packages:
    - feedstock : test1
external_dependencies: ext_dep
'''
    mocker.patch('builtins.open', mocker.mock_open(read_data=env_file))
    with pytest.raises(OpenCEError) as err:
        validate_env.validate_env([unused_env_for_arg])
    captured = capsys.readouterr()
    assert "ext_dep is not of expected type <class 'list'>" in captured.err

def test_validate_env_dict_for_external_deps(mocker, capsys):
    '''
    Test that validate env correctly handles erroneously passing a dict for external dependencies.
    '''
    unused_env_for_arg = os.path.join(test_dir, 'test-env-invalid1.yaml')
    env_file =b'''
packages:
    - feedstock : test1
external_dependencies:
    - feedstock : ext_dep
'''
    mocker.patch('builtins.open', mocker.mock_open(read_data=env_file))
    with pytest.raises(OpenCEError) as err:
        validate_env.validate_env([unused_env_for_arg])
    captured = capsys.readouterr()
    assert "{'feedstock': 'ext_dep'} is not of expected type <class 'str'>" in captured.err
