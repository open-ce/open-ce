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
import pathlib
import yaml

import conda_build.metadata
import conda_build.api
from conda_build.config import get_or_merge_config

test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'builder'))
import build_env
import build_feedstock
import utils

PYTHON_VERIONS = ['3.6','3.7']
BUILD_TYPES = ['cpu', 'cuda']

VARIANTS = [{ 'python' : [py_vers], 'build_type' : [build_type] } for py_vers in PYTHON_VERIONS for build_type in BUILD_TYPES]

def make_parser():
    ''' Parser input arguments '''
    parser = argparse.ArgumentParser(
        description = 'Lint Environment Files',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        'conda_build_config',
        type=str,
        help="""File to lint.""")

    parser.add_argument(
        '--env_files',
        nargs='*',
        type=str,
        default=[],
        help="""Environment files.""")

    return parser

def remove_version(package):
    return package.split()[0].split("=")[0]

def run_and_log(command):
    print("--->" + command)
    return os.system(command)

def main(arg_strings=None):
    parser = make_parser()
    args = parser.parse_args(arg_strings)
    for variant in VARIANTS:
        for env_file in args.env_files:
            print(str(env_file) + " : " + str(variant))
            retval,recipes = build_env._create_all_recipes([env_file],
                                                        variant,
                                                        repository_folder="./repos/",
                                                        conda_build_config=args.conda_build_config)

            packages = [package for recipe in recipes for package in recipe["packages"]]
            deps = [dep for recipe in recipes for dep in recipe["versioned_dependencies"]]

            cli = " -c https://public.dhe.ibm.com/ibmdl/export/pub/software/server/ibm-ai/conda/ "
            deps = [dep for dep in deps if not remove_version(dep) in packages]
            for dep in deps:
                if dep[-1].isdigit() and not dep[-2:] == ".*" and "." in dep:
                    dep += ".*"
                cli += "\"" + dep + "\" "

            retval = run_and_log("conda create --dry-run -n test_conda_dependencies " + cli)

            if retval != 0:
                print("An error was encountered!")
                return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())