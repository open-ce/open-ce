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

DEFAULT_BUILD_TYPES = "cpu,cuda"
DEFAULT_PYTHON_VERS = "3.6"
DEFAULT_CONDA_BUILD_CONFIG = os.path.join(os.path.dirname(__file__),
                                          "..", "conda_build_config.yaml")

class OpenCEError(Exception):
    """
    Exception class for errors that occur in an Open-CE tool.
    """
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

class Argument: #pylint: disable=no-init,too-few-public-methods
    '''Enum for Arguments'''
    CONDA_BUILD_CONFIG = 0
    OUTPUT_FOLDER=1
    CHANNELS=2
    ENV_FILE=3
    REPOSITORY_FOLDER=4
    PYTHON_VERSIONS=5
    BUILD_TYPES=6

OPENCE_ARGS = {
    Argument.CONDA_BUILD_CONFIG:
    (lambda parser: parser.add_argument(
                            '--conda_build_config',
                            type=str,
                            default=DEFAULT_CONDA_BUILD_CONFIG,
                            help='Location of conda_build_config.yaml file.' )),
    Argument.OUTPUT_FOLDER:
    (lambda parser: parser.add_argument(
                            '--output_folder',
                            type=str,
                            default='condabuild',
                            help='Path where built conda packages will be saved.')),
    Argument.CHANNELS:
    (lambda parser: parser.add_argument(
                            '--channels',
                            dest='channels_list',
                            action='append',
                            type=str,
                            default=list(),
                            help='Conda channels to be used.')),
    Argument.ENV_FILE:
    (lambda parser: parser.add_argument(
                            'env_config_file',
                            nargs='+',
                            type=str,
                            help="Environment config file. This should be a YAML file"
                                 "describing the package environment you wish to build. A collection"
                                 "of files exist under the envs directory.")),
    Argument.REPOSITORY_FOLDER:
    (lambda parser: parser.add_argument(
                            '--repository_folder',
                            type=str,
                            default="",
                            help="Directory that contains the repositories. If the"
                                 "repositories don't exist locally, they will be"
                                 "downloaded from OpenCE's git repository. If no value is provided,"
                                 "repositories will be downloaded to the current working directory.")),
    Argument.PYTHON_VERSIONS:
    (lambda parser: parser.add_argument(
                            '--python_versions',
                            type=str,
                            default=DEFAULT_PYTHON_VERS,
                            help='Comma delimited list of python versions to build for, such as "3.6" or "3.7".')),
    Argument.BUILD_TYPES:
    (lambda parser: parser.add_argument(
                            '--build_types',
                            type=str,
                            default=DEFAULT_BUILD_TYPES,
                            help='Comma delimited list of build types, such as "cpu" or "cuda".'))
}

def make_parser(arguments, *args, **kwargs):
    '''
    Make a parser from a list of OPEN-CE Arguments.
    '''
    parser = argparse.ArgumentParser(*args, **kwargs)
    for argument in arguments:
        OPENCE_ARGS[argument](parser)
    return parser

def parse_arg_list(arg_list):
    ''' Turn a comma delimited string into a python list'''
    if isinstance(arg_list, list):
        return arg_list
    return arg_list.split(",") if not arg_list is None else list()

def remove_version(package):
    '''Remove conda version from dependency.'''
    return package.split()[0].split("=")[0]

def make_schema_type(data_type,required=False):
    return (data_type, required)

def validate_type(value, schema_type):
    if isinstance(schema_type, dict):
        validate_dict_schema(value, schema_type)
    else:
        if not isinstance(value, schema_type):
            raise OpenCEError("{} is not of expected type {}".format(value, schema_type))

def validate_dict_schema(dictionary, schema):
    for k, v in schema.items():
        required = v[1]
        schema_type = v[0]
        if k not in dictionary:
            if required:
                raise OpenCEError("Required key {} was not found in {}".format(k, dictionary))
            else:
                continue
        if isinstance(schema_type, list):
            for value in dictionary[k]:
                validate_type(value, schema_type[0])
        else:
            validate_type(dictionary[k], schema_type)
    for k, v in dictionary.items():
        if not k in schema:
            raise OpenCEError("Unexpected key {} was found in {}".format(k, dictionary))
