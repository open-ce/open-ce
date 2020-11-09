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
import errno
from enum import Enum, unique
from itertools import product
import re
import yaml
import pkg_resources
from errors import OpenCEError, Error


DEFAULT_BUILD_TYPES = "cpu,cuda"
DEFAULT_PYTHON_VERS = "3.6"
DEFAULT_MPI_TYPES = "openmpi"
DEFAULT_CUDA_VERS = "10.2"
DEFAULT_CONDA_BUILD_CONFIG = os.path.join(os.path.dirname(__file__),
                                          "..", "conda_build_config.yaml")
DEFAULT_GIT_LOCATION = "https://github.com/open-ce"
SUPPORTED_GIT_PROTOCOLS = ["https:", "http:", "git@"]
DEFAULT_RECIPE_CONFIG_FILE = "config/build-config.yaml"
CONDA_ENV_FILENAME_PREFIX = "opence-conda-env-"
DEFAULT_OUTPUT_FOLDER = "condabuild"
DEFAULT_TEST_CONFIG_FILE = "tests/open-ce-tests.yaml"

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
                                        default=DEFAULT_OUTPUT_FOLDER,
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

    CUDA_VERSIONS = (lambda parser: parser.add_argument(
                                        '--cuda_versions',
                                        type=str,
                                        default=DEFAULT_CUDA_VERS,
                                        #Supress description of cuda_versions flag until more robust testing
                                        help=argparse.SUPPRESS))
                                        #help='Comma delimited list of cuda versions to build for '
                                        #     ', such as "10.2" or "11.0".'))

    DOCKER_BUILD = (lambda parser: parser.add_argument(
                                        '--docker_build',
                                        action='store_true',
                                        help="Perform a build within a docker container. "
                                             "NOTE: When the --docker_build flag is used, all arguments with paths "
                                             "should be relative to the directory containing open-ce. Only files "
                                             "within the open-ce directory and local_files will be visible at "
                                             "build time."))

    SKIP_BUILD_PACKAGES = (lambda parser: parser.add_argument(
                                        '--skip_build_packages',
                                        action='store_true',
                                        help="Do not perform builds of packages."))

    RUN_TESTS = (lambda parser: parser.add_argument(
                                        '--run_tests',
                                        action='store_true',
                                        help="Run Open-CE tests for each potential conda environment"))

    CONDA_ENV_FILE = (lambda parser: parser.add_argument(
                                        '--conda_env_file',
                                        type=str,
                                        help='Location of conda environment file.' ))

    LOCAL_CONDA_CHANNEL = (lambda parser: parser.add_argument(
                                        '--local_conda_channel',
                                        type=str,
                                        default=DEFAULT_OUTPUT_FOLDER,
                                        help='Path where built conda packages are present.'))

    TEST_WORKING_DIRECTORY = (lambda parser: parser.add_argument(
                                        '--test_working_dir',
                                        type=str,
                                        default="./",
                                        help="Directory where tests will be executed."))


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

def make_variants(python_versions=DEFAULT_PYTHON_VERS, build_types=DEFAULT_BUILD_TYPES, mpi_types=DEFAULT_MPI_TYPES,
cuda_versions=DEFAULT_CUDA_VERS):
    '''Create a cross product of possible variant combinations.'''
    variants = { 'python' : parse_arg_list(python_versions),
                 'build_type' : parse_arg_list(build_types),
                 'mpi_type' :  parse_arg_list(mpi_types),
                 'cudatoolkit' : parse_arg_list(cuda_versions)}
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
            raise OpenCEError(Error.ERROR, "{} is not of expected type {}".format(value, schema_type))

def validate_dict_schema(dictionary, schema):
    '''Recursively validate a dictionary's schema.'''
    for k, (schema_type, required) in schema.items():
        if k not in dictionary:
            if required:
                raise OpenCEError(Error.ERROR, "Required key {} was not found in {}".format(k, dictionary))
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
            raise OpenCEError(Error.ERROR, "Unexpected key {} was found in {}".format(k, dictionary))

def run_command_capture(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=None):
    """Run a shell command and capture the ret_code, stdout and stderr."""
    process = subprocess.Popen(
        cmd,
        stdout=stdout,
        stderr=stderr,
        shell=True,
        universal_newlines=True,
        cwd=cwd)
    std_out, std_err = process.communicate()

    return process.returncode == 0, std_out, std_err

