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
import pkg_resources
import re

DEFAULT_BUILD_TYPES = "cpu,cuda"
DEFAULT_PYTHON_VERS = "3.6"
DEFAULT_CONDA_BUILD_CONFIG = os.path.join(os.path.dirname(__file__),
                                          "..", "conda_build_config.yaml")
DEFAULT_GIT_LOCATION = "https://github.com/open-ce"
SUPPORTED_GIT_PROTOCOLS = ["https:", "http:", "git@"]
DEFAULT_RECIPE_CONFIG_FILE = "config/build-config.yaml"
CONDA_ENV_FILENAME_PREFIX = "opence-conda-env-"

class OpenCEError(Exception):
    """
    Exception class for errors that occur in an Open-CE tool.
    """
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

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
                                        help="Environment config file. This should be a YAML file"
                                            "describing the package environment you wish to build. A collection"
                                            "of files exist under the envs directory."))

    REPOSITORY_FOLDER = (lambda parser: parser.add_argument(
                                        '--repository_folder',
                                        type=str,
                                        default="",
                                        help="Directory that contains the repositories. If the"
                                            "repositories don't exist locally, they will be"
                                            "downloaded from OpenCE's git repository. If no value is provided,"
                                            "repositories will be downloaded to the current working directory."))

    PYTHON_VERSIONS = (lambda parser: parser.add_argument(
                                        '--python_versions',
                                        type=str,
                                        default=DEFAULT_PYTHON_VERS,
                                        help='Comma delimited list of python versions to build for'
                                              ', such as "3.6" or "3.7".'))

    BUILD_TYPES = (lambda parser: parser.add_argument(
                                        '--build_types',
                                        type=str,
                                        default=DEFAULT_BUILD_TYPES,
                                        help='Comma delimited list of build types, such as "cpu" or "cuda".'))

def make_parser(arguments, *args, **kwargs):
    '''
    Make a parser from a list of OPEN-CE Arguments.
    '''
    parser = argparse.ArgumentParser(*args, **kwargs)
    for argument in arguments:
        argument(parser)
    return parser

def parse_arg_list(arg_list):
    ''' Turn a comma delimited string into a python list'''
    if isinstance(arg_list, list):
        return arg_list
    return arg_list.split(",") if not arg_list is None else list()

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

def variant_key(py_ver, build_type):
    '''
    Returns a variant key using python version and build type
    '''
    result = ""
    if py_ver:
        result +=  "py" + py_ver
    if build_type:
        result +=  "-" + build_type
    return result

def generalize_version(package):
    """Add `.*` to package versions when it is needed."""

    # Remove multiple spaces or tabs
    package = re.sub(' +', ' ', package)

    # Check if we want to add .* to the end of versions
    py_matched = re.match(r'(\w+[-]*\w+)([\s,=,<,>]*)(.*)', package)

    if py_matched:
        name = py_matched.group(1)
        operator = py_matched.group(2)
        version = py_matched.group(3)
        append_asterik = False

        if len(version) > 0 and len(operator) > 0:

            #Append .* at the end if it is not there and if operator is space or == or = or empty
            if not version.endswith(".*") and operator.strip() in ["=", "==", " ", ""]:
                package = name + operator + version + ".*"

    print(package)
    return package

