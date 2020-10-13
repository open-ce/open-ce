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
import tempfile

OPEN_CE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BUILD_IMAGE_NAME = "builder-cuda-" + platform.machine()
BUILD_IMAGE_PATH = os.path.join(OPEN_CE_PATH, "images", BUILD_IMAGE_NAME)
LOCAL_FILES_PATH = os.path.join(os.path.join(os.getcwd(), "local_files"))
HOME_PATH = "/home/builder"

REPO_NAME = "open-ce"
IMAGE_NAME = "open-ce-builder"

DOCKER_TOOL = "docker"

def build_image():
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
    build_cmd += "."

    result = os.system(build_cmd)

    return result, image_name

def _add_volume(local_path, container_path):
    if not os.path.isdir(local_path):
        os.mkdir(local_path)
    volume_arg = "-v " + local_path + ":" + container_path + ":Z "

    return volume_arg

def _create_container(container_name, image_name, output_folder, scratch_dir):
    """
    Create a docker container
    """
    # Create the container
    docker_cmd = DOCKER_TOOL + " create -i --rm --name " + container_name + " "

    # Add output folder
    docker_cmd += _add_volume(os.path.join(os.getcwd(), output_folder), os.path.join(HOME_PATH, output_folder))

    # Add cache directory
    docker_cmd += _add_volume(os.path.join(scratch_dir, ".cache"), os.path.join(HOME_PATH, ".cache"))

    # Add conda-bld directory
    docker_cmd += _add_volume(os.path.join(scratch_dir, "conda-bld"), "/opt/conda/conda-bld")

    docker_cmd += image_name + " bash"
    result = os.system(docker_cmd)

    return result

def _copy_to_container(src, dest, container_name):
    result = os.system(DOCKER_TOOL + " cp " + src + " " + container_name + ":" + dest)
    return result

def _start_container(container_name):
    result = os.system(DOCKER_TOOL + " start " + container_name)
    return result

def _execute_in_container(container_name, command):
    docker_cmd = DOCKER_TOOL + " exec " + container_name + " "
    # Change to home directory
    docker_cmd += "bash -c 'cd " + HOME_PATH + "; " + command + "'"

    result = os.system(docker_cmd)
    return result

def _stop_container(container_name):
    result = os.system(DOCKER_TOOL + " stop " + container_name)
    return result

def build_in_container(image_name, output_folder, arg_strings):
    """
    Run a build inside of a container using the provided image_name.
    """
    time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    container_name = IMAGE_NAME + "-" + time_stamp

    scratch_dir = tempfile.mkdtemp()

    result = _create_container(container_name, image_name, output_folder, scratch_dir)
    if result:
        print("Error creating docker container: " + container_name)
        return result

    # Add the open-ce directory
    result = _copy_to_container(OPEN_CE_PATH, HOME_PATH, container_name)
    if result:
        print("Error copying open-ce directory into container")
        return 1

    # Add local_files directory (if it exists)
    if os.path.isdir(LOCAL_FILES_PATH):
        result = _copy_to_container(LOCAL_FILES_PATH, HOME_PATH, container_name)
        if result:
            print("Error copying local_files into container")
            return 1

    result = _start_container(container_name)
    if result:
        print("Error starting container " + container_name)
        return 1

    # Execute build command
    cmd = ("python " + os.path.join(HOME_PATH, "open-ce", "open-ce", os.path.basename(arg_strings[0])) + " " +
              ' '.join(arg_strings[1:]))
    result = _execute_in_container(container_name, cmd)

    _stop_container(container_name)
    shutil.rmtree(scratch_dir)

    if result:
        print("Error executing build in container")

    return result

def build_with_docker(output_folder, arg_strings):
    """
    Create a build image and run a build inside of container based on that image.
    """
    result, image_name = build_image()
    if result:
        print("Failure building image: " + image_name)
        return result

    if "--docker_build" in arg_strings:
        arg_strings.remove("--docker_build")

    result = build_in_container(image_name, output_folder, arg_strings)

    return result
