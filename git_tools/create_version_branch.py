#!/usr/bin/env python
"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************

*******************************************************************************
Script: create_version_branch.py
A script that can be used to create a version branch for an Open-CE feedstock.

The user will pass in a link to a repository, plus an optional commit. After
running the script, a new remote branch will be added to the repository with
a name based on the version number of the packages within the feedstock.
*******************************************************************************
"""

import os
import sys
import shutil
import pathlib
import git_utils

sys.path.append(os.path.join(pathlib.Path(__file__).parent.absolute(), '..', 'open-ce'))
# pylint: disable=wrong-import-position
import inputs
import conda_utils
import build_feedstock

def _make_parser():
    ''' Parser input arguments '''
    parser = inputs.make_parser([git_utils.Argument.REPO_DIR],
                                    description = 'Create a version branch for a feedstock.')

    parser.add_argument(
        '--repository',
        type=str,
        required=True,
        help="""URL to the git repository.""")

    parser.add_argument(
        '--commit',
        type=str,
        required=False,
        help="""Commit to branch from. If none is provided, the head of the repo will be used.""")

    return parser

def _get_repo_version(repo_path):
    '''
    Get the version of the first package that appears in the recipes list for the feedstock.
    '''
    saved_working_directory = os.getcwd()
    os.chdir(os.path.abspath(repo_path))

    build_config_data, _ = build_feedstock.load_package_config()

    for recipe in build_config_data["recipes"]:
        rendered_recipe = conda_utils.render_yaml(recipe["path"])
        for meta, _, _ in rendered_recipe:
            package_version = meta.meta['package']['version']
            if package_version and package_version != "None":
                os.chdir(saved_working_directory)
                return package_version

    raise Exception("Error: Unable to determine current version of the feedstock")

def _get_repo_name(repo_url):
    if not repo_url.endswith(".git"):
        repo_url += ".git"
    return os.path.splitext(os.path.basename(repo_url))[0]

def _main(arg_strings=None):
    parser = _make_parser()
    args = parser.parse_args(arg_strings)

    repo_name = _get_repo_name(args.repository)
    repo_url = args.repository
    repo_path = os.path.abspath(os.path.join(args.repo_dir, repo_name))
    print("--->Making clone location: " + repo_path)
    os.makedirs(repo_path, exist_ok=True)
    print("--->Cloning {}".format(repo_name))
    git_utils.clone_repo(repo_url, repo_path)

    if args.commit:
        git_utils.checkout(repo_path, args.commit)

    repo_version = _get_repo_version(repo_path)
    branch_name = "r" + repo_version

    if git_utils.branch_exists(repo_path, branch_name):
        print("The branch {} already exists.".format(branch_name))
    else:
        git_utils.create_branch(repo_path, branch_name)
        git_utils.push_branch(repo_path, branch_name)

    shutil.rmtree(repo_path)

if __name__ == '__main__':
    try:
        _main()
    except Exception as exc:# pylint: disable=broad-except
        print("Error: ", exc)
        sys.exit(1)
