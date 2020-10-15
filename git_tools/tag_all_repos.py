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
*******************************************************************************
"""

import argparse
import os
import sys
import pathlib
import yaml
import requests

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

    return parser

def _main(arg_strings=None):
    parser = _make_parser()
    args = parser.parse_args(arg_strings)
    repos = _get_all_repos(args.github_org, args.pat)
    print("---------------------------Cloning all Repos")
    for repo in repos:
        repo_path = os.path.abspath(os.path.join(args.repo_dir, repo["name"]))
        print("--->Making clone location: " + repo_path)
        os.makedirs(repo_path, exist_ok=True)
        print("--->Cloning {}".format(repo["name"]))
        _clone_repo(repo["ssh_url"], repo_path, args.branch)

    print("---------------------------Tagging all Repos")
    for repo in repos:
        repo_path = os.path.abspath(os.path.join(args.repo_dir, repo["name"]))
        print("--->Tagging {}".format(repo["name"]))
        _create_tag(repo_path, args.tag, args.tag_msg)

    print("---------------------------Pushing all Repos")
    for repo in repos:
        repo_path = os.path.abspath(os.path.join(args.repo_dir, repo["name"]))
        print("--->Pushing {}".format(repo["name"]))
        _push_branch(repo_path, args.tag)

def _get_all_repos(github_org, token):
    result = requests.get("https://api.github.com/orgs/{}/repos".format(github_org),
                     headers={'Authorization' : 'token {}'.format(token)})
    if result.status_code != 200:
        raise Exception("Error loading repos.")
    return yaml.safe_load(result.content)

def _clone_repo(git_url, repo_dir, git_tag=None):
    if git_tag is None:
        clone_cmd = "git clone " + git_url + " " + repo_dir
    else:
        clone_cmd = "git clone -b " + git_tag + " --single-branch " + git_url + " " + repo_dir
    if utils.run_and_log(clone_cmd) != 0:
        raise Exception("Unable to clone repository: {}".format(git_url))

def _create_tag(repo_path, tag_name, tag_msg):
    saved_working_directory = os.getcwd()
    os.chdir(repo_path)
    tag_cmd = "git tag -a {} -m \"{}\"".format(tag_name, tag_msg)
    result = utils.run_and_log(tag_cmd)
    os.chdir(saved_working_directory)
    if result != 0:
        raise Exception("Unable to tag repository {}".format(repo_path))

def _push_branch(repo_path, branch_name, remote="origin"):
    saved_working_directory = os.getcwd()
    os.chdir(repo_path)
    push_cmd = "git push {} {}".format(remote, branch_name)
    result = utils.run_and_log(push_cmd)
    os.chdir(saved_working_directory)
    if result != 0:
        raise Exception("Unable to push repository {}".format(repo_path))

if __name__ == '__main__':
    try:
        _main()
        sys.exit(0)
    except Exception as exc:# pylint: disable=broad-except
        print("Error: ", exc)
        sys.exit(1)
