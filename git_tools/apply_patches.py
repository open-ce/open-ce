#!/usr/bin/env python
"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""

import os
import sys
import pathlib
import git_utils

sys.path.append(os.path.join(pathlib.Path(__file__).parent.absolute(), '..', 'open-ce'))
import inputs # pylint: disable=wrong-import-position


def make_parser():
    ''' Parser input arguments '''
    parser = inputs.make_parser([git_utils.Argument.PUBLIC_ACCESS_TOKEN, git_utils.Argument.REPO_DIR,
                                    git_utils.Argument.BRANCH, git_utils.Argument.ORG, git_utils.Argument.SKIPPED_REPOS],
                                    description = 'Apply patches to all repos in an organization.')

    parser.add_argument(
        '--commit-msg',
        type=str,
        default="Apply Patches.",
        help="""Commit message to use.""")

    parser.add_argument(
        '--pr-msg',
        type=str,
        default="Apply Patches.",
        help="""PR message to use.""")

    parser.add_argument(
        '--patches',
        type=str,
        default="",
        help="""Patches to aply to repos.""")

    return parser

def _main(arg_strings=None):
    parser = make_parser()
    args = parser.parse_args(arg_strings)

    skipped_repos = inputs.parse_arg_list(args.skipped_repos)
    repos = git_utils.get_all_repos(args.github_org, args.pat)
    repos = [repo for repo in repos if repo["name"] not in skipped_repos]

    patches = [os.path.abspath(arg_file) for arg_file in inputs.parse_arg_list(args.patches)]
    for repo in repos:
        try:
            print("Beginning " + repo["name"] + "---------------------------")

            repo_path = os.path.abspath(os.path.join(args.repo_dir, repo["name"]))
            print("--->Making clone location: " + repo_path)
            os.makedirs(repo_path, exist_ok=True)
            print("--->Cloning {}".format(repo["name"]))
            git_utils.clone_repo(repo["ssh_url"], repo_path)
            head_branch = git_utils.get_current_branch(repo_path)
            git_utils.create_branch(repo_path, args.branch)

            for patch in patches:
                print("--->Applying Patch {}".format(patch))
                git_utils.apply_patch(repo_path, patch)

            print("--->Pushing Branch")
            git_utils.push_branch(repo_path, args.branch)

            print("--->Creating PR")
            git_utils.create_pr(args.github_org,
                                repo["name"],
                                args.pat,
                                args.commit_msg,
                                args.pr_msg,
                                args.branch,
                                head_branch)

            print("---------------------------" + "Finished " + repo["name"])
        except Exception as exc:# pylint: disable=broad-except
            print("Error encountered when trying to patch {}".format(repo["name"]))
            print(exc)
            cont = git_utils.ask_for_input("Would you like to continue applying patches to other repos?")
            if cont.startswith("y"):
                continue
            raise

if __name__ == '__main__':
    try:
        _main()
        sys.exit(0)
    except Exception as exception:# pylint: disable=broad-except
        print("Error: ", exception)
        sys.exit(1)
