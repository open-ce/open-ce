#!/usr/bin/env python
"""
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

import os
import sys
import pathlib
import git_utils

sys.path.append(os.path.join(pathlib.Path(__file__).parent.absolute(), '..', 'open-ce'))
import inputs # pylint: disable=wrong-import-position


def make_parser():
    ''' Parser input arguments '''
    parser = inputs.make_parser([git_utils.Argument.PUBLIC_ACCESS_TOKEN, git_utils.Argument.REPO_DIR,
                                    git_utils.Argument.BRANCH, git_utils.Argument.ORG, git_utils.Argument.SKIPPED_REPOS,
                                    git_utils.Argument.REVIEWERS, git_utils.Argument.TEAM_REVIEWERS,
                                    git_utils.Argument.PARAMS],
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

    param_dict = {param.split(":")[0]: param.split(":")[1] for param in args.params}

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
                replaced_patch = git_utils.fill_in_params(patch, param_dict, default_branch=head_branch)
                print("--->Applying Patch {}".format(replaced_patch))
                git_utils.apply_patch(repo_path, replaced_patch)

            print("--->Pushing Branch")
            git_utils.push_branch(repo_path, args.branch)

            print("--->Creating PR")
            created_pr = git_utils.create_pr(args.github_org,
                                             repo["name"],
                                             args.pat,
                                             args.commit_msg,
                                             args.pr_msg,
                                             args.branch,
                                             head_branch)

            print("--->Requesting PR Review")
            git_utils.request_pr_review(args.github_org,
                                        repo["name"],
                                        args.pat,
                                        created_pr["number"],
                                        inputs.parse_arg_list(args.reviewers),
                                        inputs.parse_arg_list(args.team_reviewers))

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
