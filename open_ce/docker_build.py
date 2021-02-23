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
import datetime
import platform
import argparse

import open_ce.utils as utils
from open_ce.errors import OpenCEError, Error
from open_ce.inputs import Argument

OPEN_CE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
BUILD_IMAGE_NAME = "builder"
BUILD_IMAGE_PATH = os.path.join(OPEN_CE_PATH, "images", BUILD_IMAGE_NAME)
BUILD_CUDA_IMAGE_NAME = "builder-cuda-" + platform.machine()
BUILD_CUDA_IMAGE_PATH = os.path.join(OPEN_CE_PATH, "images", BUILD_CUDA_IMAGE_NAME)
LOCAL_FILES_PATH = os.path.join(os.path.join(os.getcwd(), "local_files"))
HOME_PATH = "/home/builder"

REPO_NAME = "open-ce"
IMAGE_NAME = "open-ce-builder"

DOCKER_TOOL = "docker"

def make_parser():
    ''' Parser for input arguments '''
    arguments = [Argument.DOCKER_BUILD, Argument.OUTPUT_FOLDER,
                 Argument.CONDA_BUILD_CONFIG, Argument.ENV_FILE, Argument.DOCKER_BUILD_ARGS]
    parser = argparse.ArgumentParser(arguments)
    parser.add_argument('command_placeholder', nargs=1, type=str)
    parser.add_argument('sub_command_placeholder', nargs=1, type=str)
    for argument in arguments:
        argument(parser)

    return parser

def build_image(build_image_path, dockerfile, cuda_version=None, docker_build_args=""):
    """
    Build a docker image from the Dockerfile in BUILD_IMAGE_PATH.
    Returns a result code and the name of the new image.
    """
    if cuda_version:
        image_name = REPO_NAME + ":" + IMAGE_NAME + "-cuda" + cuda_version + "-" + str(os.getuid())
    else:
        image_name = REPO_NAME + ":" + IMAGE_NAME + "-cpu-" + str(os.getuid())
    build_cmd = DOCKER_TOOL + " build "
    build_cmd += "-f " + dockerfile + " "
    build_cmd += "-t " + image_name + " "
    build_cmd += "--build-arg BUILD_ID=" + str(os.getuid()) + " "
    build_cmd += "--build-arg GROUP_ID=" + str(os.getgid()) + " "

    build_cmd += docker_build_args + " "
    build_cmd += build_image_path

    if os.system(build_cmd):
        raise OpenCEError(Error.BUILD_IMAGE, image_name)

    return image_name

def _add_volume(local_path, container_path):
    """
    Add a volume to the container.

    If local_path is None, an anonymous volume will be used.
    """
    if local_path:
        if not os.path.isdir(local_path):
            os.mkdir(local_path)
        volume_arg = "-v " + local_path + ":" + container_path + ":Z "
    else:
        volume_arg = "-v " + container_path + " "

    return volume_arg

def _mount_name(folder_path):
    if len(folder_path) <= 1:
        return ""
    return _mount_name(os.path.dirname(folder_path)) + os.path.basename(folder_path)

def _create_container(container_name, image_name, output_folder, env_folders):
    """
    Create a docker container
    """
    # Create the container
    docker_cmd = DOCKER_TOOL + " create -i --rm --name " + container_name + " "

    # Add output folder
    docker_cmd += _add_volume(os.path.abspath(output_folder),
                              os.path.abspath(os.path.join(HOME_PATH, utils.DEFAULT_OUTPUT_FOLDER)))

    # Add cache directory
    docker_cmd += _add_volume(None, os.path.join(HOME_PATH, ".cache"))

    # Add conda-bld directory
    docker_cmd += _add_volume(None, "/opt/conda/conda-bld")

    # Add env file directory
    for env_folder in env_folders:
        docker_cmd += _add_volume(env_folder, os.path.abspath(os.path.join(HOME_PATH, "envs", _mount_name(env_folder))))

    docker_cmd += image_name + " bash"
    if os.system(docker_cmd):
        raise OpenCEError(Error.CREATE_CONTAINER, container_name)

def _copy_to_container(src, dest, container_name):
    if os.system(DOCKER_TOOL + " cp " + src + " " + container_name + ":" + dest):
        raise OpenCEError(Error.COPY_DIR_TO_CONTAINER, src, container_name)

