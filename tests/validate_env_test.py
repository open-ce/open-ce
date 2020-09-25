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

import pytest
import validate_env

def test_validate_env():
    '''
    Positive test for validate_env.
    '''
    env_file = os.path.join(test_dir, 'test-env2.yaml')
    assert validate_env.validate_env([env_file]) == 0

def test_validate_env_negative(capsys):
    '''
    Negative test for validate_env.
    '''
    env_file = os.path.join(test_dir, 'test-env-invalid1.yaml')
    assert validate_env.validate_env([env_file]) == 1
    captured = capsys.readouterr()
    assert "chnnels is not a valid key in the environment file." in captured.err
