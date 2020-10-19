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

import os
import sys
import pathlib
import git_utils

sys.path.append(os.path.join(pathlib.Path(__file__).parent.absolute(), '..', 'open-ce'))
import utils # pylint: disable=wrong-import-position

def _make_parser():
    ''' Parser input arguments '''
    parser = utils.make_parser([git_utils.Argument.PUBLIC_ACCESS_TOKEN, git_utils.Argument.REPO_DIR,
                                git_utils.Argument.BRANCH],
                               description = 'Tag all repos in an organization.')

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
        '--skipped_repos',
        type=str,
        default="",
        help="""Comma delimitted list of repos to skip tagging.""")

    return parser

def _main(arg_strings=None):
    parser = _make_parser()
    args = parser.parse_args(arg_strings)
    tag_all_repos(args.github_org, args.tag, args.tag_msg, args.branch, args.repo_dir, args.pat, args.skipped_repos)

def tag_all_repos(github_org, tag, tag_msg, branch, repo_dir, pat, skipped_repos): # pylint: disable=too-many-arguments
    '''
    Clones, then tags all repos with a given tag, and pushes back to remote.
    These steps are performed in separate loops to make debugging easier.
    '''
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

    push = git_utils.ask_for_input("Would you like to push all tags to remote?")
    if not push.startswith("y"):
        return

    print("---------------------------Pushing all Repos")
    for repo in repos:
        try:
            repo_path = os.path.abspath(os.path.join(repo_dir, repo["name"]))
            print("--->Pushing {}".format(repo["name"]))
            git_utils.push_branch(repo_path, tag)
        except Exception as exc:# pylint: disable=broad-except
            print("Error encountered when trying to push {}".format(repo["name"]))
            print(exc)
            cont = git_utils.ask_for_input("Would you like to continue with the other repos?")
            if cont.startswith("y"):
                continue
            raise

if __name__ == '__main__':
    try:
        _main()
        sys.exit(0)
    except Exception as exc:# pylint: disable=broad-except
        print("Error: ", exc)
        sys.exit(1)