def _start_container(container_name):
    if os.system(DOCKER_TOOL + " start " + container_name):
        raise OpenCEError(Error.START_CONTAINER, container_name)

def _execute_in_container(container_name, command):
    docker_cmd = DOCKER_TOOL + " exec " + container_name + " "
    # Change to home directory
    docker_cmd += "bash -c 'cd " + HOME_PATH + "; " + command + "'"
    if os.system(docker_cmd):
        raise OpenCEError(Error.BUILD_IN_CONTAINER, container_name)

def _stop_container(container_name):
    result = os.system(DOCKER_TOOL + " stop " + container_name)
    return result

def build_in_container(image_name, args, arg_strings):
    """
    Run a build inside of a container using the provided image_name.
    """
    time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    container_name = IMAGE_NAME + "-" + time_stamp

    output_folder = os.path.abspath(args.output_folder)
    env_files = [os.path.abspath(env_file) for env_file in args.env_config_file]
    conda_build_config = os.path.abspath(args.conda_build_config)

    #use set comprehension to remove duplicates
    env_folders = {os.path.dirname(env_file) for env_file in env_files}
    env_files_in_container = {os.path.join(HOME_PATH,
                                           "envs",
                                           _mount_name(os.path.dirname(env_file)),
                                           os.path.basename(env_file))
                                    for env_file in env_files}
    arg_strings = list(env_files_in_container) + arg_strings

    _create_container(container_name, image_name, output_folder, env_folders)

    # Add the open-ce directory
    _copy_to_container(OPEN_CE_PATH, HOME_PATH, container_name)

    # Add the conda_build_config
    _copy_to_container(conda_build_config, HOME_PATH, container_name)
    config_in_container = os.path.join(HOME_PATH, os.path.basename(conda_build_config))
    arg_strings = arg_strings + ["--conda_build_config", config_in_container]

    # Add local_files directory (if it exists)
    if os.path.isdir(LOCAL_FILES_PATH):
        _copy_to_container(LOCAL_FILES_PATH, HOME_PATH, container_name)


    _start_container(container_name)

    # Execute build command
    cmd = "source $HOME/.bashrc; python {} {} {} {}".format(os.path.join(HOME_PATH, "open_ce", "open-ce"),
                                      args.command,
                                      args.sub_command,
                                      ' '.join(arg_strings[0:]))
    try:
        _execute_in_container(container_name, cmd)
    finally:
        # Cleanup
        _stop_container(container_name)

def _generate_dockerfile_name(build_types, cuda_version):
    '''
    Ensure we have valid combinations.  I.e. Specify a valid cuda version
    '''
    if 'cuda' in build_types:
        dockerfile = os.path.join(BUILD_CUDA_IMAGE_PATH, "Dockerfile.cuda-" + cuda_version)
        build_image_path = BUILD_CUDA_IMAGE_PATH
        if not os.path.isfile(dockerfile):
            raise OpenCEError(Error.UNSUPPORTED_CUDA, cuda_version)
    else:
        #Build with cpu based image
        dockerfile = os.path.join(BUILD_IMAGE_PATH, "Dockerfile")
        build_image_path = BUILD_IMAGE_PATH
    return build_image_path, dockerfile

def _capable_of_cuda_containers(cuda_versions):
    '''
    Check if we can run containers with Cuda installed.  This can be accomplished in two ways
    First if the host server does not have a driver installed
    Second, if the host driver is compatible with the level of cuda being used in the image
    '''

    return not utils.cuda_driver_installed() or utils.cuda_level_supported(cuda_versions)

def build_with_docker(args, arg_strings):
    """
    Create a build image and run a build inside of container based on that image.
    """
    parser = make_parser()
    _, unused_args = parser.parse_known_args(arg_strings[1:])

    build_image_path, dockerfile = _generate_dockerfile_name(args.build_types, args.cuda_versions)

    if  'cuda' not in args.build_types or _capable_of_cuda_containers(args.cuda_versions):
        image_name = build_image(build_image_path, dockerfile,
                                 args.cuda_versions if 'cuda' in args.build_types else None,
                                 args.docker_build_args)
    else:
        raise OpenCEError(Error.INCOMPAT_CUDA, utils.get_driver_level(), args.cuda_versions)

    build_in_container(image_name, args, unused_args)
