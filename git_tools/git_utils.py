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
import subprocess
from enum import Enum, unique
import yaml
import requests

sys.path.append(os.path.join(pathlib.Path(__file__).parent.absolute(), '..', 'open-ce'))
import utils # pylint: disable=wrong-import-position

GITHUB_API = "https://api.github.com"

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

    ORG = (lambda parser: parser.add_argument(
                            'github_org',
                            type=str,
                            help="""Github org to tag."""))

    SKIPPED_REPOS = (lambda parser: parser.add_argument(
                            '--skipped_repos',
                            type=str,
                            default="",
                            help="""Comma delimitted list of repos to skip tagging."""))

def get_all_repos(github_org, token):
    '''
    Use the github API to get all repos for an org.
    https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#list-organization-repositories
    '''
    retval = []
    page_index = 1
    while True:
        options = "sort=full_name&order=asc&page={}&per_page=100".format(page_index)
        result = requests.get("{}/orgs/{}/repos?{}".format(GITHUB_API, github_org, options),
                              headers={'Authorization' : 'token {}'.format(token)})
        if result.status_code != 200:
            raise Exception("Error loading repos.")
        yaml_result = yaml.safe_load(result.content)
        if not yaml_result:
            return retval
        retval += yaml_result
        page_index += 1

def create_release(github_org, repo, token, tag_name, name, body, draft):# pylint: disable=too-many-arguments
    '''
    Use the github API to create an actual release on github.
    https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#create-a-release
    '''
    result = requests.post("{}/repos/{}/{}/releases".format(GITHUB_API, github_org, repo),
                            headers={'Authorization' : 'token {}'.format(token)},
                            json={
                            "tag_name": tag_name,
                            "name": name,
                            "body": body,
                            "draft": draft
                            })
    if result.status_code != 201:
        raise Exception("Error creating github release.")
    return yaml.safe_load(result.content)

def create_pr(github_org, repo, token, title, body, head, base):# pylint: disable=too-many-arguments
    '''Create a PR in the given Repo.'''
    result = requests.post("{}/repos/{}/{}/pulls".format(GITHUB_API, github_org, repo),
                           headers={'Authorization' : 'token {}'.format(token)},
                           json={
                               "title": title,
                               "body": body,
                               "head": head,
                               "base": base
                               })
    if result.status_code != 201:
        raise Exception("Error creating PR.")
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
    print("--->{}".format(git_cmd))
    result,std_out,_ = utils.run_command_capture(git_cmd, stderr=subprocess.STDOUT)
    os.chdir(saved_working_directory)
    if not result:
        raise Exception("Git command failed: {}\n{}".format(git_cmd, std_out))
    return std_out

def create_tag(repo_path, tag_name, tag_msg):
    '''Create an annotated tag in the given repo.'''
    _execute_git_command(repo_path, "git tag -a {} -m \"{}\"".format(tag_name, tag_msg))

def create_branch(repo_path, branch_name):
    '''Create a branch in the given repo.'''
    _execute_git_command(repo_path, "git checkout -b {}".format(branch_name))

def commit_changes(repo_path, commit_msg):
    '''Commit the outstanding changes in the given repo.'''
    _execute_git_command(repo_path, "git add ./*")
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

def get_current_branch(repo_path):
    '''Retrieve the active branch of the given repo.'''
    return _execute_git_command(repo_path, "git rev-parse --abbrev-ref HEAD").strip()

def apply_patch(repo_path, patch_path):
    '''Apply a patch to the given repo.'''
    _execute_git_command(repo_path, "cat \"{}\" | git am -3 -k".format(patch_path))
