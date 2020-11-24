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
                 cuda_versions,
                 repository_folder="./",
                 git_location=utils.DEFAULT_GIT_LOCATION,
                 git_tag_for_env="master",
                 conda_build_config=utils.DEFAULT_CONDA_BUILD_CONFIG):
        self._env_config_files = env_config_files
        self._repository_folder = repository_folder
        self._git_location = git_location
        self._git_tag_for_env = git_tag_for_env
        self._conda_build_config = conda_build_config
        self._possible_variants = utils.make_variants(python_versions, build_types, mpi_types, cuda_versions)

def test_create_commands(mocker):
    '''
    Tests that `_create_commands` correctly builds the recipe and extracts all
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
                                                        ['test_req1'],
                                                        ['used_var1', 'used_var2'],
                                                        '',
                                                        ['string1_1'])
    mocker.patch(
        'conda_build.api.render',
        return_value=render_result
    )
    mocker.patch(
        'os.chdir',
        side_effect=(lambda x: dirTracker.validate_chdir(x, expected_dirs=["/test/my_repo", # First the working directory should be changed to the arg.
                                                                           "/test/starting_dir"])) # And then changed back to the starting directory.
    )

    build_commands, _ = build_tree._create_commands("/test/my_repo", None, "master", {'python' : '3.6', 'build_type' : 'cuda', 'mpi_type' : 'openmpi', 'cudatoolkit' : '10.2'}, [])
    assert build_commands[0].packages == {'horovod'}
    for dep in {'build_req1', 'build_req2            1.2'}:
        assert dep in build_commands[0].build_dependencies
    for dep in {'run_req1            1.3'}:
        assert dep in build_commands[0].run_dependencies
    for dep in {'host_req1            1.0', 'host_req2'}:
        assert dep in build_commands[0].host_dependencies
    for dep in {'test_req1'}:
        assert dep in build_commands[0].test_dependencies

def test_feedstock_args():
    '''
    Tests that feedstock_args creates the correct arguments.
    '''

    build_commands = [
        build_tree.BuildCommand("recipe", "repo", {"pkg1", "pkg2"}),

        build_tree.BuildCommand("recipe2", "repo2", {"pkg1", "pkg2"},
                                python="3.2", mpi_type="system",
                                build_type="cuda", cudatoolkit="10.0")
    ]

    for build_command in build_commands:
        build_string = " ".join(build_command.feedstock_args())
        assert "--working_directory {}".format(build_command.repository) in build_string
        if build_command.recipe:
            assert "--recipes {}".format(build_command.recipe) in build_string
        if build_command.channels:
            for channel in build_command.channels:
                assert "--channels {}".format(channel) in build_string
        if build_command.python:
            assert "--python_versions {}".format(build_command.python) in build_string
        if build_command.build_type:
            assert "--build_types {}".format(build_command.build_type) in build_string
        if build_command.mpi_type:
            assert "--mpi_types {}".format(build_command.mpi_type) in build_string
        if build_command.cudatoolkit:
            assert "--cuda_versions {}".format(build_command.cudatoolkit) in build_string

def test_clone_repo(mocker):
    '''
    Simple positive test for `_clone_repo`.
    '''
    git_location = utils.DEFAULT_GIT_LOCATION

    mock_build_tree = TestBuildTree([], "3.6", "cpu", "openmpi", "10.2")

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
    mock_build_tree = TestBuildTree([], "3.6", "cpu", "openmpi", "10.2")

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
                                    cudatoolkit="10.2",
                                    build_command_dependencies=[1,2]),
                         build_tree.BuildCommand("recipe2",
                                    "repo2",
                                    ["package2a"],
                                    python="2.6",
                                    build_type="cpu",
                                    mpi_type="openmpi",
                                    cudatoolkit="10.2",
                                    build_command_dependencies=[]),
                         build_tree.BuildCommand("recipe3",
                                    "repo3",
                                    ["package3a", "package3b"],
                                    build_command_dependencies=[1])]

def test_get_dependency_names():
    '''
    Tests that the dependency names can be retrieved for each item in a BuildTree
    '''
    mock_build_tree = TestBuildTree([], "3.6", "cpu", "openmpi", "10.2")
    mock_build_tree.build_commands = sample_build_commands

    output = ""
    for build_command in mock_build_tree:
        output += ' '.join([mock_build_tree[dep].name() for dep in build_command.build_command_dependencies]) + "\n"

    expected_output = "\nrecipe2-py2-6-cpu-openmpi-10-2\nrecipe2-py2-6-cpu-openmpi-10-2 recipe3\n"

    assert output == expected_output

def test_build_tree_len():
    '''
    Tests that the __len__ function works for BuildTree
    '''
    mock_build_tree = TestBuildTree([], "3.6", "cpu", "openmpi", "10.2")
    mock_build_tree.build_commands = sample_build_commands

    assert len(mock_build_tree) == 3

def test_build_tree_cycle_fail():
    '''
    Tests that a cycle is detected in a build_tree.
    '''
    cycle_build_commands = [build_tree.BuildCommand("recipe1",
                                                    "repo1",
                                                    ["package1a", "package1b"],
                                                    python="2.6",
                                                    build_type="cuda",
                                                    mpi_type="openmpi",
                                                    cudatoolkit="10.2",
                                                    build_command_dependencies=[1,2]),
                            build_tree.BuildCommand("recipe2",
                                                    "repo2",
                                                    ["package2a"],
                                                    python="2.6",
                                                    build_type="cpu",
                                                    mpi_type="openmpi",
                                                    cudatoolkit="10.2",
                                                    build_command_dependencies=[0]),
                            build_tree.BuildCommand("recipe3",
                                                    "repo3",
                                                    ["package3a", "package3b"],
                                                    build_command_dependencies=[1])]

    mock_build_tree = TestBuildTree([], "3.6", "cpu", "openmpi", "10.2")
    mock_build_tree.build_commands = sample_build_commands

    mock_build_tree._detect_cycle() #Make sure there isn't a false positive.

    mock_build_tree.build_commands = cycle_build_commands

    with pytest.raises(OpenCEError) as exc:
        mock_build_tree._detect_cycle()

    assert "Build dependencies should form a Directed Acyclic Graph." in str(exc.value)
    assert "recipe1 -> recipe2 -> recipe1" in str(exc.value)
    assert "recipe1 -> recipe3 -> recipe2 -> recipe1" in str(exc.value)
    assert "recipe2 -> recipe1 -> recipe3 -> recipe2" in str(exc.value)
    assert "recipe3 -> recipe2 -> recipe1 -> recipe2" in str(exc.value)

def test_build_tree_duplicates():
    '''
    Tests that `build_tree._remove_duplicate_build_commands` removes duplicate build_commands
    and updates the `build_command_dependencies` accordingly.
    '''

    initial_build_commands = [build_tree.BuildCommand("recipe1",
                                                    "repo1",
                                                    ["package1a"],
                                                    python="2.6",
                                                    build_type="cuda",
                                                    mpi_type="openmpi",
                                                    build_command_dependencies=[],
                                                    run_dependencies=[],
                                                    build_dependencies=[],
                                                    host_dependencies=[],
                                                    test_dependencies=[]),
                              build_tree.BuildCommand("recipe2",
                                                    "repo2",
                                                    ["package2a"],
                                                    python="2.6",
                                                    build_type="cuda",
                                                    mpi_type="openmpi",
                                                    build_command_dependencies=[0],
                                                    run_dependencies=[],
                                                    build_dependencies=[],
                                                    host_dependencies=[],
                                                    test_dependencies=[])]

    duplicate_build_commands = [build_tree.BuildCommand("recipe2",
                                                    "repo2",
                                                    ["package2a"],
                                                    python="2.6",
                                                    build_type="cuda",
                                                    mpi_type="openmpi",
                                                    build_command_dependencies=[],
                                                    run_dependencies=[],
                                                    build_dependencies=[],
                                                    host_dependencies=[],
                                                    test_dependencies=[]),

                                build_tree.BuildCommand("recipe1",
                                                    "repo1",
                                                    ["package1a"],
                                                    python="2.6",
                                                    build_type="cuda",
                                                    mpi_type="openmpi",
                                                    build_command_dependencies=[],
                                                    run_dependencies=[],
                                                    build_dependencies=[],
                                                    host_dependencies=[],
                                                    test_dependencies=[]),

                                build_tree.BuildCommand("recipe3",
                                                    "repo3",
                                                    ["package3a"],
                                                    python="2.6",
                                                    build_type="cpu",
                                                    mpi_type="openmpi",
                                                    build_command_dependencies=[1],
                                                    run_dependencies=[],
                                                    build_dependencies=["package1a"],
                                                    host_dependencies=[],
                                                    test_dependencies=[])]
    additional_build_commands = [build_tree.BuildCommand("recipe4",
                                                    "repo4",
                                                    ["package4a"],
                                                    python="2.6",
                                                    build_type="cpu",
                                                    mpi_type="openmpi",
                                                    build_command_dependencies=[],
                                                    run_dependencies=[],
                                                    build_dependencies=[],
                                                    host_dependencies=[],
                                                    test_dependencies=[])]
                               
    out_commands = build_tree._add_build_command_dependencies(additional_build_commands,initial_build_commands,len(initial_build_commands))
    assert len(out_commands)==1  # Make sure the non-duplicates are not removed

    out_commands = build_tree._add_build_command_dependencies(duplicate_build_commands, initial_build_commands, len(initial_build_commands))
    assert len(out_commands)==1

    for build_command in out_commands:
        assert build_command.build_command_dependencies == [0]
