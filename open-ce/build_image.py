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
import utils

OPEN_CE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RUNTIME_IMAGE_NAME = "runtime-cuda-" + platform.machine()
RUNTIME_IMAGE_PATH = os.path.join(OPEN_CE_PATH, "images", RUNTIME_IMAGE_NAME)
REPO_NAME = "open-ce"
IMAGE_NAME = "open-ce-runtime"

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
    build_cmd += "--build-arg BUILD_ID=" + str(os.getuid()) + " "
    build_cmd += "--build-arg GROUP_ID=" + str(os.getgid()) + " "
    build_cmd += "--build-arg CONDABUILD_DIR=" + condabuild_dir + " "
    build_cmd += "--build-arg CONDA_ENV_FILE=" + conda_env_file + " " 

    build_cmd += "."

    result = os.system(build_cmd)

    return result, image_name

def build_runtime_docker_image(args_string=None):
    """
    Create a runtime image which will have a conda environment created
    using locally build conda packages and environment file.
    """
    parser = make_parser()
    args = parser.parse_args(args_string)

    condabuild_dir = os.path.abspath(args.condabuild_dir)
    conda_env_file = os.path.abspath(args.conda_env_file)
   
    if not os.path.exists(condabuild_dir) or not os.path.exists(conda_env_file):
        print("Please provide correct paths for conda build directory and conda environment file")
    else:
        print("Inputs  given: ", condabuild_dir, conda_env_file)
        shutil.copy(conda_env_file, condabuild_dir)
        result, image_name = build_image(args.condabuild_dir, args.conda_env_file)

    if result:
        print("Failure building image: " + image_name)
        return result

    return result

if __name__ == '__main__':
    sys.exit(build_runtime_docker_image())

