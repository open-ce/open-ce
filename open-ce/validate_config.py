#!/usr/bin/env python

"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""

import argparse
import os
import sys
import build_env
import utils

DEFAULT_BUILD_TYPES = "cpu,cuda"
DEFAULT_PYTHON_VERS = "3.6"

def make_parser():
    ''' Parser input arguments '''
    parser = argparse.ArgumentParser(
        description = 'Perform validation on a cond_build_config.yaml file.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        'conda_build_config',
        type=str,
        help="""File to validate.""")

    parser.add_argument(
        '--env_files',
        nargs='+',
        required=True,
        type=str,
        default=[],
        help="""Environment files.""")

    parser.add_argument(
        '--python_versions',
        type=str,
        default=DEFAULT_PYTHON_VERS,
        help='Comma delimited list of python versions to build for, such as "3.6" or "3.7".')

    parser.add_argument(
        '--build_types',
        type=str,
        default=DEFAULT_BUILD_TYPES,
        help='Comma delimited list of build types, such as "cpu" or "cuda".')

    parser.add_argument(
        '--repository_folder',
        type=str,
        default="./",
        help="Directory that contains the repositories. If the"
             "repositories don't exist locally, they will be"
             "downloaded from OpenCE's git repository. If no value is provided,"
             "repositories will be downloaded to the current working directory.")

    return parser

def run_and_log(command):
    '''Print a shell command and then execute it.'''
    print("--->{}".format(command))
    return os.system(command)

def generalize_version(package):
    """Add `.*` to package versions when it is needed."""
    dep = package
    if ("=" in dep or (dep[-1].isdigit() and "." in dep)) and not dep[-2:] == ".*":
        dep += ".*"
    if " " in dep and not "." in dep.split()[1]:
        dep += ".*"
    return dep

def validate_config(arg_strings=None):
    '''
    Entry function.
    '''
    args = make_parser().parse_args(arg_strings)
    variants = [{ 'python' : py_vers, 'build_type' : build_type } for py_vers in utils.parse_arg_list(args.python_versions)
                                                                  for build_type in utils.parse_arg_list(args.build_types)]
    for variant in variants:
        print('Validating {} for {}'.format(args.conda_build_config, variant))
        for env_file in args.env_files:
            print('Validating {} for {} : {}'.format(args.conda_build_config, env_file, variant))
            retval,recipes = build_env.create_all_recipes([env_file],
                                                        variant,
                                                        repository_folder=args.repository_folder,
                                                        conda_build_config=args.conda_build_config)
            if retval == 0:
                packages = [package for recipe in recipes for package in recipe["packages"]]
                channels = {channel for recipe in recipes for channel in recipe["channels"]}
                deps = {dep for recipe in recipes for dep in recipe.get("run_dependencies")}

                pkg_args = " ".join(["\"{}\"".format(generalize_version(dep)) for dep in deps
                                                                              if not utils.remove_version(dep) in packages])

                channel_args = " ".join({"-c \"{}\"".format(channel) for channel in channels})

                cli = "conda create --dry-run -n test_conda_dependencies {} {}".format(channel_args, pkg_args)

                retval = run_and_log(cli)

            if retval != 0:
                print('Error while validating {} for {} : {}'.format(args.conda_build_config, env_file, variant))
                return 1

            print('Successfully validated {} for {} : {}'.format(args.conda_build_config, env_file, variant))

        print('Successfully validated {} for {}'.format(args.conda_build_config, variant))

    print("{} Successfully validated!".format(args.conda_build_config))
    return 0

if __name__ == '__main__':
    sys.exit(validate_config())
