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

test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'open-ce'))
import helpers
import docker_build
from errors import OpenCEError

def test_build_image(mocker):
    '''
    Simple test for build_image
    '''
    mocker.patch('os.getuid', return_value=1234)
    mocker.patch('os.getgid', return_value=5678)

    #CUDA build
    cuda_version="11.0"
    intended_image_name = docker_build.REPO_NAME + ":" + docker_build.IMAGE_NAME + "-cuda" + cuda_version + "-1234"

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=["docker build",
                                                               "-t " + intended_image_name])))

    assert docker_build.build_image("test", "test", cuda_version) == intended_image_name

    #CPU build  
    intended_image_name = docker_build.REPO_NAME + ":" + docker_build.IMAGE_NAME + "-cpu" + "-1234"

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=["docker build",
                                                               "-t " + intended_image_name])))
    assert docker_build.build_image("test", "test") == intended_image_name

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

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=[docker_build.DOCKER_TOOL + " create",
                                                               "--name " + container_name,
                                                               "-v /my_dir/" + output_folder,
                                                               image_name])))

    docker_build._create_container(container_name, image_name, output_folder)

def test_copy_to_container(mocker):
    '''
    Simple test for _copy_to_container
    '''
    src = "my_src"
    dest = "my_dest"
    container = "my_container"

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=[docker_build.DOCKER_TOOL + " cp",
                                                               container + ":"])))

    docker_build._copy_to_container(src, dest, container)

def test_execute_in_container(mocker):
    '''
    Simple test for _execute_in_container
    '''
    container = "my_container"
    command = "my_script.py arg1 arg2"

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=[docker_build.DOCKER_TOOL + " exec " + container,
                                                               "my_script.py arg1 arg2"])))

    docker_build._execute_in_container(container, command)

def test_build_in_container(mocker):
    '''
    Simple test for build_in_container
    '''
    mocker.patch('os.getcwd', return_value='/my_dir')
    mocker.patch('os.path.isdir', return_value=[False, True])
    mocker.patch('os.mkdir')

    mocker.patch('os.system', return_value=0)

    docker_build.build_in_container("my_image", "condabuild", ["path/to/my_script.py", "arg1", "arg2"])

def test_docker_build_failures(mocker):
    '''
    Test situations where the docker commands fail
    '''
    image = "my_image"
    output_folder = "condabuild"
    cmd = ["path/to/my_script.py", "arg1", "arg2"]

    mocker.patch('os.path.isdir', return_value = True)

    # Failed create
    mocker.patch('os.system', return_value=1)

    with pytest.raises(OpenCEError) as exc:
        docker_build.build_in_container(image, output_folder, cmd)
    assert "Error creating" in str(exc.value)

    # Failed first copy
    mocker.patch('docker_build._create_container', return_value=None)

    with pytest.raises(OpenCEError) as exc:
        docker_build.build_in_container(image, output_folder, cmd)
    assert "Error copying" in str(exc.value)
    assert "open-ce" in str(exc.value)

    # Failed second copy
    mocker.patch('os.system', side_effect=[0,1])

    with pytest.raises(OpenCEError) as exc:
        docker_build.build_in_container(image, output_folder, cmd)
    assert "Error copying" in str(exc.value)
    assert "local_files" in str(exc.value)

    # Failed start
    mocker.patch('docker_build._copy_to_container', return_value=None)
    mocker.patch('os.system', return_value=1)

    with pytest.raises(OpenCEError) as exc:
        docker_build.build_in_container(image, output_folder, cmd)
    assert "Error starting" in str(exc.value)

    # Failed execute
    mocker.patch('docker_build._start_container', return_value=None)
    mocker.patch('os.system', return_value=1)

    with pytest.raises(OpenCEError) as exc:
        docker_build.build_in_container(image, output_folder, cmd)
    assert "Error executing" in str(exc.value)

def test_build_with_docker(mocker):
    '''
    Simple test for build_with_docker
    '''
    image_name = "my_image"
    output_folder = "condabuild"
    arg_strings = ["path/to/my_script.py", "--docker_build", "my-env.yaml"]
    build_type = "cuda"
    cudatoolkit = "10.2"
    mocker.patch('docker_build.build_image', return_value=(0, image_name))

    mocker.patch('docker_build.build_in_container', return_value=0)

    docker_build.build_with_docker(output_folder, build_type, cudatoolkit, arg_strings)

def test_build_with_docker_failures(mocker):
    '''
    Failure cases for build_with_docker
    '''
    output_folder = "condabuild"
    arg_strings = ["path/to/my_script.py", "--docker_build", "my-env.yaml"]
    build_type = "cuda"
    cudatoolkit = "10.2"
    mocker.patch('os.system', return_value=1)

    with pytest.raises(OpenCEError) as exc:
        docker_build.build_with_docker(output_folder, build_type, cudatoolkit, arg_strings)
    assert "Failure building image" in str(exc.value)

def test_generate_dockerfile_name():
    '''
    Simple test for _generate_dockerfile_name
    '''
    #CUDA build
    build_type = "cuda"
    cuda_version = "11.0"
    image_path, docker_file_name = docker_build._generate_dockerfile_name(build_type, cuda_version)
    assert docker_file_name == os.path.join(image_path, "Dockerfile.cuda-" + cuda_version) 

    #CPU build 	
    build_type = "cpu"
    cuda_version = "11.0"	
    image_path, docker_file_name = docker_build._generate_dockerfile_name(build_type, cuda_version)
    assert docker_file_name == os.path.join(image_path, "Dockerfile")

    #Unsupported CUDA version
    build_type = "cuda"
    cuda_version = "9.0"	
    with pytest.raises(OpenCEError) as exc:
        docker_build._generate_dockerfile_name(build_type, cuda_version)
    assert "Cannot build using docker" in str(exc.value)	

def test_capable_of_cuda_containers(mocker):
    '''
    Simple test for _capable_of_cuda_containers 
    '''
    cuda_version = "10.2"
    mocker.patch('utils.cuda_driver_installed', return_value=0)
    ret = docker_build._capable_of_cuda_containers(cuda_version)
    assert ret == True

    mocker.patch('utils.cuda_driver_installed', return_value=1)
    mocker.patch('utils.cuda_level_supported', return_value=0)
    ret = docker_build._capable_of_cuda_containers(cuda_version)
    assert ret == False

    mocker.patch('utils.cuda_driver_installed', return_value=1)
    mocker.patch('utils.cuda_level_supported', return_value=1)
    ret = docker_build._capable_of_cuda_containers(cuda_version)
    assert ret == True

def test_build_with_docker_incompatible_cuda_versions(mocker):
    '''
    Tests that passing incompatible value in --cuda_versions argument fails.
    '''
    output_folder = "condabuild"
    arg_strings = ["path/to/my_script.py", "--docker_build", "my-env.yaml"]
    build_type = "cuda"
    cuda_versions = "11.0"

    mocker.patch('docker_build._capable_of_cuda_containers', return_value=0)
    mocker.patch('utils.get_driver_level',return_value="abc")

    with pytest.raises(OpenCEError) as exc:
        docker_build.build_with_docker(output_folder, build_type, cuda_versions, arg_strings)
    assert "Driver level" in str(exc.value)
