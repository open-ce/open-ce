#!/usr/bin/env python
"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************

*******************************************************************************
Script: build_env.py

Summary:
  Build a conda package environment (e.g. tensorflow, pytorch, etc.) from
open-ce project repositories.

Description:
  This script will take an YAML build env file for any defined general project
package and dependencies and will build that project automatically, including
the  dependencies. It will execute the build_feedstock.py script as needed in
order to produce conda packages for the requested project.

In the simplest case, a build for (e.g.) tensorflow may look like this:
   $ ./open-ce/build_env.py envs/tensorflow-env.yaml
(or similar, adjusting for your path or to choose a different project).

Usage:
   $ build_env.py [ arguments ] env_config_file [env_config_file ...]
For usage description of arguments, this script supports use of --help:
   $ build_env.py --help

*******************************************************************************
"""

import argparse
import os
import sys

import build_feedstock
import docker_build
import utils
from utils import OpenCEError
from conda_env_file_generator import CondaEnvFileGenerator

def make_parser():
    ''' Parser for input arguments '''
    arguments = [utils.Argument.CONDA_BUILD_CONFIG, utils.Argument.OUTPUT_FOLDER,
                 utils.Argument.CHANNELS, utils.Argument.ENV_FILE,
                 utils.Argument.REPOSITORY_FOLDER, utils.Argument.PYTHON_VERSIONS,
                 utils.Argument.BUILD_TYPES]
    parser = utils.make_parser(arguments,
                               description = 'Build conda environment as part of Open-CE',
                               formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        '--git_location',
        type=str,
        default=utils.DEFAULT_GIT_LOCATION,
        help='The default location to clone git repositories from.')

    parser.add_argument(
        '--git_tag_for_env',
        type=str,
        default=None,
        help='Git tag to be checked out for all of the packages in an environment.')

    parser.add_argument(
        '--docker_build',
        action='store_true',
        help="""Perform a build within a docker container.
NOTE: When the --docker_build flag is used, all arguments with paths should be relative to the
directory containing open-ce. Only files within the open-ce directory and local_files will
be visible at build time.""")

    return parser

def build_env(arg_strings=None):
    '''
    Entry function.
    '''
    parser = make_parser()
    args = parser.parse_args(arg_strings)

    if args.docker_build:
        return docker_build.build_with_docker(args.output_folder, sys.argv)

    # Checking conda-build existence if --docker_build is not specified
    utils.check_if_conda_build_exists()

    # Here, importing BuildTree is intentionally done after checking
    # existence of conda-build as BuildTree uses conda_build APIs.
    from build_tree import BuildTree  # pylint: disable=import-outside-toplevel

    result = 0

    common_package_build_args = []
    common_package_build_args += ["--output_folder", os.path.abspath(args.output_folder)]
    common_package_build_args += ["--channel", os.path.abspath(args.output_folder)]
    common_package_build_args += ["--conda_build_config", os.path.abspath(args.conda_build_config)]

    for channel in args.channels_list:
        common_package_build_args += ["--channels", channel]

    # If repository_folder doesn't exist, create it
    if args.repository_folder and not os.path.exists(args.repository_folder):
        os.mkdir(args.repository_folder)

    try:
        build_tree = BuildTree(env_config_files=args.env_config_file,
                               python_versions=utils.parse_arg_list(args.python_versions),
                               build_types=utils.parse_arg_list(args.build_types),
                               repository_folder=args.repository_folder,
                               git_location=args.git_location,
                               git_tag_for_env=args.git_tag_for_env,
                               conda_build_config=args.conda_build_config)
    except OpenCEError as err:
        print(err.msg)
        return 1

    conda_env_data = CondaEnvFileGenerator(
                               python_versions=utils.parse_arg_list(args.python_versions),
                               build_types=utils.parse_arg_list(args.build_types),
                               channels=args.channels_list,
                               output_folder=os.path.abspath(args.output_folder),
                               )

    # Build each package in the packages list
    for build_command in build_tree:
        build_args = common_package_build_args + build_command.feedstock_args()
        result = build_feedstock.build_feedstock(build_args)

        if result != 0:
            print("Unable to build recipe: " +  build_command.repository)
            return result

        conda_env_data.update_conda_env_file_content(build_command, build_tree)

    conda_env_files = conda_env_data.write_conda_env_files()
    print("Following conda environment files are generated", conda_env_files)

    return result

if __name__ == '__main__':
    sys.exit(build_env())
