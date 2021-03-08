#!/usr/bin/env python
# *****************************************************************
# (C) Copyright IBM Corp. 2020, 2021. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# *****************************************************************

"""
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
                             --branch main \\
                             --skipped_repos open-ce
*******************************************************************************
"""

import os
import sys
import pathlib
import git_utils

sys.path.append(os.path.join(pathlib.Path(__file__).parent.absolute(), '..'))
from open_ce import inputs # pylint: disable=wrong-import-position

def _make_parser():
    ''' Parser input arguments '''
    parser = inputs.make_parser([git_utils.Argument.PUBLIC_ACCESS_TOKEN, git_utils.Argument.REPO_DIR,
                                    git_utils.Argument.BRANCH, git_utils.Argument.ORG, git_utils.Argument.SKIPPED_REPOS],
                                    description = 'Tag all repos in an organization.')

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

    return parser

def tag_all_repos(github_org, tag, tag_msg, branch, repo_dir, pat, skipped_repos): # pylint: disable=too-many-arguments
    '''
    Clones, then tags all repos with a given tag, and pushes back to remote.
    These steps are performed in separate loops to make debugging easier.
    '''
    skipped_repos = inputs.parse_arg_list(skipped_repos)
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
            cont_tag = git_utils.ask_for_input("Would you like to continue tagging other repos?")
            if cont_tag.startswith("y"):
                continue
            raise

def _main(arg_strings=None):
    parser = _make_parser()
    args = parser.parse_args(arg_strings)
    tag_all_repos(args.github_org, args.tag, args.tag_msg, args.branch, args.repo_dir, args.pat, args.skipped_repos)

if __name__ == '__main__':
    try:
        _main()
    except Exception as exc:# pylint: disable=broad-except
        print("Error: ", exc)
        sys.exit(1)
