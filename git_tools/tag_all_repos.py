#!/usr/bin/env python
"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************

*******************************************************************************
Script: tag_all_repos.py
A script that can be used to create the same annotated git tag in all
repos within an organization.

To tag all of the feedstocks in the open-ce org with the tag `open-ce-v1.0.0`,
the following command can be used:
./git_tools/tag_all_repos.py open-ce \\
                             --tag open-ce-v1.0.0 \\
                             --tag-msg "Open-CE Release Version 1.0.0" \\
                             --pat ${YOUR_PUBLIC_ACCESS_TOKEN} \\
                             --repo-dir ./repos \\
                             --branch master \\
                             --skipped_repos open-ce
*******************************************************************************
"""

import argparse
import os
import sys
import pathlib
import git_utils

sys.path.append(os.path.join(pathlib.Path(__file__).parent.absolute(), '..', 'open-ce'))
import utils # pylint: disable=wrong-import-position

def _make_parser():
    ''' Parser input arguments '''
    parser = argparse.ArgumentParser(
        description = 'Tag all repos in an organization.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        'github_org',
        type=str,
        help="""Github org to tag.""")

    parser.add_argument(
        '--tag',
        type=str,
        required=True,
        help="""Tag to create.""")

    parser.add_argument(
        '--tag-msg',
        type=str,
        required=True,
        help="""Tag message to use.""")

    parser.add_argument(
        '--branch',
        type=str,
        default=None,
        help="""Branch to tag.""")

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

    parser.add_argument(
        '--skipped_repos',
        type=str,
        default="",
        help="""Comma delimitted list of repos to skip tagging.""")

    return parser

def _main(arg_strings=None):
    parser = _make_parser()
    args = parser.parse_args(arg_strings)
    tag_all_repos(args.github_org, args.tag, args.tag_msg, args.branch, args.repo_dir, args.pat, args.skipped_repos)

def tag_all_repos(github_org, tag, tag_msg, branch, repo_dir, pat, skipped_repos):
    skipped_repos = utils.parse_arg_list(skipped_repos)
    repos = git_utils.get_all_repos(github_org, pat)
    repos = [repo for repo in repos if repo["name"] not in skipped_repos ]
    print("---------------------------Cloning all Repos")
    for repo in repos:
        repo_path = os.path.abspath(os.path.join(repo_dir, repo["name"]))
        print("--->Making clone location: " + repo_path)
        os.makedirs(repo_path, exist_ok=True)
        print("--->Cloning {}".format(repo["name"]))
        git_utils.clone_repo(repo["ssh_url"], repo_path, branch)

    print("---------------------------Tagging all Repos")
    for repo in repos:
        repo_path = os.path.abspath(os.path.join(repo_dir, repo["name"]))
        print("--->Tagging {}".format(repo["name"]))
        git_utils.create_tag(repo_path, tag, tag_msg)

    print("---------------------------Pushing all Repos")
    for repo in repos:
        repo_path = os.path.abspath(os.path.join(repo_dir, repo["name"]))
        print("--->Pushing {}".format(repo["name"]))
        git_utils.push_branch(repo_path, tag)

if __name__ == '__main__':
    try:
        _main()
        sys.exit(0)
    except Exception as exc:# pylint: disable=broad-except
        print("Error: ", exc)
        sys.exit(1)