def run_and_log(command):
    '''Print a shell command and then execute it.'''
    print("--->{}".format(command))
    return os.system(command)

def get_output(command):
    '''Print and execute a shell command and then return the output.'''
    print("--->{}".format(command))
    _,std_out,_ = run_command_capture(command, stderr=subprocess.STDOUT)
    return std_out.strip()

def variant_string(py_ver, build_type, mpi_type, cudatoolkit):
    '''
    Returns a variant key using python version and build type
    '''
    result = ""
    if py_ver:
        result +=  "py" + py_ver
    if build_type:
        result +=  "-" + build_type
    if mpi_type:
        result +=  "-" + mpi_type
    if cudatoolkit:
        result += "-" + cudatoolkit
    return result

def generalize_version(package):
    """Add `.*` to package versions when it is needed."""

    # Remove multiple spaces or tabs
    package = re.sub(r'\s+', ' ', package)

    # Check if we want to add .* to the end of versions
    py_matched = re.match(r'([\w-]+)([\s=<>]*)(\d[.\d*]*)(.*)', package)

    if py_matched:
        name = py_matched.group(1)
        operator = py_matched.group(2)
        version = py_matched.group(3)
        build = py_matched.group(4)
        if len(version) > 0 and len(operator) > 0:

            #Append .* at the end if it is not there and if operator is space or == or empty
            if not version.endswith(".*") and operator.strip() in ["==", " ", ""]:
                package = name + operator + version + ".*" + build

    return package

def cuda_level_supported(cuda_level):
    '''
    Check if the requested cuda level is supported by loaded NVIDIA driver
    '''

    return float(get_driver_cuda_level()) >= float(cuda_level)

def get_driver_cuda_level():
    '''
    Return what level of Cuda the driver can support
    '''
    try:
        smi_out = subprocess.check_output("nvidia-smi").decode("utf-8").strip()
        return re.search(r"CUDA Version\: (\d+\.\d+)", smi_out).group(1)
    except OSError as err:
        if err.errno == errno.ENOENT:
            raise OpenCEError(Error.ERROR, "nvidia-smi command not found") from err

        raise OpenCEError(Error.ERROR, "nvidia-smi command unexpectedly failed") from err

def get_driver_level():
    '''
    Return the NVIDIA driver level on the system.
    '''
    try:
        smi_out = subprocess.check_output("nvidia-smi").decode("utf-8").strip()
        return re.search(r"Driver Version\: (\d+\.\d+\.\d+)", smi_out).group(1)
    except OSError as err:
        if err.errno == errno.ENOENT:
            raise OpenCEError(Error.ERROR, "nvidia-smi command not found") from err

        raise OpenCEError(Error.ERROR, "nvidia-smi command unexpectedly failed") from err

def cuda_driver_installed():
    '''
    Determine if the current machine has the NVIDIA driver installed
    '''

    try:
        lsmod_out = subprocess.check_output("lsmod").decode("utf-8").strip()
        return re.search(r"nvidia ", lsmod_out) is not None
    except OSError as err:
        if err.errno == errno.ENOENT:
            raise OpenCEError(Error.ERROR, "lsmod command not found") from err

        raise OpenCEError(Error.ERROR, "lsmod command unexpectedly failed") from err

def is_subdir(child_path, parent_path):
    """ Checks if given child path is sub-directory of parent_path. """

    child = os.path.realpath(child_path)
    parent = os.path.realpath(parent_path)

    relative = os.path.relpath(child, start=parent)
    return not relative.startswith(os.pardir)

def replace_conda_env_channels(conda_env_file, original_channel, new_channel):
    '''
    Use regex to substitute channels in a conda env file.
    Regex 'original_channel' is replaced with 'new_channel'
    '''
    with open(conda_env_file, 'r') as file_handle:
        env_info = yaml.safe_load(file_handle)

    env_info['channels'] = [re.sub(original_channel, new_channel, channel) for channel in env_info['channels']]

    with open(conda_env_file, 'w') as file_handle:
        yaml.safe_dump(env_info, file_handle)
