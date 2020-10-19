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

import conda_build.api
from conda_build.config import get_or_merge_config

test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', '..', 'open-ce'))
import build_feedstock # pylint: disable=wrong-import-position
import utils # pylint: disable=wrong-import-position

def make_parser():
    ''' Parser for input arguments '''
    arguments = [utils.Argument.PYTHON_VERSIONS, utils.Argument.BUILD_TYPES, utils.Argument.MPI_TYPES]
    parser = utils.make_parser(arguments,
                               description = 'PR Test for Feedstocks',
                               formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    return parser

def main(arg_strings=None):
    '''
    Entry function.
    '''
    parser = make_parser()
    args = parser.parse_args(arg_strings)
    variants = utils.make_variants(args.python_versions, args.build_types, args.mpi_types)

    build_config_data, _ = build_feedstock.load_package_config()

    pr_branch = utils.get_output("git log -1 --format='%H'")
    utils.run_and_log("git remote set-head origin -a")
    default_branch = utils.get_output("git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'")

    config = get_or_merge_config(None)
    config.variant_config_files = [utils.DEFAULT_CONDA_BUILD_CONFIG]
    recipe_conda_build_config = os.path.join(os.getcwd(), "config", "conda_build_config.yaml")
    if os.path.exists(recipe_conda_build_config):
        config.variant_config_files += [recipe_conda_build_config]
    config.verbose = False

    utils.run_and_log("git checkout {}".format(default_branch))
    master_build_numbers = dict()
    for recipe in build_config_data["recipes"]:
        metas = conda_build.api.render(recipe['path'],
                                    config=config,
                                    variants=variants[0],
                                    bypass_env_check=True,
                                    finalize=False)
        for meta,_,_ in metas:
            master_build_numbers[meta.meta['package']['name']] = {"version" : meta.meta['package']['version'],
                                                                  "number" : meta.meta['build']['number']}

    utils.run_and_log("git checkout {}".format(pr_branch))
    current_pr_build_numbers = dict()
    for recipe in build_config_data["recipes"]:
        metas = conda_build.api.render(recipe['path'],
                                    config=config,
                                    variants=variants[0],
                                    bypass_env_check=True,
                                    finalize=False)
        for meta,_,_ in metas:
            current_pr_build_numbers[meta.meta['package']['name']] = {"version" : meta.meta['package']['version'],
                                                                      "number" : meta.meta['build']['number']}

    print("Current PR Build Info:    ", current_pr_build_numbers)
    print("Master Branch Build Info: ", master_build_numbers)

    #No build numbers can go backwards without a version change.
    for package in master_build_numbers:
        if package in current_pr_build_numbers and current_pr_build_numbers[package]["version"] == master_build_numbers[package]["version"]:
            assert int(current_pr_build_numbers[package]["number"]) >= int(master_build_numbers[package]["number"]), "If the version doesn't change, the build number can't be reduced."

    #If packages are added or removed, don't require a version change
    if set(master_build_numbers.keys()) != set(current_pr_build_numbers.keys()):
        return

    #At least one package needs to increase the build number or change the version.
    checks = [current_pr_build_numbers[package]["version"] != master_build_numbers[package]["version"] or
              int(current_pr_build_numbers[package]["number"]) > int(master_build_numbers[package]["number"])
                  for package in master_build_numbers]
    assert any(checks), "At least one package needs to increase the build number or change the version."

if __name__ == '__main__':
    try:
        main()
        print("BUILD NUMBER SUCCESS")
    except Exception as exc: # pylint: disable=broad-except
        print("BUILD NUMBER ERROR: ", exc)
        sys.exit(1)
