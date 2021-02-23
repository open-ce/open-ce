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

import open_ce.utils as utils
from open_ce.inputs import Argument
from open_ce.errors import OpenCEError, Error

import open_ce.build_tree as build_tree # pylint: disable=wrong-import-position

COMMAND = 'config'

DESCRIPTION = 'Perform validation on a conda_build_config.yaml file.'

ARGUMENTS = [Argument.CONDA_BUILD_CONFIG, Argument.ENV_FILE,
             Argument.REPOSITORY_FOLDER, Argument.PYTHON_VERSIONS,
             Argument.BUILD_TYPES, Argument.MPI_TYPES, Argument.CUDA_VERSIONS]

def validate_config(args):
    '''Entry Function'''
    variants = utils.make_variants(args.python_versions, args.build_types, args.mpi_types, args.cuda_versions)
    validate_env_config(args.conda_build_config, args.env_config_file, variants, args.repository_folder)

def validate_env_config(conda_build_config, env_config_files, variants, repository_folder):
    '''
    Validates a lits of Open-CE env files against a conda build config
    for a given set of variants.
    '''
    for variant in variants:
        for env_file in env_config_files:
            print('Validating {} for {} : {}'.format(conda_build_config, env_file, variant))
            try:
                _ = build_tree.BuildTree([env_file],
                                          variant['python'],
                                          variant['build_type'],
                                          variant['mpi_type'],
                                          variant['cudatoolkit'],
                                          repository_folder=repository_folder,
                                          conda_build_config=conda_build_config)
            except OpenCEError as err:
                raise OpenCEError(Error.VALIDATE_CONFIG, conda_build_config, env_file, variant, err.msg) from err
            print('Successfully validated {} for {} : {}'.format(conda_build_config, env_file, variant))

def validate_build_tree(build_commands, external_deps, package_indices=None):
    '''
    Check a build tree for dependency compatability.
    '''
    packages = [package for recipe in build_tree.traverse_build_commands(build_commands, package_indices)
                            for package in recipe.packages]
    channels = {channel for recipe in build_commands for channel in recipe.channels}
    deps = build_tree.get_installable_packages(build_commands, external_deps, package_indices)

    pkg_args = " ".join(["\"{}\"".format(utils.generalize_version(dep)) for dep in deps
                                                                    if not utils.remove_version(dep) in packages])
    channel_args = " ".join({"-c \"{}\"".format(channel) for channel in channels})

    cli = "conda create --dry-run -n test_conda_dependencies {} {}".format(channel_args, pkg_args)
    ret_code, std_out, std_err = utils.run_command_capture(cli)
    if not ret_code:
        raise OpenCEError(Error.VALIDATE_BUILD_TREE, cli, std_out, std_err)

ENTRY_FUNCTION = validate_config
