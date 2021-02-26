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
import sys
import pathlib
import pytest
from argparse import Namespace

test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'open-ce'))
import helpers
import container_build
import utils
from errors import OpenCEError

def test_build_image(mocker):
    '''
    Simple test for build_image
    '''
    mocker.patch('os.getuid', return_value=1234)
    mocker.patch('os.getgid', return_value=5678)

    #CUDA build
    cuda_version="11.0"
    container_tool = "docker"
    intended_image_name = container_build.REPO_NAME + ":" + container_build.IMAGE_NAME + "-cuda" + cuda_version + "-1234"

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=["docker build",
                                                               "-t " + intended_image_name])))

    assert container_build.build_image("test", "test", container_tool, cuda_version) == intended_image_name

    #CPU build  
    intended_image_name = container_build.REPO_NAME + ":" + container_build.IMAGE_NAME + "-cpu" + "-1234"

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=["docker build",
                                                               "-t " + intended_image_name])))
    assert container_build.build_image("test", "test", container_tool) == intended_image_name

def test_create_container(mocker):
    '''
    Simple test for _create_container
    '''
    mocker.patch('os.getcwd', return_value='/my_dir')
    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('os.mkdir')

    container_name = "my_container"
    image_name = "my_image"
    output_folder = "condabuild"
    env_folders = ["/test/my_envs"]
    container_tool = "docker"
    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=[container_tool + " create",
                                                               "--name " + container_name,
                                                               "-v /my_dir/" + output_folder,
                                                               "-v /test/my_envs",
                                                               image_name])))

    container_build._create_container(container_name, image_name, output_folder, env_folders, container_tool)

def test_copy_to_container(mocker):
    '''
    Simple test for _copy_to_container
    '''
    src = "my_src"
    dest = "my_dest"
    container = "my_container"
    container_tool = "docker" 
    
    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=[container_tool + " cp",
                                                               container + ":"])))

    container_build._copy_to_container(src, dest, container, container_tool)

def test_execute_in_container(mocker):
    '''
    Simple test for _execute_in_container
    '''
    container = "my_container"
    command = "my_script.py arg1 arg2"
    container_tool = "docker"

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=[container_tool + " exec " + container,
                                                               "my_script.py arg1 arg2"])))

    container_build._execute_in_container(container, command, container_tool)

def make_args(command="build",
              sub_command="env",
              output_folder="condabuild",
              env_config_file="open-ce.yaml",
              conda_build_config="conda_build_config.yaml",
              build_types="cuda",
              cuda_versions="10.2",
              container_build_args="",
              container_tool=utils.DEFAULT_CONTAINER_TOOL,
              **kwargs):
    return Namespace(command = command,
                     sub_command = sub_command,
                     output_folder = output_folder,
                     env_config_file = env_config_file,
                     conda_build_config = conda_build_config,
                     build_types=build_types,
                     cuda_versions=cuda_versions,
                     container_build_args=container_build_args,
                     container_tool=container_tool,
                     **kwargs)

def test_build_in_container(mocker):
    '''
    Simple test for build_in_container
    '''
    mocker.patch('os.getcwd', return_value='/my_dir')
    mocker.patch('os.path.isdir', return_value=[False, True])
    mocker.patch('os.mkdir')

    mocker.patch('os.system', return_value=0)

    args = make_args()

    container_build.build_in_container("my_image", args, ["arg1", "arg2"])

def test_container_build_failures(mocker):
    '''
    Test situations where the container commands fail
    '''
    image = "my_image"
    args = make_args()
    cmd = ["arg1", "arg2"]

    mocker.patch('os.path.isdir', return_value = True)

    # Failed create
    mocker.patch('os.system', return_value=1)

    with pytest.raises(OpenCEError) as exc:
        container_build.build_in_container(image, args, cmd)
    assert "Error creating" in str(exc.value)

    # Failed first copy
    mocker.patch('container_build._create_container', return_value=None)

    with pytest.raises(OpenCEError) as exc:
        container_build.build_in_container(image, args, cmd)
    assert "Error copying" in str(exc.value)
    assert "open-ce" in str(exc.value)

    # Failed second copy
    mocker.patch('os.system', side_effect=[0,1])

    with pytest.raises(OpenCEError) as exc:
        container_build.build_in_container(image, args, cmd)
    assert "Error copying" in str(exc.value)
    assert "conda_build_config" in str(exc.value)

    # Failed third copy
    mocker.patch('os.system', side_effect=[0,0,1])

    with pytest.raises(OpenCEError) as exc:
        container_build.build_in_container(image, args, cmd)
    assert "Error copying" in str(exc.value)
    assert "local_files" in str(exc.value)

    # Failed start
    mocker.patch('container_build._copy_to_container', return_value=None)
    mocker.patch('os.system', return_value=1)

    with pytest.raises(OpenCEError) as exc:
        container_build.build_in_container(image, args, cmd)
    assert "Error starting" in str(exc.value)

    # Failed execute
    mocker.patch('container_build._start_container', return_value=None)
    mocker.patch('os.system', return_value=1)

    with pytest.raises(OpenCEError) as exc:
        container_build.build_in_container(image, args, cmd)
    assert "Error executing" in str(exc.value)

