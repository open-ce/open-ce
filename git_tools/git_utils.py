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
from enum import Enum, unique
import yaml
import requests

sys.path.append(os.path.join(pathlib.Path(__file__).parent.absolute(), '..', 'open-ce'))
import utils # pylint: disable=wrong-import-position

@unique
class Argument(Enum):
    '''Enum for Arguments'''
    PUBLIC_ACCESS_TOKEN = (lambda parser: parser.add_argument(
                                          '--pat',
                                          type=str,
                                          required=True,
                                          help="""Github public access token."""))
    REPO_DIR = (lambda parser: parser.add_argument(
                              '--repo-dir',
                              type=str,
                              default="./",
                              help="""Directory to store repos."""))
    BRANCH = (lambda parser: parser.add_argument(
                            '--branch',
                            type=str,
                            default=None,
                            help="""Branch to work from."""))

def get_all_repos(github_org, token):
    '''Use the github API to get all repos for an org.'''
    result = requests.get("https://api.github.com/orgs/{}/repos".format(github_org),
                     headers={'Authorization' : 'token {}'.format(token)})
    if result.status_code != 200:
        raise Exception("Error loading repos.")
    return yaml.safe_load(result.content)

def clone_repo(git_url, repo_dir, git_tag=None):
    '''Clone a repo to the given location.'''
    if git_tag is None:
        clone_cmd = "git clone " + git_url + " " + repo_dir
    else:
        clone_cmd = "git clone -b " + git_tag + " --single-branch " + git_url + " " + repo_dir
    if utils.run_and_log(clone_cmd) != 0:
        raise Exception("Unable to clone repository: {}".format(git_url))

def _execute_git_command(repo_path, git_cmd):
    saved_working_directory = os.getcwd()
    os.chdir(repo_path)
    result = utils.run_and_log(git_cmd)
    os.chdir(saved_working_directory)
    if result != 0:
        raise Exception("Git command failed: {}".format(git_cmd))

def create_tag(repo_path, tag_name, tag_msg):
    '''Create an annotated tag in the given repo.'''
    _execute_git_command(repo_path, "git tag -a {} -m \"{}\"".format(tag_name, tag_msg))

def create_branch(repo_path, branch_name):
    '''Create a branch in the given repo.'''
    _execute_git_command(repo_path, "git checkout -b {}".format(branch_name))

def commit_changes(repo_path, commit_msg):
    '''Commit the outstanding changes in the given repo.'''
    _execute_git_command(repo_path, "git commit -avm \"{}\"".format(commit_msg))

def push_branch(repo_path, branch_name, remote="origin"):
    '''Push the given repo to the remote branch.'''
    _execute_git_command(repo_path, "git push {} {}".format(remote, branch_name))

def ask_for_input(message, acceptable=None):
    '''Repeatedly ask for user input until an acceptable response is given.'''
    if not acceptable:
        acceptable = ["yes", "y", "no", "n"]
    display_message = "{} ({}) > ".format(message, "/".join(acceptable))
    user_input = input(display_message)
    while user_input.lower() not in acceptable:
        print("{} is not a valid selection.".format(user_input))
        user_input = input(display_message)
    return user_input.lower()
