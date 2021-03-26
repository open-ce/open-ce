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

import pathlib
import errno
import pytest

test_dir = pathlib.Path(__file__).parent.absolute()

import open_ce.inputs as inputs
import open_ce.utils as utils
from open_ce.errors import OpenCEError

def test_parse_arg_list_list_input():
    '''
    Parse arg list should return the input argument if it's already a list.
    '''
    list_input = ["a", "b", "c"]
    assert list_input == inputs.parse_arg_list(list_input)

def test_parse_arg_list_small_string_input():
    '''
    Tests that parse_arg_list works for a simple case.
    '''
    string_input = "a,b,c"
    list_output = ["a", "b", "c"]
    assert list_output == inputs.parse_arg_list(string_input)

def test_parse_arg_list_large_string_input():
    '''
    Test parse_arg_list with a more complicated input, including spaces.
    '''
    string_input = "this,is a, big  , test  ,"
    list_output = ["this", "is a", " big  ", " test  ", ""]
    assert list_output == inputs.parse_arg_list(string_input)

def test_cuda_level_supported(mocker):
    '''
    Simple test for cuda_level_supported
    '''
    #expected cuda version supported by the system
    cuda_version="10.2"
    mocker.patch('open_ce.utils.get_driver_cuda_level',return_value="10.2")
    assert utils.cuda_level_supported(cuda_version) == True

    #expected cuda version not supported by the system
    cuda_version="11.0"
    mocker.patch('open_ce.utils.get_driver_cuda_level',return_value="10.2")
    assert utils.cuda_level_supported(cuda_version) == False

def test_get_driver_cuda_level(mocker):
    '''
    Simple test for get_driver_cuda_level
    '''
    mocker.patch('subprocess.check_output',return_value=bytes("CUDA Version: 10.2","utf-8"))
    assert utils.get_driver_cuda_level() == "10.2" 

def test_get_driver_cuda_level_failures(mocker):
    '''
    Simple test for get_driver_cuda_level failure scenarios
    '''
    mocker.patch('subprocess.check_output',side_effect=OSError(errno.ENOENT,"" ))
    with pytest.raises(OpenCEError) as exc:
        utils.get_driver_cuda_level()
    assert "nvidia-smi command not found" in str(exc.value)

    mocker.patch('subprocess.check_output',side_effect=OSError(errno.EPERM,"" ))
    with pytest.raises(OpenCEError) as exc:
        utils.get_driver_cuda_level()
    assert "nvidia-smi command unexpectedly failed" in str(exc.value)

def test_get_driver_level(mocker):
    '''
    Simple test for get_driver_level
    '''    
    mocker.patch('subprocess.check_output',return_value=bytes("Driver Version: 440.33.01","utf-8"))
    assert utils.get_driver_level() == "440.33.01"

def test_get_driver_level_failures(mocker):
    '''
    Simple test for get_driver_level failure scenarios
    '''
    mocker.patch('subprocess.check_output',side_effect=OSError(errno.ENOENT,"" ))
    with pytest.raises(OpenCEError) as exc:
        utils.get_driver_level()
    assert "nvidia-smi command not found" in str(exc.value)

    mocker.patch('subprocess.check_output',side_effect=OSError(errno.EPERM,"" ))
    with pytest.raises(OpenCEError) as exc:
        utils.get_driver_level()
    assert "nvidia-smi command unexpectedly failed" in str(exc.value)

def test_cuda_driver_installed(mocker):
    '''
    Simple test for cuda_driver_installed
    '''
    mocker.patch('subprocess.check_output',return_value=bytes("nvidia   123","utf-8"))
    assert utils.cuda_driver_installed() == True

def test_cuda_driver_installed_failures(mocker):
    '''
    Simple test for cuda_driver_installed failure scenarios
    '''
    mocker.patch('subprocess.check_output',side_effect=OSError(errno.ENOENT,"" ))
    with pytest.raises(OpenCEError) as exc:
        utils.cuda_driver_installed()
    assert "lsmod command not found" in str(exc.value)    

    mocker.patch('subprocess.check_output',side_effect=OSError(errno.EPERM,"" ))
    with pytest.raises(OpenCEError) as exc:
        utils.cuda_driver_installed()
    assert "lsmod command unexpectedly failed" in str(exc.value)

def test_get_branch_of_tag(mocker):
    '''
    Simple tests for the get_up_to_date_branch
    '''
    sample_output = "main\n  remotes/origin/main\n* remotes/origin/r2.4.1   \n"
    mocker.patch('open_ce.utils.run_command_capture', side_effect=[(True, sample_output, ""), (False, sample_output, "")])

    assert utils._get_branch_of_tag("mytag") == "remotes/origin/r2.4.1"

    assert utils._get_branch_of_tag("mytag") == "mytag"