def test_build_with_container_tool(mocker):
    '''
    Simple test for build_with_container_tool
    '''
    image_name = "my_image"
    arg_strings = ["path/to/open-ce", "build", "env", "--container_build", "my-env.yaml",
                   "--cuda_versions", "10.2", "--build_types", "cuda"]
    args = make_args()
    mocker.patch('container_build.build_image', return_value=(0, image_name))

    mocker.patch('container_build.build_in_container', return_value=0)

    container_build.build_with_container_tool(args, arg_strings)

def test_build_with_container_tool_failures(mocker):
    '''
    Failure cases for build_with_container_tool
    '''
    arg_strings = ["path/to/open-ce", "build", "env", "--container_build", "my-env.yaml",
                   "--cuda_versions", "10.2", "--build_types", "cuda"]
    args = make_args()
    mocker.patch('os.system', return_value=1)

    with pytest.raises(OpenCEError) as exc:
        container_build.build_with_container_tool(args, arg_strings)
    assert "Failure building image" in str(exc.value)

def test_generate_dockerfile_name():
    '''
    Simple test for _generate_dockerfile_name
    '''
    #CUDA build
    build_type = "cuda"
    cuda_version = "11.0"
    image_path, docker_file_name = container_build._generate_dockerfile_name(build_type, cuda_version)
    assert docker_file_name == os.path.join(image_path, "Dockerfile.cuda-" + cuda_version)

    #CPU build
    build_type = "cpu"
    cuda_version = "11.0"
    image_path, docker_file_name = container_build._generate_dockerfile_name(build_type, cuda_version)
    assert docker_file_name == os.path.join(image_path, "Dockerfile")

    #Unsupported CUDA version
    build_type = "cuda"
    cuda_version = "9.0"
    with pytest.raises(OpenCEError) as exc:
        container_build._generate_dockerfile_name(build_type, cuda_version)
    assert "Cannot build using container" in str(exc.value)

def test_capable_of_cuda_containers(mocker):
    '''
    Simple test for _capable_of_cuda_containers
    '''
    cuda_version = "10.2"
    mocker.patch('utils.cuda_driver_installed', return_value=0)
    ret = container_build._capable_of_cuda_containers(cuda_version)
    assert ret == True

    mocker.patch('utils.cuda_driver_installed', return_value=1)
    mocker.patch('utils.cuda_level_supported', return_value=0)
    ret = container_build._capable_of_cuda_containers(cuda_version)
    assert ret == False

    mocker.patch('utils.cuda_driver_installed', return_value=1)
    mocker.patch('utils.cuda_level_supported', return_value=1)
    ret = container_build._capable_of_cuda_containers(cuda_version)
    assert ret == True

def test_build_with_container_tool_incompatible_cuda_versions(mocker):
    '''
    Tests that passing incompatible value in --cuda_versions argument fails.
    '''
    arg_strings = ["path/to/open-ce", "build", "env", "--container_build", "my-env.yaml",
                   "--cuda_versions", "10.2", "--build_types", "cuda"]
    args = make_args()

    mocker.patch('container_build._capable_of_cuda_containers', return_value=0)
    mocker.patch('utils.get_driver_level',return_value="abc")

    with pytest.raises(OpenCEError) as exc:
        container_build.build_with_container_tool(args, arg_strings)
    assert "Driver level" in str(exc.value)

def test_container_build_with_container_tool_build_args(mocker):
    '''
    Tests that container build arguments are parsed and passed to container build.
    '''
    build_args = "--build-arg ENV1=test1 --build-arg ENV2=test2 same_setting 0,1"

    arg_strings = ["path/to/open-ce", "build", "env", "--container_build", "my-env.yaml",
                   "--container_build_args", build_args]
    args = make_args()
    mocker.patch('os.system', return_value=0)

    container_build.build_with_container_tool(args, arg_strings)

def test_container_build_with_container_tool(mocker):
    '''
    Tests that container_tool argument is parsed and passed to container build.
    '''
    container_tool = "podman"

    arg_strings = ["path/to/open-ce", "build", "env", "--container_build", "my-env.yaml",
                   "--container_tool", container_tool]
    args = make_args()
    mocker.patch('os.system', return_value=0)

    container_build.build_with_container_tool(args, arg_strings)
