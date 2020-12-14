#!/usr/bin/env python

"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""

import utils
from inputs import Argument
from errors import OpenCEError, Error

utils.check_if_conda_build_exists()

import build_tree # pylint: disable=wrong-import-position

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

def validate_build_tree(build_commands, external_deps):
    '''
    Check a build tree for dependency compatability.
    '''
    packages = [package for recipe in build_commands for package in recipe.packages]
    channels = {channel for recipe in build_commands for channel in recipe.channels}
    deps = {dep for recipe in build_commands for dep in recipe.run_dependencies}
    deps.update(external_deps)

    pkg_args = " ".join(["\"{}\"".format(utils.generalize_version(dep)) for dep in deps
                                                                    if not utils.remove_version(dep) in packages])

    channel_args = " ".join({"-c \"{}\"".format(channel) for channel in channels})

    cli = "conda create --dry-run -n test_conda_dependencies {} {}".format(channel_args, pkg_args)

    ret_code, std_out, std_err = utils.run_command_capture(cli)
    if not ret_code:
        raise OpenCEError(Error.VALIDATE_BUILD_TREE, cli, std_out, std_err)

ENTRY_FUNCTION = validate_config
