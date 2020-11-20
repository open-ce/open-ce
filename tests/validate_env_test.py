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
import validate_env
from errors import OpenCEError

def test_validate_env():
    '''
    Positive test for validate_env.
    '''
    env_file = os.path.join(test_dir, 'test-env2.yaml')
    open_ce._main(["validate", validate_env.COMMAND, env_file])

def test_validate_env_negative():
    '''
    Negative test for validate_env.
    '''
    env_file = os.path.join(test_dir, 'test-env-invalid1.yaml')
    with pytest.raises(OpenCEError) as exc:
        open_ce._main(["validate", validate_env.COMMAND, env_file])
    assert "Unexpected key chnnels was found in " in str(exc.value)

def test_validate_env_wrong_external_deps(mocker,):
    '''
    Test that validate env correctly handles invalid data for external dependencies.
    '''
    unused_env_for_arg = os.path.join(test_dir, 'test-env-invalid1.yaml')
    env_file = { 'packages' : [{ 'feedstock' : 'test1' }], 'external_dependencies' : 'ext_dep' }
    mocker.patch('conda_utils.render_yaml', return_value=env_file)

    with pytest.raises(OpenCEError) as exc:
        open_ce._main(["validate", validate_env.COMMAND, unused_env_for_arg])
    assert "ext_dep is not of expected type <class 'list'>" in str(exc.value)

def test_validate_env_dict_for_external_deps(mocker,):
    '''
    Test that validate env correctly handles erroneously passing a dict for external dependencies.
    '''
    unused_env_for_arg = os.path.join(test_dir, 'test-env-invalid1.yaml')
    env_file = { 'packages' : [{ 'feedstock' : 'test1' }], 'external_dependencies' : [{ 'feedstock' : 'ext_dep'}] }
    mocker.patch('conda_utils.render_yaml', return_value=env_file)

    with pytest.raises(OpenCEError) as exc:
        open_ce._main(["validate", validate_env.COMMAND, unused_env_for_arg])
    assert "{'feedstock': 'ext_dep'} is not of expected type <class 'str'>" in str(exc.value)
