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

import sys
import os
import traceback
import yaml

import utils
import conda_build.api
from conda_build.config import get_or_merge_config

def make_parser():
    ''' Parser input arguments '''
    arguments = [utils.Argument.CONDA_BUILD_CONFIG, utils.Argument.OUTPUT_FOLDER,
                 utils.Argument.CHANNELS, utils.Argument.PYTHON_VERSIONS,
                 utils.Argument.BUILD_TYPES, utils.Argument.MPI_TYPES]
    parser = utils.make_parser(arguments,
                               description = 'Build conda packages as part of Open-CE')

    parser.add_argument(
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
path of \"recipe\".""")

    parser.add_argument(
        '--recipes',
        dest='recipe_list',
        action='store',
        default=None,
        help='Comma separated list of recipe names to build.')

    parser.add_argument(
        '--working_directory',
        type=str,
        help='Directory to run the script in.')

    parser.add_argument(
        '--local_src_dir',
        type=str,
        required=False,
        help='Path where package source is downloaded in the form of RPM/Debians/Tar.')

    return parser

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
            print("Unable to open provided config file: " + config_file)
            return None, config_file

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
            print("ERROR: local_src_dir path \"" + local_src_dir + "\" specified doesn't exist")
            return 1
        os.environ["LOCAL_SRC_DIR"] = local_src_dir
    else:
        if 'LOCAL_SRC_DIR' in os.environ:
            del os.environ['LOCAL_SRC_DIR']

    return 0

def build_feedstock(args_string=None):
    '''
    Entry function.
    '''
    parser = make_parser()
    args = parser.parse_args(args_string)

    saved_working_directory = None
    if args.working_directory:
        saved_working_directory = os.getcwd()
        os.chdir(os.path.abspath(args.working_directory))

    build_config_data, recipe_config_file  = load_package_config(args.recipe_config_file)
    if build_config_data is None:
        return 1

    args.recipes = utils.parse_arg_list(args.recipe_list)
    result = 0

    # Build each recipe
    for recipe in build_config_data['recipes']:
        if args.recipes and recipe['name'] not in args.recipes:
            continue

        config = get_or_merge_config(None)
        config.skip_existing = True
        config.output_folder = args.output_folder
        config.variant_config_files = [args.conda_build_config]

        recipe_conda_build_config = os.path.join(os.getcwd(), "config", "conda_build_config.yaml")
        if os.path.exists(recipe_conda_build_config):
            config.variant_config_files.append(recipe_conda_build_config)

        config.channel_urls = args.channels_list + build_config_data.get('channels', [])

        result = _set_local_src_dir(args.local_src_dir, recipe, recipe_config_file)
        if result != 0:
            break

        variants = dict()
        if args.python_versions:
            variants['python'] = utils.parse_arg_list(args.python_versions)
        if args.build_types:
            variants['build_type'] = utils.parse_arg_list(args.build_types)

        try:
            conda_build.api.build(os.path.join(os.getcwd(), recipe['path']),
                               config=config, variants=variants)
        except Exception: # pylint: disable=broad-except
            traceback.print_exc()
            print("Failure building recipe: " + (recipe['name'] if 'name' in recipe else os.getcwd))
            result = 1

    if saved_working_directory:
        os.chdir(saved_working_directory)

    return result

if __name__ == '__main__':
    utils.check_if_conda_build_exists()
    sys.exit(build_feedstock())
