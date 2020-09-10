#!/usr/bin/env python
"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""
"""
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
import yaml
import argparse

from util import parse_arg_list

default_recipe_config_file = "config/build-config.yaml"
default_conda_build_config = "../open-ce/conda_build_config.yaml"

def make_parser():
    ''' Parser input arguments '''
    parser = argparse.ArgumentParser(
        description = 'Build conda packages as part of Open-CE',
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        '--recipe-config-file',
        type=str,
        default=None,
        help="""Path to the recipe configuration YAML file. The configuration
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
        '--output_folder',
        type=str,
        default='condabuild',
        help='Path where built conda packages will be saved.')

    parser.add_argument(
        '--recipes',
        dest='recipe_list',
        action='store',
        default=None,
        help='Comma separated list of recipe names to build.')

    parser.add_argument(
        '--conda_build_config',
        type=str,
        default=default_conda_build_config,
        help='Location of conda_build_config.yaml file.')

    parser.add_argument(
        '--python_versions',
        dest='python_versions_list',
        action='store',
        type=str,
        default=None,
        help='Comma delimited list of python versions to build for, such as "3.6" or 3.7".')

    parser.add_argument(
        '--build_types',
        dest='build_types_list',
        action='store',
        type=str,
        default=None,
        help='Comma delimited list of build types, such as "cpu" or "cuda".')

    parser.add_argument(
        '--working_directory',
        type=str,
        help='Directory to run the script in.')

    parser.add_argument(
        '--channels',
        dest='channels_list',
        action='append',
        type=str,
        default=list(),
        help='Conda channel to be used.')

    parser.add_argument(
        '--local_src_dir',
        type=str,
        required=False,
        help='Path where package source is downloaded in the form of RPM/Debians/Tar.')

    return parser

def load_package_config(config_file=None):
    # Check for a config file. If the user does not provide a recipe config
    # file as an argument, it will be assumed that there is only one
    # recipe to build, and it is in the directory called 'recipe'.
    if not config_file and not os.path.exists(default_recipe_config_file):
        recipe_name = os.path.basename(os.getcwd())
        build_config_data = {'recipes':[{'name':recipe_name, 'path':'recipe'}]}
    else:
        if not config_file:
            config_file = default_recipe_config_file
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
    # Local source directory provided as command line arguement has higher priority
    # than what is specified in build-config.yaml
    if local_src_dir_arg:
        local_src_dir = os.path.expanduser(local_src_dir_arg)
    elif 'local_src_dir' in recipe:
        local_src_dir = os.path.expanduser(recipe.get('local_src_dir'))
        # If a relative path is specified, it should be in relation to the config file
        if not os.path.isabs(local_src_dir):
            local_src_dir = os.path.join(os.path.dirname(os.path.abspath(recipe_config_file)), local_src_dir)
    else:
        local_src_dir = None

    if local_src_dir:
       if not os.path.exists(local_src_dir):
           print("ERROR: local_src_dir path \"" + local_src_dir + "\" specified doesn't exist")
           return 1
       else:
           os.environ["LOCAL_SRC_DIR"] = local_src_dir
    else:
        if 'LOCAL_SRC_DIR' in os.environ:
            del os.environ['LOCAL_SRC_DIR']

    return 0

def build_feedstock(args_string=None):
    parser = make_parser()
    args = parser.parse_args(args_string)

    saved_working_directory = None
    if args.working_directory:
        saved_working_directory = os.getcwd()
        os.chdir(os.path.abspath(args.working_directory))

    build_config_data, recipe_config_file  = load_package_config(args.recipe_config_file)
    if build_config_data is None:
        return 1

    args.recipes = parse_arg_list(args.recipe_list)
    result = 0

    # Build each recipe
    for recipe in build_config_data['recipes']:
        if args.recipes and recipe['name'] not in args.recipes:
            continue
        conda_build_args = "conda-build "
        conda_build_args += "--skip-existing "
        conda_build_args += "--output-folder " + args.output_folder + " "
        conda_build_args += "-m " + args.conda_build_config + " "
        recipe_conda_build_config = os.path.join(os.getcwd(), "config", "conda_build_config.yaml")
        if os.path.exists(recipe_conda_build_config):
            conda_build_args += " -m " + recipe_conda_build_config + " "

        for channel in args.channels_list:
            conda_build_args += "-c " + channel + " "

        for channel in build_config_data.get('channels', []):
            conda_build_args += "-c " + channel + " "

        variants = dict()
        if args.python_versions_list:
            variants['python'] = parse_arg_list(args.python_versions_list)
        if args.build_types_list:
            variants['build_type'] = parse_arg_list(args.build_types_list)
        if variants:
            conda_build_args += "--variants \"" + str(variants) + "\" "

        conda_build_args += recipe['path']

        result = _set_local_src_dir(args.local_src_dir, recipe, recipe_config_file)
        if result != 0:
            break

        print(conda_build_args)
        result = os.system(conda_build_args)
        if result != 0:
            print("Failure building recipe: " + (recipe['name'] if 'name' in recipe else os.getcwd))
            result = 1
            break

    if saved_working_directory:
        os.chdir(saved_working_directory)

    return result

if __name__ == '__main__':
    sys.exit(build_feedstock())

