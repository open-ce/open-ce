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
import yaml
import requests

sys.path.append(os.path.join(pathlib.Path(__file__).parent.absolute(), '..', 'open-ce'))
import utils # pylint: disable=wrong-import-position

def get_all_repos(github_org, token):
    result = requests.get("https://api.github.com/orgs/{}/repos".format(github_org),
                     headers={'Authorization' : 'token {}'.format(token)})
    if result.status_code != 200:
        raise Exception("Error loading repos.")
    return yaml.safe_load(result.content)

def clone_repo(git_url, repo_dir, git_tag=None):
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
    _execute_git_command(repo_path, "git tag -a {} -m \"{}\"".format(tag_name, tag_msg))

def create_branch(repo_path, branch_name):
    _execute_git_command(repo_path, "git checkout -b {}".format(branch_name))

def commit_changes(repo_path, commit_msg):
    _execute_git_command(repo_path, "git commit -avm \"{}\"".format(commit_msg))

def push_branch(repo_path, branch_name, remote="origin"):
    _execute_git_command(repo_path, "git push {} {}".format(remote, branch_name))
