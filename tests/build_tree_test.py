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
import pytest

test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'open-ce'))
import build_tree
import utils
from errors import OpenCEError
import helpers

class TestBuildTree(build_tree.BuildTree):
    __test__ = False
    def __init__(self, #pylint: disable=super-init-not-called
                 env_config_files,
                 python_versions,
                 build_types,
                 mpi_types,
                 repository_folder="./",
                 git_location=utils.DEFAULT_GIT_LOCATION,
                 git_tag_for_env="master",
                 conda_build_config=utils.DEFAULT_CONDA_BUILD_CONFIG):
        self._env_config_files = env_config_files
        self._repository_folder = repository_folder
        self._git_location = git_location
        self._git_tag_for_env = git_tag_for_env
        self._conda_build_config = conda_build_config

def test_create_recipes(mocker):
    '''
    Tests that `_create_recipes` correctly builds the recipe and extracts all
    of the dependencies from the conda_build render result.
    '''
    dirTracker = helpers.DirTracker()
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
        side_effect=(lambda x: dirTracker.validate_chdir(x, expected_dirs=["/test/my_repo", # First the working directory should be changed to the arg.
                                                                           "/test/starting_dir"])) # And then changed back to the starting directory.
    )

    create_recipes_result = build_tree._create_recipes("/test/my_repo", None, "master", {'python' : '3.6', 'build_type' : 'cuda', 'mpi_type' : 'openmpi'}, [])
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
    git_location = utils.DEFAULT_GIT_LOCATION

    mock_build_tree = TestBuildTree([], "3.6", "cpu", "openmpi")

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=["git clone",
                                                               "-b master",
                                                               "--single-branch",
                                                               git_location + "/my_repo.git",
                                                               "/test/my_repo"]))
    )

    mock_build_tree._clone_repo(git_location + "/my_repo.git", "/test/my_repo", None, "master")

def test_clone_repo_failure(mocker):
    '''
    Simple negative test for `_clone_repo`.
    '''
    mock_build_tree = TestBuildTree([], "3.6", "cpu", "openmpi")

    mocker.patch(
        'os.system',
        side_effect=(lambda x: helpers.validate_cli(x, expect=["git clone"], retval=1))
    )

    with pytest.raises(OpenCEError) as exc:
        mock_build_tree._clone_repo("https://bad_url", "/test/my_repo", None, "master")
    assert "Unable to clone repository" in str(exc.value)

sample_build_commands = [build_tree.BuildCommand("recipe1",
                                    "repo1",
                                    ["package1a", "package1b"],
                                    python="2.6",
                                    build_type="cuda",
                                    mpi_type="openmpi",
                                    build_command_dependencies=[1,2]),
                         build_tree.BuildCommand("recipe2",
                                    "repo2",
                                    ["package2a"],
                                    python="2.6",
                                    build_type="cpu",
                                    mpi_type="openmpi",
                                    build_command_dependencies=[]),
                         build_tree.BuildCommand("recipe3",
                                    "repo3",
                                    ["package3a", "package3b"],
                                    build_command_dependencies=[1])]

def test_get_dependency_names():
    '''
    Tests that the dependency names can be retrieved for each item in a BuildTree
    '''
    mock_build_tree = TestBuildTree([], "3.6", "cpu", "openmpi")
    mock_build_tree.build_commands = sample_build_commands

    output = ""
    for build_command in mock_build_tree:
        output += ' '.join([mock_build_tree[dep].name() for dep in build_command.build_command_dependencies]) + "\n"

    expected_output = "\nrecipe2-py2-6-cpu-openmpi\nrecipe2-py2-6-cpu-openmpi recipe3\n"

    assert output == expected_output

def test_build_tree_len():
    '''
    Tests that the __len__ function works for BuildTree
    '''
    mock_build_tree = TestBuildTree([], "3.6", "cpu", "openmpi")
    mock_build_tree.build_commands = sample_build_commands

    assert len(mock_build_tree) == 3
