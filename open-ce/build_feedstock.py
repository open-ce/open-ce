#!/usr/bin/env python
"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************

*******************************************************************************
Script: build_feedstock.py

Summary:
  Build conda package(s) from open-ce project feedstock repositories.

Description:
  This script will build any given Open-CE package from within the desired
package feedstock.  It can be executed implicitly as part of Open-CE builds
executed by build-env.py, or it can be run directly for a selected feedstock.
It will build a conda package for the chosen feedstock using the default
recipe(s) found within that package's build tree, or with an alternative
recipe specified on the command line.

Usage:
   $ build_feedstock.py [ arguments ]
For usage description of arguments, this script supports use of --help:
   $ build_feedstock.py --help

*******************************************************************************
"""

import os
import traceback
import yaml

import utils
from errors import OpenCEError, Error
from build_tree import BuildCommand
utils.check_if_conda_build_exists()

# pylint: disable=wrong-import-position
import conda_build.api
from conda_build.config import get_or_merge_config
# pylint: enable=wrong-import-position

COMMAND = 'build_feedstock'

DESCRIPTION = 'Build conda packages as part of Open-CE'

ARGUMENTS = [utils.Argument.CONDA_BUILD_CONFIG, utils.Argument.OUTPUT_FOLDER,
             utils.Argument.CHANNELS, utils.Argument.PYTHON_VERSIONS,
             utils.Argument.BUILD_TYPES, utils.Argument.MPI_TYPES,
             utils.Argument.CUDA_VERSIONS,
             (lambda parser: parser.add_argument(
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
path of \"recipe\".""")),
             (lambda parser: parser.add_argument(
                    '--recipes',
                    dest='recipe_list',
                    action='store',
                    default=None,
                    help='Comma separated list of recipe names to build.')),
             (lambda parser: parser.add_argument(
                    '--working_directory',
                    type=str,
                    help='Directory to run the script in.')),
             (lambda parser: parser.add_argument(
                    '--local_src_dir',
                    type=str,
                    required=False,
                    help='Path where package source is downloaded in the form of RPM/Debians/Tar.'))]

def get_conda_build_config():
    '''
    Checks for a conda_build_config file inside config dir of the feedstock.
    And returns the same if it exists.
    '''
    recipe_conda_build_config = os.path.join(os.getcwd(), "config", "conda_build_config.yaml")
    return recipe_conda_build_config if os.path.exists(recipe_conda_build_config) else None

def load_package_config(config_file=None):
    '''
    Check for a config file. If the user does not provide a recipe config
    file as an argument, it will be assumed that there is only one
    recipe to build, and it is in the directory called 'recipe'.
    '''
    if not config_file and not os.path.exists(utils.DEFAULT_RECIPE_CONFIG_FILE):
        recipe_name = os.path.basename(os.getcwd())
        build_config_data = {'recipes':[{'name':recipe_name, 'path':'recipe'}]}
    else:
        if not config_file:
            config_file = utils.DEFAULT_RECIPE_CONFIG_FILE
        if not os.path.exists(config_file):
            raise OpenCEError(Error.CONFIG_FILE, config_file)

        with open(config_file, 'r') as stream:
            build_config_data = yaml.safe_load(stream)

    return build_config_data, config_file

def _set_local_src_dir(local_src_dir_arg, recipe, recipe_config_file):
    """
    Set the LOCAL_SRC_DIR environment variable if local_src_dir is specified.
    """
    # Local source directory provided as command line argument has higher priority
    # than what is specified in build-config.yaml
    if local_src_dir_arg:
        local_src_dir = os.path.expanduser(local_src_dir_arg)
    elif 'local_src_dir' in recipe:
        local_src_dir = os.path.expanduser(recipe.get('local_src_dir'))
        # If a relative path is specified, it should be in relation to the config file
        if not os.path.isabs(local_src_dir):
            local_src_dir = os.path.join(os.path.dirname(os.path.abspath(recipe_config_file)),
                                         local_src_dir)
    else:
        local_src_dir = None

    if local_src_dir:
        if not os.path.exists(local_src_dir):
            raise OpenCEError(Error.LOCAL_SRC_DIR, local_src_dir)
        os.environ["LOCAL_SRC_DIR"] = local_src_dir
    else:
        if 'LOCAL_SRC_DIR' in os.environ:
            del os.environ['LOCAL_SRC_DIR']

def build_feedstock_from_command(command, # pylint: disable=too-many-arguments
                                 recipe_config_file=None,
                                 output_folder=utils.DEFAULT_OUTPUT_FOLDER,
                                 extra_channels=None,
                                 conda_build_config=utils.DEFAULT_CONDA_BUILD_CONFIG,
                                 local_src_dir=None):
    '''
    Build a feedstock from a build_command object.
    '''
    if not extra_channels:
        extra_channels = []
    saved_working_directory = None
    if command.repository:
        saved_working_directory = os.getcwd()
        os.chdir(os.path.abspath(command.repository))

    build_config_data, recipe_config_file  = load_package_config(recipe_config_file)

    recipes_to_build = utils.parse_arg_list(command.recipe)

    # Build each recipe
    for recipe in build_config_data['recipes']:
        if recipes_to_build and recipe['name'] not in recipes_to_build:
            continue

        config = get_or_merge_config(None)
        config.skip_existing = True
        config.output_folder = output_folder
        config.variant_config_files = [conda_build_config]

        recipe_conda_build_config = os.path.join(os.getcwd(), "config", "conda_build_config.yaml")
        if os.path.exists(recipe_conda_build_config):
            config.variant_config_files.append(recipe_conda_build_config)

        config.channel_urls = command.channels + extra_channels + build_config_data.get('channels', [])

        _set_local_src_dir(local_src_dir, recipe, recipe_config_file)

        try:
            for variant in utils.make_variants(command.python, command.build_type, command.mpi_type, command.cudatoolkit):
                conda_build.api.build(os.path.join(os.getcwd(), recipe['path']),
                               config=config, variants=variant)
        except Exception as exc: # pylint: disable=broad-except
            traceback.print_exc()
            raise OpenCEError(Error.BUILD_RECIPE,
                              recipe['name'] if 'name' in recipe else os.getcwd,
                              str(exc)) from exc

    if saved_working_directory:
        os.chdir(saved_working_directory)

def build_feedstock(args):
    '''Entry Function'''
    command = BuildCommand(recipe=utils.parse_arg_list(args.recipe_list),
                           repository=args.working_directory,
                           packages=[],
                           python=args.python_versions,
                           build_type=args.build_types,
                           mpi_type=args.mpi_types,
                           cudatoolkit=args.cuda_versions,
                           channels=args.channels_list)

    build_feedstock_from_command(command,
                                 recipe_config_file=args.recipe_config_file,
                                 output_folder=args.output_folder,
                                 local_src_dir=args.local_src_dir)
