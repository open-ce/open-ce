"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""

import argparse
from enum import Enum, unique
import utils

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
                                        default=utils.DEFAULT_CONDA_BUILD_CONFIG,
                                        help='Location of conda_build_config.yaml file.' ))

    OUTPUT_FOLDER = (lambda parser: parser.add_argument(
                                        '--output_folder',
                                        type=str,
                                        default=utils.DEFAULT_OUTPUT_FOLDER,
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
                                        default=utils.DEFAULT_PYTHON_VERS,
                                        help='Comma delimited list of python versions to build for '
                                             ', such as "3.6" or "3.7".'))

    BUILD_TYPES = (lambda parser: parser.add_argument(
                                        '--build_types',
                                        type=str,
                                        default=utils.DEFAULT_BUILD_TYPES,
                                        help='Comma delimited list of build types, such as "cpu" or "cuda".'))

    MPI_TYPES = (lambda parser: parser.add_argument(
                                        '--mpi_types',
                                        type=str,
                                        default=utils.DEFAULT_MPI_TYPES,
                                        help='Comma delimited list of mpi types, such as "openmpi" or "system".'))

    CUDA_VERSIONS = (lambda parser: parser.add_argument(
                                        '--cuda_versions',
                                        type=str,
                                        default=utils.DEFAULT_CUDA_VERS,
                                        help='CUDA version to build for '
                                             ', such as "10.2" or "11.0".'))

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
                                        default=utils.DEFAULT_OUTPUT_FOLDER,
                                        help='Path where built conda packages are present.'))

    TEST_WORKING_DIRECTORY = (lambda parser: parser.add_argument(
                                        '--test_working_dir',
                                        type=str,
                                        default="./",
                                        help="Directory where tests will be executed."))

    RECIPE_CONFIG_FILE = (lambda parser: parser.add_argument(
                                        '--recipe-config-file',
                                        type=str,
                                        default=None,
                                        help="""R|Path to the recipe configuration YAML file. The configuration
file lists paths to recipes to be built within a feedstock.

Below is an example stating that there are two recipes to build,
one named my_project and one named my_variant.

recipes:
  - name : my_project
    path : recipe

  - name : my_variant
    path: variants

If no path is given, the default value is build-config.yaml.
If build-config.yaml does not exist, and no value is provided,
it will be assumed there is a single recipe with the
path of \"recipe\"."""))

    RECIPES = (lambda parser: parser.add_argument(
                                        '--recipes',
                                        dest='recipe_list',
                                        action='store',
                                        default=None,
                                        help='Comma separated list of recipe names to build.'))

    WORKING_DIRECTORY = (lambda parser: parser.add_argument(
                                        '--working_directory',
                                        type=str,
                                        help='Directory to run the script in.'))

    LOCAL_SRC_DIR = (lambda parser: parser.add_argument(
                                        '--local_src_dir',
                                        type=str,
                                        required=False,
                                        help='Path where package source is downloaded in the form of RPM/Debians/Tar.'))

    GIT_LOCATION = (lambda parser: parser.add_argument(
                                        '--git_location',
                                        type=str,
                                        default=utils.DEFAULT_GIT_LOCATION,
                                        help='The default location to clone git repositories from.'))

    GIT_TAG_FOR_ENV = (lambda parser: parser.add_argument(
                                        '--git_tag_for_env',
                                        type=str,
                                        default=None,
                                        help='Git tag to be checked out for all of the packages in an environment.'))

    TEST_LABELS = (lambda parser: parser.add_argument(
                                        '--test_labels',
                                        type=str,
                                        default="",
                                        help="Comma delimited list of labels indicating what tests to run."))



def make_parser(arguments, *args, formatter_class=OpenCEFormatter, **kwargs):
    '''
    Make a parser from a list of OPEN-CE Arguments.
    '''
    parser = argparse.ArgumentParser(*args, formatter_class=formatter_class, **kwargs)
    for argument in arguments:
        argument(parser)
    return parser

def add_subparser(subparsers, command, arguments, *args, formatter_class=OpenCEFormatter, **kwargs):
    '''
    Make a parser from a list of OPEN-CE Arguments.
    '''
    subparser = subparsers.add_parser(command, *args, formatter_class=formatter_class, **kwargs)
    for argument in arguments:
        argument(subparser)
    return subparser

def parse_arg_list(arg_list):
    ''' Turn a comma delimited string into a python list'''
    if isinstance(arg_list, list):
        return arg_list
    return arg_list.split(",") if not arg_list is None else list()
