"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""

import os
import argparse
import sys
import subprocess
from enum import Enum, unique
from itertools import product
import pkg_resources

DEFAULT_BUILD_TYPES = "cpu,cuda"
DEFAULT_PYTHON_VERS = "3.6"
DEFAULT_MPI_TYPES = "openmpi"
DEFAULT_CONDA_BUILD_CONFIG = os.path.join(os.path.dirname(__file__),
                                          "..", "conda_build_config.yaml")
DEFAULT_GIT_LOCATION = "https://github.com/open-ce"
SUPPORTED_GIT_PROTOCOLS = ["https:", "http:", "git@"]
DEFAULT_RECIPE_CONFIG_FILE = "config/build-config.yaml"

class OpenCEError(Exception):
    """
    Exception class for errors that occur in an Open-CE tool.
    """
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

class OpenCEFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """
    Default help text formatter class used within Open-CE.
    Allows the use of raw text argument descriptions by
    prepending 'R|' to the description text.
    """
    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
        return super()._split_lines(text, width)

@unique
class Argument(Enum):
    '''Enum for Arguments'''
    CONDA_BUILD_CONFIG = (lambda parser: parser.add_argument(
                                        '--conda_build_config',
                                        type=str,
                                        default=DEFAULT_CONDA_BUILD_CONFIG,
                                        help='Location of conda_build_config.yaml file.' ))

    OUTPUT_FOLDER = (lambda parser: parser.add_argument(
                                        '--output_folder',
                                        type=str,
                                        default='condabuild',
                                        help='Path where built conda packages will be saved.'))

    CHANNELS = (lambda parser: parser.add_argument(
                                        '--channels',
                                        dest='channels_list',
                                        action='append',
                                        type=str,
                                        default=list(),
                                        help='Conda channels to be used.'))

    ENV_FILE = (lambda parser: parser.add_argument(
                                        'env_config_file',
                                        nargs='+',
                                        type=str,
                                        help="Environment config file. This should be a YAML file "
                                             "describing the package environment you wish to build. A collection "
                                             "of files exist under the envs directory."))

    REPOSITORY_FOLDER = (lambda parser: parser.add_argument(
                                        '--repository_folder',
                                        type=str,
                                        default="",
                                        help="Directory that contains the repositories. If the "
                                            "repositories don't exist locally, they will be "
                                            "downloaded from OpenCE's git repository. If no value is provided, "
                                            "repositories will be downloaded to the current working directory."))

    PYTHON_VERSIONS = (lambda parser: parser.add_argument(
                                        '--python_versions',
                                        type=str,
                                        default=DEFAULT_PYTHON_VERS,
                                        help='Comma delimited list of python versions to build for '
                                             ', such as "3.6" or "3.7".'))

    BUILD_TYPES = (lambda parser: parser.add_argument(
                                        '--build_types',
                                        type=str,
                                        default=DEFAULT_BUILD_TYPES,
                                        help='Comma delimited list of build types, such as "cpu" or "cuda".'))

    MPI_TYPES = (lambda parser: parser.add_argument(
                                        '--mpi_types',
                                        type=str,
                                        default=DEFAULT_MPI_TYPES,
                                        help='Comma delimited list of mpi types, such as "openmpi" or "system".'))

    DOCKER_BUILD = (lambda parser: parser.add_argument(
                                        '--docker_build',
                                        action='store_true',
                                        help="Perform a build within a docker container. "
                                             "NOTE: When the --docker_build flag is used, all arguments with paths "
                                             "should be relative to the directory containing open-ce. Only files "
                                             "within the open-ce directory and local_files will be visible at "
                                             "build time."))

    USE_LOCAL_SCRATCH = (lambda parser: parser.add_argument(
                                        '--use_local_scratch',
                                        action='store_true',
                                        help="When performing a build within a container, use local scratch space "
                                             "instead of disk space within the container. This can be useful if the "
                                             "container has limited disk space. If `local_scratch_folder` is not "
                                             "set, scratch space will be taken from a temporary folder, which will "
                                             "be deleted after the job has completed."))

    LOCAL_SCRATCH_FOLDER = (lambda parser: parser.add_argument(
                                        '--local_scratch_folder',
                                        type=str,
                                        default=None,
                                        help='Local folder to use for scratch space when building within a container.'))

def make_parser(arguments, *args, formatter_class=OpenCEFormatter, **kwargs):
    '''
    Make a parser from a list of OPEN-CE Arguments.
    '''
    parser = argparse.ArgumentParser(*args, formatter_class=formatter_class, **kwargs)
    for argument in arguments:
        argument(parser)
    return parser

def parse_arg_list(arg_list):
    ''' Turn a comma delimited string into a python list'''
    if isinstance(arg_list, list):
        return arg_list
    return arg_list.split(",") if not arg_list is None else list()

def make_variants(python_versions=DEFAULT_PYTHON_VERS, build_types=DEFAULT_BUILD_TYPES, mpi_types=DEFAULT_MPI_TYPES):
    '''Create a cross product of possible variant combinations.'''
    variants = { 'python' : parse_arg_list(python_versions),
                 'build_type' : parse_arg_list(build_types),
                 'mpi_type' :  parse_arg_list(mpi_types)}
    return [dict(zip(variants,y)) for y in product(*variants.values())]

def remove_version(package):
    '''Remove conda version from dependency.'''
    return package.split()[0].split("=")[0]

def check_if_conda_build_exists():
    '''Checks if conda-build is installed and exits if it is not'''
    try:
        pkg_resources.get_distribution('conda-build')
    except pkg_resources.DistributionNotFound:
        print("Cannot find `conda_build`, please see https://github.com/open-ce/open-ce#requirements"
              " for a list of requirements.")
        sys.exit(1)

def make_schema_type(data_type,required=False):
    '''Make a schema type tuple.'''
    return (data_type, required)

def validate_type(value, schema_type):
    '''Validate a single type instance against a schema type.'''
    if isinstance(schema_type, dict):
        validate_dict_schema(value, schema_type)
    else:
        if not isinstance(value, schema_type):
            raise OpenCEError("{} is not of expected type {}".format(value, schema_type))

def validate_dict_schema(dictionary, schema):
    '''Recursively validate a dictionary's schema.'''
    for k, (schema_type, required) in schema.items():
        if k not in dictionary:
            if required:
                raise OpenCEError("Required key {} was not found in {}".format(k, dictionary))
            continue
        if isinstance(schema_type, list):
            if dictionary[k] is not None: #Handle if the yaml file has an empty list for this key.
                validate_type(dictionary[k], list)
                for value in dictionary[k]:
                    validate_type(value, schema_type[0])
        else:
            validate_type(dictionary[k], schema_type)
    for k in dictionary:
        if not k in schema:
            raise OpenCEError("Unexpected key {} was found in {}".format(k, dictionary))

def run_and_log(command):
    '''Print a shell command and then execute it.'''
    print("--->{}".format(command))
    return os.system(command)

def get_output(command):
    '''Print and execute a shell command and then return the output.'''
    print("--->{}".format(command))
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()
