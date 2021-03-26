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

from enum import Enum, unique

@unique
class Error(Enum):
    '''Enum for Arguments'''
    ERROR = (0, "Unexpected Error: {}")
    CREATE_CONTAINER = (1, "Error creating container: \"{}\"")
    COPY_DIR_TO_CONTAINER = (2, "Error copying \"{}\" directory into container: \"{}\"")
    START_CONTAINER = (3, "Error starting container: \"{}\"")
    BUILD_IN_CONTAINER = (4, "Error executing build in container: \"{}\"")
    BUILD_IMAGE = (5, "Failure building image: \"{}\"")
    VALIDATE_ENV = (6, "Error validating \"{}\" for variant {}\n{}")
    VALIDATE_CONFIG = (7, "Error validating \"{}\" for \"{}\" in variant \"{}\"\n{}")
    CONFIG_CONTENT = (8, "Content Error!:\n"
                         "An environment file needs to specify packages or "
                         "import another environment file.")
    CLONE_REPO = (9, "Unable to clone repository: {}")
    CREATE_BUILD_TREE = (10, "Error creating Build Tree\n{}")
    BUILD_RECIPE = (11, "Unable to build recipe: {}\n{}")
    CONFIG_FILE = (12, "Unable to open provided config file: {}")
    LOCAL_SRC_DIR = (13, "local_src_dir path \"{}\" specified doesn't exist")
    BUILD_TREE_CYCLE = (14, "Build dependencies should form a Directed Acyclic Graph.\n"
                            "The following dependency cycles were detected in the build tree:\n{}")
    INCORRECT_INPUT_PATHS = (15, "Input paths specified don't exist")
    LOCAL_CHANNEL_NOT_IN_CONTEXT = (16, "Specified local conda channel directory is not" +
              " in the current build context. \n Either move the local conda channel" +
              " directory in the current directory or run the script from the path" +
              " which contains local conda channel directory.")
    VALIDATE_BUILD_TREE = (17, "Dependencies are not compatible.\nCommand:\n{}\nOutput:\n{}\nError:\n{}")
    INCOMPAT_CUDA = (18, "Driver level \"{}\" is not new enough to support cuda \"{}\"")
    UNSUPPORTED_CUDA = (19, "Cannot build using container image for cuda \"{}\" no Dockerfile currently exists")
    TOO_MANY_CUDA = (20, "Only one cuda version allowed to be built with container build at a time")
    FAILED_TESTS = (21, "There were {} test failures")
    CONDA_ENV_FILE_REQUIRED = (22, "The '--conda_env_file' argument is required.")
    PATCH_APPLICATION = (23, "Failed to apply patch {} on feedstock {}")
    GET_LICENSES = (24, "Error generating licenses file.\nCommand:\n{}\nOUTPUT:\n{}Error:\n{}")
    FILE_DOWNLOAD = (25, "Failed to download {} with error:\n{}")
    CONDA_BUILD_CONFIG_FILE_NOT_FOUND = (26, "Failed to locate conda_build_config.yaml.")
    NO_CONTAINER_TOOL_FOUND = (27, "No container tool found on the system.")
    CONDA_PACKAGE_INFO = (28, "Conda Package Info Failed.\nCommand:\n{}\nOutput:\n{}")
    REMOTE_PACKAGE_DEPENDENCIES = (29, "Failure getting remote dependencies for the following packages:\n{}\nError:\n{}")

class OpenCEError(Exception):
    """
    Exception class for errors that occur in an Open-CE tool.
    """
    def __init__(self, error, *additional_args, **kwargs):
        msg = "[OPEN-CE-ERROR-{}] {}".format(error.value[0], error.value[1].format(*additional_args))
        super().__init__(msg, **kwargs)
        self.msg = msg
