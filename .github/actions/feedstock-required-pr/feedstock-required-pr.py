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
import sys
import os
import pathlib
import subprocess
test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', '..', '..', 'open-ce'))

import conda_build.api
from conda_build.config import get_or_merge_config

import build_feedstock
import utils

def make_parser():
    ''' Parser for input arguments '''
    arguments = [utils.Argument.PYTHON_VERSIONS, utils.Argument.BUILD_TYPES]
    parser = utils.make_parser(arguments,
                               description = 'PR Test for Feedstocks',
                               formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    return parser

def feedstock_pr(arg_strings=None):
    '''
    Entry function.
    '''
    parser = make_parser()
    args = parser.parse_args(arg_strings)
    variants = [{ 'python' : py_vers, 'build_type' : build_type } for py_vers in utils.parse_arg_list(args.python_versions)
                                                                  for build_type in utils.parse_arg_list(args.build_types)]

    build_config_data, recipe_config_file = build_feedstock.load_package_config()
    print(build_config_data)

    pr_branch = get_result("git log -1 --format='%H'")
    default_branch = get_result("git log -2 --format='%H' | tail -n 1")

    config = get_or_merge_config(None)
    config.variant_config_files = [utils.DEFAULT_CONDA_BUILD_CONFIG, recipe_config_file]
    config.verbose = False

    utils.run_and_log("git checkout {}".format(default_branch))
    master_build_numbers = set()
    for recipe in build_config_data["recipes"]:
        metas = conda_build.api.render(recipe['path'],
                                    config=config,
                                    variants=variants[0],
                                    bypass_env_check=True,
                                    finalize=False)
        master_build_numbers.update([(meta.meta['package']['name'], meta.meta['build']['number']) for meta,_,_ in metas])

    utils.run_and_log("git checkout {}".format(pr_branch))
    current_pr_build_numbers = set()
    for recipe in build_config_data["recipes"]:
        metas = conda_build.api.render(recipe['path'],
                                    config=config,
                                    variants=variants[0],
                                    bypass_env_check=True,
                                    finalize=False)
        current_pr_build_numbers.update([(meta.meta['package']['name'], meta.meta['build']['number']) for meta,_,_ in metas])

    if current_pr_build_numbers == master_build_numbers:
        print("There is no change in build numbers.")
        return 1

    return 0

def get_result(command):
    return subprocess.check_output(command, shell=True).decode("utf-8").strip()

if __name__ == '__main__':
    sys.exit(feedstock_pr())
