#!/usr/bin/env python
"""
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
"""

import os
import shutil
from open_ce import utils
from open_ce.inputs import Argument
from open_ce.errors import OpenCEError, Error

COMMAND = 'image'
DESCRIPTION = 'Run Open-CE tools within a container'
ARGUMENTS = [Argument.LOCAL_CONDA_CHANNEL, Argument.CONDA_ENV_FILE]

OPEN_CE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
RUNTIME_IMAGE_NAME = "opence-runtime"
RUNTIME_IMAGE_PATH = os.path.join(OPEN_CE_PATH, "images", RUNTIME_IMAGE_NAME)
REPO_NAME = "open-ce"
IMAGE_NAME = "open-ce-runtime"
BUILD_CONTEXT = "."

OPENCE_USER = "opence"
LOCAL_CONDA_CHANNEL_IN_IMG = "opence-local-conda-channel"
TARGET_DIR = "/home/{}/{}".format(OPENCE_USER, LOCAL_CONDA_CHANNEL_IN_IMG)

DOCKER_TOOL = "docker"

def build_image(local_conda_channel, conda_env_file):
    """
    Build a docker image from the Dockerfile in RUNTIME_IMAGE_PATH.
    Returns a result code and the name of the new image.
    """
    image_name = REPO_NAME + ":" + IMAGE_NAME + "-" + str(os.getuid())
    build_cmd = DOCKER_TOOL + " build "
    build_cmd += "-f " + os.path.join(RUNTIME_IMAGE_PATH, "Dockerfile") + " "
    build_cmd += "-t " + image_name + " "
    build_cmd += "--build-arg OPENCE_USER=" + OPENCE_USER + " "
    build_cmd += "--build-arg LOCAL_CONDA_CHANNEL=" + local_conda_channel + " "
    build_cmd += "--build-arg CONDA_ENV_FILE=" + conda_env_file + " "
    build_cmd += "--build-arg TARGET_DIR=" + TARGET_DIR + " "
    build_cmd += BUILD_CONTEXT

    print("Docker build command: ", build_cmd)
    if os.system(build_cmd):
        raise OpenCEError(Error.BUILD_IMAGE, image_name)

    return image_name

def _validate_input_paths(local_conda_channel, conda_env_file):

    # Check if path exists
    if not os.path.exists(local_conda_channel) or not os.path.exists(conda_env_file):
        raise OpenCEError(Error.INCORRECT_INPUT_PATHS)

    # Check if local conda channel path is subdir of the docker build context
    if not utils.is_subdir(local_conda_channel, os.path.abspath(BUILD_CONTEXT)):
        raise OpenCEError(Error.LOCAL_CHANNEL_NOT_IN_CONTEXT)

def build_runtime_docker_image(args):
    """
    Create a runtime image which will have a conda environment created
    using locally built conda packages and environment file.
    """
    local_conda_channel = os.path.abspath(args.local_conda_channel)
    conda_env_file = os.path.abspath(args.conda_env_file)
    _validate_input_paths(local_conda_channel, conda_env_file)

    # Copy the conda environment file into the local conda channel with a new name and modify it
    conda_env_runtime_filename = os.path.splitext(os.path.basename(args.conda_env_file))[0]+'-runtime.yaml'
    conda_env_runtime_file = os.path.join(local_conda_channel, os.path.basename(conda_env_runtime_filename))

    try:
        shutil.copy(conda_env_file, conda_env_runtime_file)
    except shutil.SameFileError:
        print("Info: Environment file already in local conda channel.")
    utils.replace_conda_env_channels(conda_env_runtime_file, r'file:.*', "file:/{}".format(TARGET_DIR))

    # Check if input local conda channel path is absolute
    if os.path.isabs(args.local_conda_channel):
        # make it relative to BUILD CONTEXT
        args.local_conda_channel = os.path.relpath(args.local_conda_channel, start=BUILD_CONTEXT)

    image_name = build_image(args.local_conda_channel, os.path.basename(conda_env_runtime_file))

    print("Docker image with name {} is built successfully.".format(image_name))

ENTRY_FUNCTION = build_runtime_docker_image
