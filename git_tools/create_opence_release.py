#!/usr/bin/env python
"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************

*******************************************************************************
Script: create_opence_release.py
A script that can be used to cut an open-ce release.
*******************************************************************************
"""

import argparse
import sys
import os
import glob
import git_utils

def _make_parser():
    ''' Parser input arguments '''
    parser = argparse.ArgumentParser(
        description = 'A script that can be used to cut an open-ce release.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        '--github-org',
        type=str,
        default="open-ce",
        help="""Org to cut an Open-CE release in.""")

    parser.add_argument(
        '--primary-repo',
        type=str,
        default="open-ce",
        help="""Primary open-ce repo.""")

    parser.add_argument(
        '--version',
        type=str,
        required=True,
        help="""Release version to cut.""")

    parser.add_argument(
        '--branch',
        type=str,
        default=None,
        help="""Branch to cut a release from. Default is default branch in each repo.""")

    parser.add_argument(
        '--repo-dir',
        type=str,
        default="./",
        help="""Directory to store repos.""")

    parser.add_argument(
        '--pat',
        type=str,
        required=True,
        help="""Github public access token.""")

    return parser

def _main(arg_strings=None):
    parser = _make_parser()
    args = parser.parse_args(arg_strings)
    version_name = "open-ce-v{}".format(args.version)
    version_msg = "Open-CE Release {}".format(args.version)
    primary_repo_url = "git@github.com:{}/{}.git".format(args.github_org, args.primary_repo)

    primary_repo_path = os.path.abspath(os.path.join(args.repo_dir, args.primary_repo))
    print("--->Making clone location: " + primary_repo_path)
    os.makedirs(primary_repo_path, exist_ok=True)
    print("--->Cloning {}".format(primary_repo_url))
    git_utils.clone_repo(primary_repo_url, primary_repo_path, args.branch)

    print("--->Creating {} branch in {}".format(version_name, args.primary_repo))
    git_utils.create_branch(primary_repo_path, version_name)

    print("--->Updating env files.")
    update_env_files(primary_repo_path, version_name)

    return

    tag_all_repos.tag_all_repos(github_org=args.github_org,
                                tag=version_name,
                                tag_msg=version_msg,
                                branch=args.branch,
                                repo_dir=args.repo_dir,
                                pat=args.pat,
                                skipped_repos=args.primary_repo)

def update_env_files(open_ce_path, new_git_tag):
    for env_file in glob.glob(os.path.join(open_ce_path, "envs", "*.yaml")):
        print(env_file)

if __name__ == '__main__':
    try:
        _main()
        sys.exit(0)
    except Exception as exc:# pylint: disable=broad-except
        print("Error: ", exc)
        sys.exit(1)
