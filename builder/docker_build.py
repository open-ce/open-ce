"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""
import os

OPEN_CE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BUILD_IMAGE_PATH = os.path.join(OPEN_CE_PATH, "images/builder")
LOCAL_FILES_PATH = os.path.join(os.path.dirname(OPEN_CE_PATH), "local_files")
HOME_PATH = "/home/builder"

REPO_NAME = "open-ce"

def build_image():
    """
    Build a docker image from the Dockerfile in BUILD_IMAGE_PATH.
    Returns a result code and the name of the new image.
    """
    image_name = REPO_NAME + ":open-ce-builder-" + str(os.getuid())
    build_cmd = "docker build "
    build_cmd += "-f " + os.path.join(BUILD_IMAGE_PATH, "Dockerfile") + " "
    build_cmd += "-t " + image_name + " "
    build_cmd += "--build-arg BUILD_ID=" + str(os.getuid()) + " "
    build_cmd += "--build-arg GROUP_ID=" + str(os.getgid()) + " "
    build_cmd += "."

    result = os.system(build_cmd)

    return result, image_name

def build_in_container(image_name, output_folder, arg_strings):
    """
    Run a build inside of a container using the provided image_name.
    """
    docker_cmd = "docker run --rm "

    # Add output folder
    local_output_folder = os.path.join(os.getcwd(), output_folder)
    if not os.path.isdir(local_output_folder):
        os.mkdir(local_output_folder)
    docker_cmd += "-v " + local_output_folder + ":" + os.path.join(HOME_PATH, output_folder) + ":rw "

    # Add open-ce directory
    docker_cmd += "-v " + OPEN_CE_PATH + ":" + HOME_PATH + "/open-ce:ro "

    # Add local_files directory (if it exists)
    if os.path.isdir(os.path.join(os.getcwd(), "local_files")):
        docker_cmd += "-v " + os.getcwd() + "/local_files:" + HOME_PATH + "/local_files:ro "

    docker_cmd += image_name + " "
    docker_cmd += "bash -c 'cd " + HOME_PATH + "; " + ' '.join(arg_strings)  + "'"

    result = os.system(docker_cmd)

    return result

def build_with_docker(output_folder, arg_strings):
    """
    Create a build image and run a build inside of container based on that image.
    """
    result, image_name = build_image()
    arg_strings.remove("--docker_build")
    result = build_in_container(image_name, output_folder, arg_strings)

    return result
