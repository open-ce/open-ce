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
import yaml
import pytest

test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'open-ce'))
import helpers
import build_image
from errors import OpenCEError, Error

def test_build_image_positive_case(mocker):
    '''
    Simple test for build_image
    '''
    intended_image_name = build_image.REPO_NAME + ":" + build_image.IMAGE_NAME

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=["docker build",
                                                               "-t " + intended_image_name])))

    arg_strings = ["--local_conda_channel", "tests/testcondabuild", "--conda_env_file", "tests/test-conda-env.yaml"]
    build_image.build_runtime_docker_image(arg_strings)
    os.remove("tests/testcondabuild/test-conda-env.yaml")

def test_not_existing_local_conda_channel(mocker):
    '''
    Test for not existing local conda channel
    '''
    # Local conda channel dir passed doesn't exist
    arg_strings = ["--local_conda_channel", "tests/not-existing-dir", "--conda_env_file", "tests/test-conda-env.yaml"]
    with pytest.raises(OpenCEError) as exc:
        build_image.build_runtime_docker_image(arg_strings)
    assert Error.INCORRECT_INPUT_PATHS.value[1] in str(exc.value)

def test_not_existing_env_file(mocker):
    '''
    Test for not existing conda environment file
    '''

    # Conda environment file passed doesn't exist
    arg_strings = ["--local_conda_channel", "tests/testcondabuild", "--conda_env_file", "tests/non-existing-env.yaml"]
    with pytest.raises(OpenCEError) as exc:
        build_image.build_runtime_docker_image(arg_strings)
    assert Error.INCORRECT_INPUT_PATHS.value[1] in str(exc.value)

def test_out_of_context_local_channel(mocker):
    '''
    Test for local conda channel not being in the build context
    '''

    # Local conda channel dir passed isn't within the build context
    TEST_CONDA_CHANNEL_DIR = "../../testcondabuild-pytest"

    if not os.path.exists(os.path.abspath(TEST_CONDA_CHANNEL_DIR)):
        os.mkdir(TEST_CONDA_CHANNEL_DIR)

    arg_strings = ["--local_conda_channel", TEST_CONDA_CHANNEL_DIR, "--conda_env_file", "tests/test-conda-env.yaml"]
    with pytest.raises(OpenCEError) as exc:
        build_image.build_runtime_docker_image(arg_strings)
    assert Error.LOCAL_CHANNEL_NOT_IN_CONTEXT.value[1] in str(exc.value)

    os.rmdir(TEST_CONDA_CHANNEL_DIR)

def test_local_conda_channel_with_absolute_path(mocker):
    '''
    Test for build_image with local conda channel with its absolute path
    '''
    intended_image_name = build_image.REPO_NAME + ":" + build_image.IMAGE_NAME

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=["docker build",
                                                               "-t " + intended_image_name])))

    arg_strings = ["--local_conda_channel", os.path.join(test_dir, "testcondabuild"), "--conda_env_file", "tests/test-conda-env.yaml"]
    build_image.build_runtime_docker_image(arg_strings)
    os.remove("tests/testcondabuild/test-conda-env.yaml")

def get_channel_being_modified(conda_env_file):
    with open(conda_env_file, 'r') as file_handle:
        env_info = yaml.safe_load(file_handle)

    channels = env_info['channels']
    channel_index = 0
    channel_being_modified = ""
    for channel in channels:
        if channel.startswith("file:"):
            channel_index = channels.index(channel)
            channel_being_modified = channel
            break

    return channel_index, channel_being_modified

def test_channel_update_in_conda_env(mocker):
    '''
    Test to see if channel is being updated in the conda env file before passing to build_image
    '''

    intended_image_name = build_image.REPO_NAME + ":" + build_image.IMAGE_NAME

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=["docker build",
                                                               "-t " + intended_image_name])))

    channel_index_before, channel_to_be_modified = get_channel_being_modified("tests/test-conda-env.yaml")
 
    arg_strings = ["--local_conda_channel", os.path.join(test_dir, "testcondabuild"), "--conda_env_file", "tests/test-conda-env.yaml"]
    build_image.build_runtime_docker_image(arg_strings)
    
    # We copy conda environment file to the passed local conda channel before updating it
    channel_index_after, channel_modified = get_channel_being_modified("tests/testcondabuild/test-conda-env.yaml")
    
    assert channel_modified == "file:/{}".format(build_image.TARGET_DIR)
    assert channel_index_before == channel_index_after

    # Cleanup
    os.remove("tests/testcondabuild/test-conda-env.yaml") 

def test_for_failed_docker_build_cmd(mocker):
    '''
    Simple test for build_image being failed due to some error in building the image
    '''
    mocker.patch('os.system', return_value=1)

    arg_strings = ["--local_conda_channel", "tests/testcondabuild", "--conda_env_file", "tests/test-conda-env.yaml"]
    with pytest.raises(OpenCEError) as exc:
        build_image.build_runtime_docker_image(arg_strings)
    assert "Failure building image" in str(exc.value)

    os.remove("tests/testcondabuild/test-conda-env.yaml")
