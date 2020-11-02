"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""

from enum import Enum, unique

@unique
class Error(Enum):
    '''Enum for Arguments'''
    ERROR = (0, "Unexpected Error: {}")
    CREATE_CONTAINER = (1, "Error creating docker container: \"{}\"")
    COPY_DIR_TO_CONTAINER = (2, "Error copying \"{}\" directory into container: \"{}\"")
    START_CONTAINER = (3, "Error starting docker container: \"{}\"")
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
    UNSUPPORTED_CUDA = (19, "Cannot build using docker image for cuda \"{}\" no Dockerfile currently exists")
    TOO_MANY_CUDA = (20, "Only one cuda version allowed to be built with docker at a time")

class OpenCEError(Exception):
    """
    Exception class for errors that occur in an Open-CE tool.
    """
    def __init__(self, error, *additional_args, **kwargs):
        msg = "[OPEN-CE-ERROR-{}] {}".format(error.value[0], error.value[1].format(*additional_args))
        super().__init__(msg, **kwargs)
        self.msg = msg
