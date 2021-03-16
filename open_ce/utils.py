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

import os
import sys
import subprocess
import errno
from itertools import product
import re
import urllib.request
import tempfile
import pkg_resources
from open_ce.errors import OpenCEError, Error
from open_ce import inputs


DEFAULT_BUILD_TYPES = "cpu,cuda"
DEFAULT_PYTHON_VERS = "3.7"
DEFAULT_MPI_TYPES = "openmpi"
DEFAULT_CUDA_VERS = "10.2"
CONDA_BUILD_CONFIG_FILE = "conda_build_config.yaml"
DEFAULT_CONDA_BUILD_CONFIG = os.path.abspath(os.path.join(os.getcwd(), CONDA_BUILD_CONFIG_FILE))
DEFAULT_GIT_LOCATION = "https://github.com/open-ce"
SUPPORTED_GIT_PROTOCOLS = ["https:", "http:", "git@"]
DEFAULT_RECIPE_CONFIG_FILE = "config/build-config.yaml"
CONDA_ENV_FILENAME_PREFIX = "opence-conda-env-"
DEFAULT_OUTPUT_FOLDER = "condabuild"
DEFAULT_TEST_CONFIG_FILE = "tests/open-ce-tests.yaml"
DEFAULT_GIT_TAG = None
OPEN_CE_VARIANT = "open-ce-variant"
DEFAULT_TEST_WORKING_DIRECTORY = "./"
KNOWN_VARIANT_PACKAGES = ["python", "cudatoolkit"]
DEFAULT_LICENSES_FILE = "licenses.csv"
TMP_LICENSE_DIR = "tmp_license_src"
OPEN_CE_INFO_FILE = "open-ce-info.yaml"
DEFAULT_CONTAINER_TOOL = "docker"

def make_variants(python_versions=DEFAULT_PYTHON_VERS, build_types=DEFAULT_BUILD_TYPES, mpi_types=DEFAULT_MPI_TYPES,
cuda_versions=DEFAULT_CUDA_VERS):
    '''Create a cross product of possible variant combinations.'''
    variants = { 'python' : inputs.parse_arg_list(python_versions),
                 'build_type' : inputs.parse_arg_list(build_types),
                 'mpi_type' :  inputs.parse_arg_list(mpi_types),
                 'cudatoolkit' : inputs.parse_arg_list(cuda_versions)}
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
    if cwd and not os.path.exists(cwd):
        os.mkdir(cwd)
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

def variant_string_to_dict(var_string):
    """
    Returns a dictionary of variants based on the versions within the variant string.
    """
    variants = var_string.split("-")
    variant_dict = { 'python' : variants[0][2:],
                     'build_type' : variants[1],
                     'mpi_type' : variants[2],
                     'cudatoolkit' : variants[3] }

    return variant_dict

def generalize_version(package):
    """Add `.*` to package versions when it is needed."""

    # Remove multiple spaces or tabs
    package = re.sub(r'\s+', ' ', package)

    # Check if we want to add .* to the end of versions
    py_matched = re.match(r'([\w-]+)([\s=<>]*)(\d[.\d*\w*]*)([=\s]*.*)', package)

    if py_matched:
        name = py_matched.group(1)
        operator = py_matched.group(2)
        version = py_matched.group(3)
        build = py_matched.group(4)
        if len(version) > 0 and len(operator) > 0:

            #Append .* at the end if it is not there and if operator is space or == or empty
            if not version.endswith(".*") and version[-1].isdigit() and operator.strip() in ["==", " ", ""]:
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

def check_cuda_version_match(command):
    '''
    Check whether cudatoolkit matches the system CUDA version (as per CUDA_HOME).
    If not, print a warning.  Returns True/False based on match.
    '''

    # Version is recorded in $CUDA_HOME/version.txt; make sure $CUDA_HOME is set first.
    # (If $CUDA_HOME doesn't exist, read will fail so we return False).
    check_cuda_home()
    cudavers_file = os.environ['CUDA_HOME'] + '/version.txt'
    try:
        cudafile = open(cudavers_file,'r')
        cuda_home_version = cudafile.readline()
        version_match = cuda_home_version.find(str(command.cudatoolkit))
        cudafile.close()
        if version_match > 0:
            return True
    except cudavers_file:
        # Treating as a warning rather than a fatal error
        print("WARNING: Could not read version from " + cudavers_file)

    # Versions do not match.  Return False.
    return False

def check_cuda_home():
    '''
    Ensure CUDA_HOME is set.
    If unset, then set to default of /usr/local/cuda
    '''

    if 'CUDA_HOME' not in os.environ:
        # CUDA_HOME is not set, so set it to the default location
        os.environ['CUDA_HOME'] = "/usr/local/cuda"

def is_subdir(child_path, parent_path):
    """ Checks if given child path is sub-directory of parent_path. """

    child = os.path.realpath(child_path)
    parent = os.path.realpath(parent_path)

    relative = os.path.relpath(child, start=parent)
    return not relative.startswith(os.pardir)

def is_url(to_check):
    '''
    Determines if a string is a URL
    '''
    return to_check.startswith("http:") or to_check.startswith("https:")

def download_file(url, filename=None):
    '''
    Downloads a file from a url string.
    Raises an OpenCE Error if an exception is encountered.
    '''
    retval = None
    try:
        if not filename:
            download_path = tempfile.NamedTemporaryFile(suffix=os.path.basename(url), delete=False).name
        else:
            download_path = tempfile.NamedTemporaryFile(suffix=filename, delete=False).name
        retval, _ = urllib.request.urlretrieve(url, filename=download_path)
    except Exception as exc: # pylint: disable=broad-except
        raise OpenCEError(Error.FILE_DOWNLOAD, url, str(exc)) from exc
    return retval

def replace_conda_env_channels(conda_env_file, original_channel, new_channel):
    '''
    Use regex to substitute channels in a conda env file.
    Regex 'original_channel' is replaced with 'new_channel'
    '''
    #pylint: disable=import-outside-toplevel
    import yaml

    with open(conda_env_file, 'r') as file_handle:
        env_info = yaml.safe_load(file_handle)

    env_info['channels'] = [re.sub(original_channel, new_channel, channel) for channel in env_info['channels']]

    with open(conda_env_file, 'w') as file_handle:
        yaml.safe_dump(env_info, file_handle)

def git_clone(git_url, git_tag, location):
    '''
    Clone a git repository and checkout a certain branch.
    '''
    clone_cmd = "git clone " + git_url + " " + location
    print("Clone cmd: ", clone_cmd)
    clone_result = os.system(clone_cmd)

    cur_dir = os.getcwd()
    clone_successful = clone_result == 0
    if clone_successful:
        if not git_tag is None:
            os.chdir(location)
            checkout_cmd = "git checkout " + git_tag
            print("Checkout branch/tag command: ", checkout_cmd)
            checkout_res = os.system(checkout_cmd)
            os.chdir(cur_dir)
            clone_successful = checkout_res == 0
    else:
        raise OpenCEError(Error.CLONE_REPO, git_url)

    return clone_successful
