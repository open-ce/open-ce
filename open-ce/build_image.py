#!/usr/bin/env python
"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""
import os
import sys
import datetime
import platform
import shutil
import yaml
import utils

OPEN_CE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RUNTIME_IMAGE_NAME = "runtime-cuda-" + platform.machine()
RUNTIME_IMAGE_PATH = os.path.join(OPEN_CE_PATH, "images", RUNTIME_IMAGE_NAME)
REPO_NAME = "open-ce"
IMAGE_NAME = "open-ce-runtime"
BUILD_CONTEXT = "."

TARGET_DIR="opence-local-conda-channel"

DOCKER_TOOL = "docker"

def make_parser():
    ''' Parser for input arguments '''
    arguments = [utils.Argument.CONDABUILD_DIR, utils.Argument.CONDA_ENV_FILE]
    parser = utils.make_parser(arguments, description='Run Open-CE tools within a container')

    return parser

def build_image(condabuild_dir, conda_env_file):
    """
    Build a docker image from the Dockerfile in RUNTIME_IMAGE_PATH.
    Returns a result code and the name of the new image.
    """
    image_name = REPO_NAME + ":" + IMAGE_NAME + "-" + str(os.getuid())
    build_cmd = DOCKER_TOOL + " build "
    build_cmd += "-f " + os.path.join(RUNTIME_IMAGE_PATH, "Dockerfile") + " "
    build_cmd += "-t " + image_name + " "
    build_cmd += "--build-arg USER_ID=" + str(os.getuid()) + " "
    build_cmd += "--build-arg GROUP_ID=" + str(os.getgid()) + " "
    build_cmd += "--build-arg CONDABUILD_DIR=" + condabuild_dir + " "
    build_cmd += "--build-arg CONDA_ENV_FILE=" + conda_env_file + " " 
    build_cmd += "--build-arg TARGET_DIR=" + TARGET_DIR + " "
    build_cmd += BUILD_CONTEXT

    print("Docker build command: ", build_cmd)
    result = os.system(build_cmd)

    return result, image_name

def _is_subdir(child_path, parent_path):
    child = os.path.realpath(child_path)
    parent = os.path.realpath(parent_path)

    relative = os.path.relpath(child, start=parent)

    return not relative.startswith(os.pardir)

def _update_channels(conda_env_file):
    with open(conda_env_file, 'r') as f:
        env_info = yaml.safe_load(f)

    channels = env_info['channels']
    for channel in channels:
        if channel.startswith("file:"):
            index = channels.index(channel)
            channels.remove(channel)
            channels.insert(index,"file://home/opence/" + TARGET_DIR)
            break
    env_info['channels'] = channels

    with open(conda_env_file, 'w') as f:
        yaml.safe_dump(env_info, f)

def are_input_paths_valid(condabuild_dir, conda_env_file):
    ret_val = False
    condabuild_dir = os.path.abspath(condabuild_dir)
    conda_env_file = os.path.abspath(conda_env_file)
    if not os.path.exists(condabuild_dir) or not os.path.exists(conda_env_file):
        print("Please provide correct paths for conda build directory and conda environment file")
    elif not _is_subdir(condabuild_dir, os.path.abspath(BUILD_CONTEXT)):
        print("Specified condabuild directory is not in the current directory. \n" +
              "Either move the condabuild directory in the current directory or run" +
              "the script from the path which contains condabuild directory")
    else:
        print("Inputs  given: ", condabuild_dir, conda_env_file)
        shutil.copy(conda_env_file, condabuild_dir)
        ret_val = True

    return ret_val
 
def build_runtime_docker_image(args_string=None):
    """
    Create a runtime image which will have a conda environment created
    using locally build conda packages and environment file.
    """
    parser = make_parser()
    args = parser.parse_args(args_string)

    if are_input_paths_valid(args.condabuild_dir, args.conda_env_file):
        conda_env_file = os.path.join(os.path.abspath(args.condabuild_dir), os.path.basename(args.conda_env_file))
        _update_channels(conda_env_file)
        result, image_name = build_image(args.condabuild_dir, os.path.basename(args.conda_env_file))

    if result:
        print("Failure building image: " + image_name)
        return result

    return result

if __name__ == '__main__':
    sys.exit(build_runtime_docker_image())

