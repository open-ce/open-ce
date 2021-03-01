#!/usr/bin/env python
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
import glob

import build_feedstock
import container_build
import utils
import inputs
from inputs import Argument
import test_feedstock
from errors import OpenCEError, Error

COMMAND = "env"

DESCRIPTION = 'Build conda environment as part of Open-CE'

ARGUMENTS = [Argument.CONDA_BUILD_CONFIG,
             Argument.OUTPUT_FOLDER,
             Argument.CHANNELS,
             Argument.ENV_FILE,
             Argument.PACKAGES,
             Argument.REPOSITORY_FOLDER,
             Argument.PYTHON_VERSIONS,
             Argument.BUILD_TYPES,
             Argument.MPI_TYPES,
             Argument.CUDA_VERSIONS,
             Argument.SKIP_BUILD_PACKAGES,
             Argument.RUN_TESTS,
             Argument.CONTAINER_BUILD,
             Argument.GIT_LOCATION,
             Argument.GIT_TAG_FOR_ENV,
             Argument.TEST_LABELS,
             Argument.CONTAINER_BUILD_ARGS,
             Argument.CONTAINER_TOOL]

def _run_tests(build_tree, test_labels, conda_env_files):
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
        test_feedstocks = build_tree.get_test_feedstocks(variant_string)
        if test_feedstocks:
            print("\n*** Running tests within the " + os.path.basename(conda_env_file) + " conda environment ***\n")
        for feedstock in test_feedstocks:
            print("Running tests for " + feedstock)
            failed_tests += test_feedstock.test_feedstock(conda_env_file,
                                                          test_labels=test_labels,
                                                          working_directory=feedstock)

    test_feedstock.display_failed_tests(failed_tests)
    if failed_tests:
        raise OpenCEError(Error.FAILED_TESTS, len(failed_tests))

def _all_outputs_exist(output_folder, output_files):
    return all([os.path.exists(os.path.join(os.path.abspath(output_folder), package))
                    for package in output_files])

def build_env(args):
    '''Entry Function'''

    if args.container_build:
        if len(args.cuda_versions.split(',')) > 1:
            raise OpenCEError(Error.TOO_MANY_CUDA)
        try:
            container_build.build_with_container_tool(args, sys.argv)
        finally:
            for conda_env_file in glob.glob(os.path.join(args.output_folder, "*.yaml")):
                utils.replace_conda_env_channels(conda_env_file,
                                                 os.path.abspath(os.path.join(container_build.HOME_PATH,
                                                                              utils.DEFAULT_OUTPUT_FOLDER)),
                                                 os.path.abspath(args.output_folder))
        return

    # Checking conda-build existence if --container_build is not specified
    utils.check_if_conda_build_exists()

    # Here, importing BuildTree is intentionally done after checking
    # existence of conda-build as BuildTree uses conda_build APIs.
    from build_tree import BuildTree  # pylint: disable=import-outside-toplevel

    # If repository_folder doesn't exist, create it
    if args.repository_folder and not os.path.exists(args.repository_folder):
        os.mkdir(args.repository_folder)

    # Create the build tree
    build_tree = BuildTree(env_config_files=args.env_config_file,
                               python_versions=inputs.parse_arg_list(args.python_versions),
                               build_types=inputs.parse_arg_list(args.build_types),
                               mpi_types=inputs.parse_arg_list(args.mpi_types),
                               cuda_versions=inputs.parse_arg_list(args.cuda_versions),
                               repository_folder=args.repository_folder,
                               channels=args.channels_list,
                               git_location=args.git_location,
                               git_tag_for_env=args.git_tag_for_env,
                               conda_build_config=args.conda_build_config,
                               packages=inputs.parse_arg_list(args.packages))

    # Generate conda environment files
    conda_env_files = build_tree.write_conda_env_files(output_folder=os.path.abspath(args.output_folder),
                                                       path=os.path.abspath(args.output_folder))
    print("Generated conda environment files from the selected build arguments:", conda_env_files.values())
    print("INFO: One can use these environment files to create a conda" \
          " environment using \"conda env create -f <conda_env_file_name>.\"")

    if not args.skip_build_packages:
        # Build each package in the packages list
        for build_command in build_tree:
            if not _all_outputs_exist(args.output_folder, build_command.output_files):
                try:
                    print("Building " + build_command.recipe)
                    build_feedstock.build_feedstock_from_command(build_command,
                                                            output_folder=os.path.abspath(args.output_folder),
                                                            conda_build_config=os.path.abspath(args.conda_build_config))
                except OpenCEError as exc:
                    raise OpenCEError(Error.BUILD_RECIPE, build_command.repository, exc.msg) from exc
            else:
                print("Skipping build of " + build_command.recipe + " because it already exists")

    if args.run_tests:
        _run_tests(build_tree, inputs.parse_arg_list(args.test_labels), conda_env_files)

ENTRY_FUNCTION = build_env
