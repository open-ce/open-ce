# *****************************************************************
#
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2020. All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# *****************************************************************

import sys
import os
import pathlib
test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'open-ce'))

import pytest

import build_tree
import utils
import helpers

class TestBuildTree(build_tree.BuildTree):
    __test__ = False
    def __init__(self,
                 env_config_files,
                 python_versions,
                 build_types,
                 repository_folder="./",
                 git_location=build_tree.DEFAULT_GIT_LOCATION,
                 git_tag_for_env="master",
                 conda_build_config=utils.DEFAULT_CONDA_BUILD_CONFIG):
        self._env_config_files = env_config_files
        self._repository_folder = repository_folder
        self._git_location = git_location
        self._git_tag_for_env = git_tag_for_env
        self._conda_build_config = conda_build_config

def test_create_recipes(mocker, capsys):
    '''
    Tests that `_create_recipes` correctly builds the recipe and extracts all
    of the dependencies from the conda_build render result.
    '''
    mocker.patch(
        'os.getcwd',
        return_value="/test/starting_dir"
    )
    render_result=helpers.make_render_result("horovod", ['build_req1', 'build_req2            1.2'],
                                                        ['run_req1            1.3'],
                                                        ['host_req1            1.0', 'host_req2'],
                                                        ['test_req1'])
    mocker.patch(
        'conda_build.api.render',
        return_value=render_result
    )
    mocker.patch(
        'os.chdir',
        side_effect=(lambda x: helpers.validate_chdir(x, expected_dirs=["/test/my_repo", # First the working directory should be changed to the arg.
                                                                        "/test/starting_dir"])) # And then changed back to the starting directory.
    )

    create_recipes_result = build_tree._create_recipes("/test/my_repo", None, "master", {'python' : ['3.6'], 'build_type' : ['cuda']}, [])
    assert create_recipes_result[0].packages == {'horovod'}
    for dep in {'build_req1', 'build_req2            1.2'}:
        assert dep in create_recipes_result[0].build_dependencies
    for dep in {'run_req1            1.3'}:
        assert dep in create_recipes_result[0].run_dependencies
    for dep in {'host_req1            1.0', 'host_req2'}:
        assert dep in create_recipes_result[0].host_dependencies
    for dep in {'test_req1'}:
        assert dep in create_recipes_result[0].test_dependencies

def test_clone_repo(mocker):
    '''
    Simple positive test for `_clone_repo`.
    '''
    git_location = build_tree.DEFAULT_GIT_LOCATION

    mock_build_tree = TestBuildTree([], "3.6", "cpu")

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=["git clone",
                                                               "-b master",
                                                               "--single-branch",
                                                               git_location + "/my_repo.git",
                                                               "/test/my_repo"]))
    )

    assert mock_build_tree._clone_repo("/test/my_repo", None, "master") == 0

def test_clone_repo_failure(mocker, capsys):
    '''
    Simple negative test for `_clone_repo`.
    '''
    git_location = build_tree.DEFAULT_GIT_LOCATION

    mock_build_tree = TestBuildTree([], "3.6", "cpu")

    mocker.patch(
        'os.system',
        side_effect=(lambda x: helpers.validate_cli(x, expect=["git clone"], retval=1))
    )

    assert mock_build_tree._clone_repo("/test/my_repo", None, "master") == 1
    captured = capsys.readouterr()
    assert "Unable to clone repository" in captured.out
