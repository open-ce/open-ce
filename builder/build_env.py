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
   $ ./builder/build_env.py envs/tensorflow-env.yaml
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
import yaml

import conda_build.metadata
import conda_build.api
from conda_build.config import get_or_merge_config

import build_feedstock
from util import parse_arg_list

default_conda_build_config = os.path.join(os.path.dirname(__file__), "..", "conda_build_config.yaml")
default_build_types = "cpu,cuda"
default_python_vers = "3.6"
default_git_location = "https://github.com/open-ce"

def make_parser():
    ''' Parser input arguments '''
    parser = argparse.ArgumentParser(
        description = 'Build conda environment as part of Open-CE',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        'env_config_file',
        nargs='+',
        type=str,
        help="""Environment config file. This should be a YAML file
describing the package environment you wish to build. A collection
of files exist under the envs directory.""")

    parser.add_argument(
        '--repository_folder',
        type=str,
        default="",
        help="""Directory that contains the repositories. If the
repositories don't exist locally, they will be
downloaded from OpenCE's git repository. If no value is provided,
repositories will be downloaded to the current working directory.""")

    parser.add_argument(
        '--output_folder',
        type=str,
        default='condabuild',
        help='Path where built conda packages will be saved.')

    parser.add_argument(
        '--conda_build_config',
        type=str,
        default=default_conda_build_config,
        help='Location of conda_build_config.yaml file.')

    parser.add_argument(
        '--python_versions',
        type=str,
        default=default_python_vers,
        help='Comma delimited list of python versions to build for, such as "3.6" or "3.7".')

    parser.add_argument(
        '--build_types',
        type=str,
        default=default_build_types,
        help='Comma delimited list of build types, such as "cpu" or "cuda".')

    parser.add_argument(
        '--git_location',
        type=str,
        default=default_git_location,
        help='The default location to clone git repositories from.')

    parser.add_argument(
        '--git_tag_for_env',
        type=str,
        default=None,
        help='Git tag to be checked out for all of the packages in an environment.')

    parser.add_argument(
        '--channels',
        dest='channels_list',
        action='append',
        type=str,
        default=list(),
        help='Extra conda channel to be used.')

    return parser

def make_hash(d):
    return hash(str(d))

def load_env_config_files(config_files, variants):
    # Load all of the environment config files, plus any that come from "imported_envs" within an environment config file.
    env_config_files = [os.path.abspath(e) for e in config_files]
    env_config_data_list = []
    loaded_files = []
    while env_config_files:
        # Load the environment config files using conda-build's API. This will allow for the
        # filtering of text using selectors and jinja2 functions
        meta_obj = conda_build.metadata.MetaData(env_config_files[0], variant=variants)
        env = meta_obj.get_rendered_recipe_text()

        # Examine all of the imported_envs items and determine if they still need to be loaded.
        new_config_files = []
        for imported_env in env.get('imported_envs', []):
            imported_env = os.path.expanduser(imported_env)
            if not os.path.isabs(imported_env):
                imported_env = os.path.join(os.path.dirname(env_config_files[0]), imported_env)
            if not imported_env in env_config_files and not imported_env in loaded_files:
                new_config_files += [imported_env]

        # If there are new files to load, add them to the env_conf_files list.
        # Otherwise, remove the current file from the env_conf_files list and add its data to the env_config_data_list.
        if new_config_files:
            env_config_files = new_config_files + env_config_files
        else:
            env_config_data_list += [env]
            loaded_files += [env_config_files[0]]
            env_config_files.pop(0)

    return env_config_data_list

def _clone_repo(git_location, repo_dir, env_config_data, git_tag_from_config, git_tag_for_env):
    """
    Clone the git repo at repository.
    """
    git_url = git_location + "/" + os.path.basename(repo_dir) + ".git"
    # Priority is given to command line specified tag, if it is not
    # specified then package specific tag, and when even that is not specified
    # then top level git tag specified for env in the env file. And if nothing is
    # at all specified then fall back to default branch of the repo.

    git_tag = git_tag_for_env
    if git_tag is None:
        if git_tag_from_config:
            git_tag = git_tag_from_config
        else:
            git_tag = env_config_data.get('git_tag_for_env', None)

    if git_tag is None:
        clone_cmd = "git clone " + git_url + " " + repo_dir
    else:
        clone_cmd = "git clone -b " + git_tag + " --single-branch " + git_url + " " + repo_dir

    print("Clone cmd: ", clone_cmd)
    clone_result = os.system(clone_cmd)
    if clone_result != 0:
        print("Unable to clone repository: " + git_url + " " + str(clone_result))
        return 1

    return 0

def _get_package_dependencies(path, variant_config_files, variants):
    """
    Return a list of output packages and a list of dependency packages
    for the recipe at a given path. Uses conda-render to determine this information.
    """
    def remove_versions(lst):
        return [x.split()[0] for x in lst]

    # Call conda-build's render tool to get a list of dictionaries representing
    # the recipe for each variant that will be built.
    config = get_or_merge_config(None)
    config.variant_config_files = variant_config_files
    config.verbose = False
    metas = conda_build.api.render(path, config=config, variants=variants, bypass_env_check=True, finalize=False)

    # Parse out the package names and dependencies from each variant
    packages = set()
    deps = set()
    for meta,_,_ in metas:
        packages.add(meta.meta['package']['name'])
        deps.update(remove_versions(meta.meta['requirements'].get('run', [])))
        deps.update(remove_versions(meta.meta['requirements'].get('host', [])))
        deps.update(remove_versions(meta.meta['requirements'].get('build', [])))
        if 'test' in meta.meta:
            deps.update(remove_versions(meta.meta['test'].get('requires', [])))

    return packages, deps

