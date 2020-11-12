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

import os
import sys
import glob

import build_feedstock
import docker_build
import utils
import validate_config
import test_feedstock
from errors import OpenCEError, Error

COMMAND = "build_env"

DESCRIPTION = 'Build conda environment as part of Open-CE'

ARGUMENTS = [utils.Argument.CONDA_BUILD_CONFIG, utils.Argument.OUTPUT_FOLDER,
             utils.Argument.CHANNELS, utils.Argument.ENV_FILE,
             utils.Argument.REPOSITORY_FOLDER, utils.Argument.PYTHON_VERSIONS,
             utils.Argument.BUILD_TYPES, utils.Argument.MPI_TYPES,
             utils.Argument.CUDA_VERSIONS, utils.Argument.SKIP_BUILD_PACKAGES,
             utils.Argument.RUN_TESTS, utils.Argument.DOCKER_BUILD,
             (lambda parser: parser.add_argument(
                    '--git_location',
                    type=str,
                    default=utils.DEFAULT_GIT_LOCATION,
                    help='The default location to clone git repositories from.')),
             (lambda parser: parser.add_argument(
                    '--git_tag_for_env',
                    type=str,
                    default=None,
                    help='Git tag to be checked out for all of the packages in an environment.'))]

def _run_tests(build_tree, conda_env_files):
    """
    Run through all of the tests within a build tree for the given conda environment files.

    Args:
        build_tree (BuildTree): The build tree containing the tests
        conda_env_files (dict): A dictionary where the key is a variant string and the value
                                is the name of a conda environment file.
    """
    failed_tests = []
    # Run test commands for each conda environment that was generated
    for variant_string, conda_env_file in conda_env_files.items():
        test_commands = build_tree.get_test_commands(variant_string)
        if test_commands:
            print("\n*** Running tests within the " + os.path.basename(conda_env_file) + " conda environment ***\n")
        for feedstock, feedstock_test_commands in test_commands.items():
            print("Running tests for " + feedstock)
            failed_tests += test_feedstock.run_test_commands(conda_env_file, feedstock_test_commands)

    test_feedstock.display_failed_tests(failed_tests)
    if failed_tests:
        raise OpenCEError(Error.FAILED_TESTS, len(failed_tests))

def build_env(args):
    '''Entry Function'''
    if args.docker_build:
        if len(args.cuda_versions.split(',')) > 1:
            raise OpenCEError(Error.TOO_MANY_CUDA)
        docker_build.build_with_docker(os.path.abspath(args.output_folder), args.build_types, args.cuda_versions, sys.argv)
        for conda_env_file in glob.glob(os.path.join(args.output_folder, "*.yaml")):
            utils.replace_conda_env_channels(conda_env_file,
                                             os.path.abspath(os.path.join(docker_build.HOME_PATH,
                                                                          utils.DEFAULT_OUTPUT_FOLDER)),
                                             os.path.abspath(args.output_folder))
        return

    # Checking conda-build existence if --docker_build is not specified
    utils.check_if_conda_build_exists()

    # Here, importing BuildTree is intentionally done after checking
    # existence of conda-build as BuildTree uses conda_build APIs.
    from build_tree import BuildTree  # pylint: disable=import-outside-toplevel

    # If repository_folder doesn't exist, create it
    if args.repository_folder and not os.path.exists(args.repository_folder):
        os.mkdir(args.repository_folder)

    variants = utils.make_variants(args.python_versions, args.build_types, args.mpi_types)
    validate_config.validate_env_config(args.conda_build_config, args.env_config_file, variants, args.repository_folder)

    # Create the build tree
    build_tree = BuildTree(env_config_files=args.env_config_file,
                               python_versions=utils.parse_arg_list(args.python_versions),
                               build_types=utils.parse_arg_list(args.build_types),
                               mpi_types=utils.parse_arg_list(args.mpi_types),
                               cuda_versions=utils.parse_arg_list(args.cuda_versions),
                               repository_folder=args.repository_folder,
                               git_location=args.git_location,
                               git_tag_for_env=args.git_tag_for_env,
                               conda_build_config=args.conda_build_config)

    # Generate conda environment files
    conda_env_files = build_tree.write_conda_env_files(channels=args.channels_list,
                                                       output_folder=os.path.abspath(args.output_folder),
                                                       path=os.path.abspath(args.output_folder))
    print("Generated conda environment files from the selected build arguments:", conda_env_files.values())
    print("INFO: One can use these environment files to create a conda" \
          " environment using \"conda env create -f <conda_env_file_name>.\"")

    if not args.skip_build_packages:
        # Build each package in the packages list
        for build_command in build_tree:
            try:
                build_feedstock.build_feedstock_from_command(build_command,
                                                            output_folder=os.path.abspath(args.output_folder),
                                                            extra_channels=[os.path.abspath(args.output_folder)] +
                                                                           args.channels_list,
                                                            conda_build_config=os.path.abspath(args.conda_build_config))
            except OpenCEError as exc:
                raise OpenCEError(Error.BUILD_RECIPE, build_command.repository, exc.msg) from exc

    if args.run_tests:
        _run_tests(build_tree, conda_env_files)
