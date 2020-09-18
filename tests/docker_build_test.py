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

import os
import sys
import pathlib
from datetime import date
test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'builder'))

import pytest
import helpers

import docker_build

def test_build_image(mocker):
    '''
    Simple test for build_image
    '''
    mocker.patch('os.getuid', return_value=1234)
    mocker.patch('os.getgid', return_value=5678)

    intended_image_name = docker_build.REPO_NAME + ":" + docker_build.IMAGE_NAME + "-1234"

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=["docker build",
                                                               "-t " + intended_image_name])))

    result, image_name = docker_build.build_image()
    assert result == 0
    assert image_name == intended_image_name

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

    assert docker_build._create_container(container_name, image_name, output_folder) == 0

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

    assert docker_build._copy_to_container(src, dest, container) == 0

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

    assert docker_build._execute_in_container(container, command) == 0
 
def test_build_in_container(mocker):
    '''
    Simple test for build_in_container
    '''
    mocker.patch('os.getcwd', return_value='/my_dir')
    mocker.patch('os.path.isdir', return_value=[False, True])
    mocker.patch('os.mkdir')

    mocker.patch('os.system', return_value=0)

    assert docker_build.build_in_container("my_image", "condabuild", ["path/to/my_script.py", "arg1", "arg2"]) == 0

def test_docker_build_failures(mocker, capsys):
    '''
    Test situations where the docker commands fail
    '''
    image = "my_image"
    output_folder = "condabuild"
    cmd = ["path/to/my_script.py", "arg1", "arg2"]

    mocker.patch('os.path.isdir', return_value = True)

    # Failed create
    mocker.patch('docker_build._create_container', return_value=1)

    assert docker_build.build_in_container(image, output_folder, cmd) == 1
    captured = capsys.readouterr()
    assert "Error creating" in captured.out

    # Failed first copy
    mocker.patch('docker_build._create_container', return_value=0)
    mocker.patch('docker_build._copy_to_container', side_effect=[1,1])

    assert docker_build.build_in_container(image, output_folder, cmd) == 1
    captured = capsys.readouterr()
    assert "Error copying open-ce directory" in captured.out

    # Failed second copy
    mocker.patch('docker_build._copy_to_container', side_effect=[0,1])

    assert docker_build.build_in_container(image, output_folder, cmd) == 1
    captured = capsys.readouterr()
    assert "Error copying local_files" in captured.out

    # Failed start
    mocker.patch('docker_build._copy_to_container', return_value=0)
    mocker.patch('docker_build._start_container', return_value=1)

    assert docker_build.build_in_container(image, output_folder, cmd) == 1
    captured = capsys.readouterr()
    assert "Error starting" in captured.out

    # Failed execute
    mocker.patch('docker_build._start_container', return_value=0)
    mocker.patch('docker_build._execute_in_container', return_value=1)

    assert docker_build.build_in_container(image, output_folder, cmd) == 1
    captured = capsys.readouterr()
    assert "Error executing" in captured.out

def test_build_with_docker(mocker):
    '''
    Simple test for build_with_docker
    '''
    image_name = "my_image"
    output_folder = "condabuild"
    arg_strings = ["path/to/my_script.py", "--docker_build", "my-env.yaml"]

    mocker.patch('docker_build.build_image', return_value=(0, image_name))

    mocker.patch('docker_build.build_in_container', return_value=0)

    assert docker_build.build_with_docker(output_folder, arg_strings) == 0

def test_build_with_docker_failures(mocker, capsys):
    '''
    Failure cases for build_with_docker
    '''
    image_name = "my_image"
    output_folder = "condabuild"
    arg_strings = ["path/to/my_script.py", "--docker_build", "my-env.yaml"]

    mocker.patch('docker_build.build_image', return_value=(1, image_name))

    assert docker_build.build_with_docker(output_folder, arg_strings) == 1
    captured = capsys.readouterr()
    assert "Failure building image" in captured.out
