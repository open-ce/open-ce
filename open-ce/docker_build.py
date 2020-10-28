"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""
import os
import datetime
import platform

import utils
from errors import OpenCEError, Error

OPEN_CE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BUILD_IMAGE_NAME = "builder-cuda-" + platform.machine()
BUILD_IMAGE_PATH = os.path.join(OPEN_CE_PATH, "images", BUILD_IMAGE_NAME)
LOCAL_FILES_PATH = os.path.join(os.path.join(os.getcwd(), "local_files"))
HOME_PATH = "/home/builder"

REPO_NAME = "open-ce"
IMAGE_NAME = "open-ce-builder"

DOCKER_TOOL = "docker"

def make_parser():
    ''' Parser for input arguments '''
    arguments = [utils.Argument.DOCKER_BUILD]
    parser = utils.make_parser(arguments, description='Run Open-CE tools within a container')

    return parser

def _build_image():
    """
    Build a docker image from the Dockerfile in BUILD_IMAGE_PATH.
    Returns a result code and the name of the new image.
    """
    image_name = REPO_NAME + ":" + IMAGE_NAME + "-" + str(os.getuid())
    build_cmd = DOCKER_TOOL + " build "
    build_cmd += "-f " + os.path.join(BUILD_IMAGE_PATH, "Dockerfile") + " "
    build_cmd += "-t " + image_name + " "
    build_cmd += "--build-arg BUILD_ID=" + str(os.getuid()) + " "
    build_cmd += "--build-arg GROUP_ID=" + str(os.getgid()) + " "
    build_cmd += BUILD_IMAGE_PATH

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

def _create_container(container_name, image_name, output_folder):
    """
    Create a docker container
    """
    # Create the container
    docker_cmd = DOCKER_TOOL + " create -i --rm --name " + container_name + " "

    # Add output folder
    docker_cmd += _add_volume(os.path.join(os.getcwd(), output_folder), os.path.join(HOME_PATH, output_folder))

    # Add cache directory
    docker_cmd += _add_volume(None, os.path.join(HOME_PATH, ".cache"))

    # Add conda-bld directory
    docker_cmd += _add_volume(None, "/opt/conda/conda-bld")

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

def build_in_container(image_name, output_folder, arg_strings):
    """
    Run a build inside of a container using the provided image_name.
    """
    time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    container_name = IMAGE_NAME + "-" + time_stamp

    _create_container(container_name, image_name, output_folder)

    # Add the open-ce directory
    _copy_to_container(OPEN_CE_PATH, HOME_PATH, container_name)

    # Add local_files directory (if it exists)
    if os.path.isdir(LOCAL_FILES_PATH):
        _copy_to_container(LOCAL_FILES_PATH, HOME_PATH, container_name)

    _start_container(container_name)

    # Execute build command
    cmd = ("python " + os.path.join(HOME_PATH, "open-ce", "open-ce", os.path.basename(arg_strings[0])) + " " +
              ' '.join(arg_strings[1:]))
    _execute_in_container(container_name, cmd)

    # Cleanup
    _stop_container(container_name)

def build_with_docker(output_folder, arg_strings):
    """
    Create a build image and run a build inside of container based on that image.
    """
    parser = make_parser()
    _, unused_args = parser.parse_known_args(arg_strings)

    image_name = _build_image()

    build_in_container(image_name, output_folder, unused_args)
