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

import sys
import pathlib
import os
import glob
import git_utils
import tag_all_repos

sys.path.append(os.path.join(pathlib.Path(__file__).parent.absolute(), '..', 'open-ce'))
import inputs # pylint: disable=wrong-import-position

def _make_parser():
    ''' Parser input arguments '''
    parser = inputs.make_parser([git_utils.Argument.PUBLIC_ACCESS_TOKEN, git_utils.Argument.REPO_DIR,
                                    git_utils.Argument.BRANCH],
                                    description = 'A script that can be used to cut an open-ce release.')

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
        '--code-name',
        type=str,
        default=None,
        help="""Code name for release.""")

    return parser

def _main(arg_strings=None):
    parser = _make_parser()
    args = parser.parse_args(arg_strings)
    version_name = "open-ce-v{}".format(args.version)
    release_number = ".".join(args.version.split(".")[:-1])
    branch_name = "open-ce-r{}".format(release_number)
    primary_repo_url = "git@github.com:{}/{}.git".format(args.github_org, args.primary_repo)

    version_msg = "Open-CE Version {}".format(args.version)
    release_name = "v{}".format(args.version)
    if args.code_name:
        version_msg = "{} Code-named {}".format(version_msg, args.code_name)
        release_name = "{} ({})".format(release_name, args.code_name)

    primary_repo_path = os.path.abspath(os.path.join(args.repo_dir, args.primary_repo))
    print("--->Making clone location: " + primary_repo_path)
    os.makedirs(primary_repo_path, exist_ok=True)
    print("--->Cloning {}".format(primary_repo_url))
    git_utils.clone_repo(primary_repo_url, primary_repo_path, args.branch)

    print("--->Creating {} branch in {}".format(version_name, args.primary_repo))
    git_utils.create_branch(primary_repo_path, branch_name)

    print("--->Updating env files.")
    _update_env_files(primary_repo_path, version_name)

    print("--->Committing env files.")
    git_utils.commit_changes(primary_repo_path, "Updates for {}".format(release_number))

    print("--->Tag Primary Branch")
    git_utils.create_tag(primary_repo_path, version_name, version_msg)

    push = git_utils.ask_for_input("Would you like to push changes to primary repo?")
    if push.startswith("y"):
        print("--->Pushing branch.")
        git_utils.push_branch(primary_repo_path, branch_name)
        print("--->Pushing tag.")
        git_utils.push_branch(primary_repo_path, version_name)

    tag_all_repos.tag_all_repos(github_org=args.github_org,
                                tag=version_name,
                                tag_msg=version_msg,
                                branch=args.branch,
                                repo_dir=args.repo_dir,
                                pat=args.pat,
                                skipped_repos=args.primary_repo)

    release = git_utils.ask_for_input("Would you like to create a github release?")
    if release.startswith("y"):
        print("--->Creating Draft Release.")
        git_utils.create_release(args.github_org, args.primary_repo, args.pat, version_name, release_name, version_msg, True)

def _update_env_files(open_ce_path, new_git_tag):
    for env_file in glob.glob(os.path.join(open_ce_path, "envs", "*.yaml")):
        print("--->Updating {}".format(env_file))
        with open(env_file, 'r') as content_file:
            env_file_contents = content_file.read()
        if not "git_tag_for_env" in env_file_contents:
            env_file_contents = """{}
git_tag_for_env: {}
""".format(env_file_contents, new_git_tag)

        with open(env_file, 'w') as content_file:
            content_file.write(env_file_contents)

if __name__ == '__main__':
    try:
        _main()
        sys.exit(0)
    except Exception as exc:# pylint: disable=broad-except
        print("Error: ", exc)
        sys.exit(1)