def _create_recipes(repository, recipes, variant_config_files, variants, channels):
    """
    Create a recipe dictionary for each recipe within a repository. The dictionary
    will have all of the information needed to build the recipe, as well as to
    create the dependency tree.
    """
    saved_working_directory = os.getcwd()
    os.chdir(repository)

    config_data, _ = build_feedstock.load_package_config()
    outputs = []
    for recipe in config_data.get('recipes', []):
        if recipes and not recipe.get('name') in recipes:
            continue
        packages, deps = _get_package_dependencies(recipe.get('path'), variant_config_files, variants)
        output = { 'recipe' : recipe.get('name', None),
                   'repository' : repository,
                   'packages' : packages,
                   'dependencies' : deps,
                   'channels' : channels if channels else []}
        outputs.append(output)

    os.chdir(saved_working_directory)
    return outputs

def _create_dep_tree(recipes):
    """
    Create a dependency tree for a list of recipes.

    Each recipe will contain a 'dependencies` key which contains a list of integers.
    Each integer in the list represents the index of the dependencies recipe within the
    recipe list.
    """

    # Create a packages dictionary that uses all of a recipe's packages as key, with
    # the recipes index as values.
    packages = dict()
    for index, recipe in enumerate(recipes):
        for package in recipe.get('packages', []):
            packages.update({ package : [index] + packages.get(package, []) })

    # Create a new list of dictionary items that each contain:
    #     A list of indices for each dependency.
    #     A boolean indicating whether the recipe has been seen during a traversal
    # Note: This will filter out all dependencies that aren't in the recipes list.
    outputs = []
    for index, recipe in enumerate(recipes):
        deps = []
        for dep in recipe.get('dependencies', []):
            if dep in packages:
                deps += filter(lambda x: x != index, packages[dep])
        output = { 'dep_indices' : deps,
                   'seen' : False }
        outputs.append(output)

    return outputs

def _traverse_deps_tree(recipes, deps_tree, deps):
    """
    Generator function that goes through a recipes dependency tree.
    """
    for dep in deps:
        if deps_tree[dep]['seen']:
            continue
        yield from _traverse_deps_tree(recipes, deps_tree, deps_tree[dep]['dep_indices'])
        yield recipes[dep]
        deps_tree[dep]['seen'] = True

def _traverse_recipes(recipes, deps_tree):
    """
    Generator function that goes through every recipe in a list.
    If a recipe has dependencies, those recipes will be returned
    first.
    """
    yield from _traverse_deps_tree(recipes, deps_tree, range(len(recipes)))

def build_env(arg_strings=None):
    parser = make_parser()
    args = parser.parse_args(arg_strings)
    result = 0

    python_build_args = []
    common_package_build_args = []
    common_package_build_args += ["--output_folder", os.path.abspath(args.output_folder)]
    common_package_build_args += ["--channel", os.path.abspath(args.output_folder)]
    common_package_build_args += ["--conda_build_config", os.path.abspath(args.conda_build_config)]

    if args.build_types:
        common_package_build_args += ["--build_types", args.build_types]

    for channel in args.channels_list:
        common_package_build_args += ["--channels", channel]

    # If repository_folder doesn't exist, create it
    if args.repository_folder and not os.path.exists(args.repository_folder):
        os.mkdir(args.repository_folder)

    for py_vers in parse_arg_list(args.python_versions):
        print("Builds for python version: " + py_vers)
        python_build_args = ["--python_versions", py_vers]
        variants = { 'python' : py_vers, 'build_type' : parse_arg_list(args.build_types) }
        env_config_data_list = load_env_config_files(args.env_config_file, variants)

        packages_seen = set()
        recipes = []
        # Create recipe dictionaries for each repository in the environment file
        for env_config_data in env_config_data_list:

            packages = env_config_data.get('packages', [])
            if not packages:
                packages = []
            for package in packages:
                if make_hash(package) in packages_seen:
                    continue

                # Check if the directory for the feedstock already exists.
                # If it doesn't attempt to clone the repository.
                repository = package['feedstock'] + "-feedstock"
                if args.repository_folder:
                    repo_dir = os.path.join(args.repository_folder, repository)
                else:
                    repo_dir = repository

                if not os.path.exists(repo_dir):
                    result = _clone_repo(args.git_location, repo_dir, env_config_data, package.get('git_tag'), args.git_tag_for_env)
                    if result != 0:
                        return result

                recipes += _create_recipes(repo_dir, package.get('recipes'), [os.path.abspath(args.conda_build_config)], variants, env_config_data.get('channels', None))
                packages_seen.add(make_hash(package))

        # Add dependency tree information to the packages list
        dep_tree = _create_dep_tree(recipes)

        # Build each package in the packages list
        for recipe in _traverse_recipes(recipes, dep_tree):
            package_build_args = ["--working_directory", recipe['repository']]

            for channel in recipe.get('channels', []):
                package_build_args += ["--channels", channel]

            if 'recipe' in recipe:
                package_build_args += ["--recipes", recipe['recipe']]

            result = build_feedstock.build_feedstock(common_package_build_args + python_build_args + package_build_args)
            if result != 0:
                print("Unable to build recipe: " +  recipe['repository'])
                return result

    return result

if __name__ == '__main__':
    sys.exit(build_env())
