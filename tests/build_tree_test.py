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

import os
from collections import Counter
import pathlib
import pytest
import networkx

test_dir = pathlib.Path(__file__).parent.absolute()

import open_ce.build_tree as build_tree
import open_ce.utils as utils
import open_ce.env_config as env_config
from open_ce.errors import OpenCEError
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
                 git_tag_for_env=utils.DEFAULT_GIT_TAG,
                 git_up_to_date = False,
                 conda_build_config=utils.DEFAULT_CONDA_BUILD_CONFIG):
        self._env_config_files = env_config_files
        self._repository_folder = repository_folder
        self._git_location = git_location
        self._git_tag_for_env = git_tag_for_env
        self._git_up_to_date = git_up_to_date
        self._conda_build_config = conda_build_config
        self._possible_variants = utils.make_variants(python_versions, build_types, mpi_types, cuda_versions)
        self._test_feedstocks = dict()
        self._initial_package_indices = None

def test_create_commands(mocker):
    '''
    Tests that `_create_commands` correctly builds the recipe and extracts all
    of the dependencies from the conda_build render result.
    '''
    dir_tracker = helpers.DirTracker()
    mocker.patch(
        'os.getcwd',
        return_value="/test/starting_dir"
    )
    render_result=helpers.make_render_result("horovod", ['build_req1', 'build_req2            1.2'],
                                                        ['run_req1            1.3'],
                                                        ['Host_req1            1.0', 'host_req2'],
                                                        ['test_req1'],
                                                        ['string1_1'])
    mocker.patch(
        'conda_build.api.render',
        return_value=render_result
    )
    mocker.patch(
        'conda_build.api.get_output_file_paths',
         return_value=['/output/path/linux/horovod.tar.gz']
    )
    mocker.patch(
        'os.chdir',
        side_effect=(lambda x: dir_tracker.validate_chdir(x, expected_dirs=["/test/my_repo", # First the working directory should be changed to the arg.
                                                                           "/test/starting_dir"])) # And then changed back to the starting directory.
    )

    build_commands = [x.build_command for x in build_tree._create_commands("/test/my_repo", "True", "my_recipe_path", None, "main", {'python' : '3.6', 'build_type' : 'cuda', 'mpi_type' : 'openmpi', 'cudatoolkit' : '10.2'}, []).nodes()]
    assert build_commands[0].packages == ['horovod']
    assert build_commands[0].recipe_path == "my_recipe_path"
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

    mock_build_tree = TestBuildTree([], "3.6", "cpu", "openmpi", "10.2", git_tag_for_env="main")

    dir_tracker= helpers.DirTracker()
    mocker.patch(
        'os.getcwd',
        side_effect=dir_tracker.mocked_getcwd
    )
    mocker.patch(
        'os.chdir',
        side_effect=dir_tracker.validate_chdir
    )
    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, possible_expect=["git clone",
                                                               git_location + "/my_repo.git",
                                                               "/test/my_repo", "git checkout main"]))
    )

    mock_build_tree._clone_repo(git_location + "/my_repo.git", "/test/my_repo", None, None)

def test_get_repo_git_tag_options(mocker, capsys):
    '''
    Test for `_get_repo` that verifies `git_tag` and `git_tag_for_env` priorities.
    '''
    env_file1 = os.path.join(test_dir, 'test-env1.yaml')
    mock_build_tree = TestBuildTree([env_file1], "3.6", "cpu", "openmpi", "10.2")

    dir_tracker= helpers.DirTracker()
    mocker.patch(
        'os.getcwd',
        side_effect=dir_tracker.mocked_getcwd
    )
    mocker.patch(
        'os.chdir',
        side_effect=dir_tracker.validate_chdir
    )
    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, possible_expect=["git clone", "git checkout"]))
    )

    possible_variants = utils.make_variants("3.6", "cpu", "openmpi", "10.2")
    for variant in possible_variants:

        # test-env1.yaml has defined "git_tag" and "git_tag_for_env".
        env_config_data_list = env_config.load_env_config_files([env_file1], variant)
        for env_config_data in env_config_data_list:
            packages = env_config_data.get(env_config.Key.packages.name, [])
            for package in packages:
                _ = mock_build_tree._get_repo(env_config_data, package)
                validate_git_tags(mock_build_tree._git_tag_for_env, env_config_data, package, capsys)

        # Setting git_tag_for_env in BuildTree should override whatever is in the config file
        mock_build_tree._git_tag_for_env = "test_tag_for_all"
        env_config_data_list = env_config.load_env_config_files([env_file1], variant)
        for env_config_data in env_config_data_list:
            packages = env_config_data.get(env_config.Key.packages.name, [])
            for package in packages:
                _ = mock_build_tree._get_repo(env_config_data, package)
                validate_git_tags(mock_build_tree._git_tag_for_env, env_config_data, package, capsys)

        # Setting git_tag_for_env in BuildTree back to Default and no git tags
        # specified in the config file too.
        mocker.patch(
            'os.system',
            return_value=0,
            side_effect=(lambda x: helpers.validate_cli(x, possible_expect=["git clone", "git apply"], reject=["git checkout"]))
        )

        mock_build_tree._git_tag_for_env = None
        env_file2 = os.path.join(test_dir, 'test-env3.yaml')
        env_config_data_list = env_config.load_env_config_files([env_file2], variant)
        for env_config_data in env_config_data_list:
            packages = env_config_data.get(env_config.Key.packages.name, [])
            for package in packages:
                _ = mock_build_tree._get_repo(env_config_data, package)
                validate_git_tags(mock_build_tree._git_tag_for_env, env_config_data, package, capsys)

def test_get_repo_with_patches(mocker, capsys):
    '''
    Test for `_get_repo` that verifies `patches` field
    '''
    env_file = os.path.join(test_dir, 'test-env3.yaml')
    mock_build_tree = TestBuildTree([env_file], "3.6", "cpu", "openmpi", "10.2")

    dir_tracker= helpers.DirTracker()
    mocker.patch(
        'os.getcwd',
        side_effect=dir_tracker.mocked_getcwd
    )
    mocker.patch(
        'os.chdir',
        side_effect=dir_tracker.validate_chdir
    )

    mocker.patch(
        'os.system',
        return_value=0,
        side_effect=(lambda x: helpers.validate_cli(x, expect=["git apply"], ignore=["git clone", "git checkout"]))
    )

    possible_variants = utils.make_variants("3.6", "cpu", "openmpi", "10.2")
    for variant in possible_variants:
        # test-env3.yaml has specified "patches".
        env_config_data_list = env_config.load_env_config_files([env_file], variant)
        for env_config_data in env_config_data_list:
            packages = env_config_data.get(env_config.Key.packages.name, [])
            for package in packages:

                if package.get(env_config.Key.feedstock.name) == "package22":
                    _ = mock_build_tree._get_repo(env_config_data, package)
                    captured = capsys.readouterr()
                    assert "Patch apply command:  git apply" in captured.out
                    break

def test_get_repo_for_nonexisting_patch(mocker):
    '''
    Test for `_get_repo` that verifies exception is thrown when patch application fails
    '''
    env_file = os.path.join(test_dir, 'test-env3.yaml')
    mock_build_tree = TestBuildTree([env_file], "3.6", "cpu", "openmpi", "10.2")

    dir_tracker= helpers.DirTracker()
    mocker.patch(
        'os.getcwd',
        side_effect=dir_tracker.mocked_getcwd
    )
    mocker.patch(
        'os.chdir',
        side_effect=dir_tracker.validate_chdir
    )
    mocker.patch(
        'os.system',
        side_effect=(lambda x: helpers.validate_cli(x, expect=["git apply"], ignore=["git clone", "git checkout"], retval=1))
    )

    possible_variants = utils.make_variants("3.6", "cpu", "openmpi", "10.2")
    for variant in possible_variants:
        # test-env3.yaml has defined "patches".
        env_config_data_list = env_config.load_env_config_files([env_file], variant)
        for env_config_data in env_config_data_list:
            packages = env_config_data.get(env_config.Key.packages.name, [])
            for package in packages:

                # "package211" has specified a non-existing patch
                if package.get(env_config.Key.feedstock.name) == "package211":
                    with pytest.raises(OpenCEError) as exc:
                        _ = mock_build_tree._get_repo(env_config_data, package)
                    assert "Failed to apply patch " in str(exc.value)

def validate_git_tags(git_tag_for_env, env_config_data, package, capsys):
    '''
    Validation function for git tag being used for each feedstock. Note, this logic depends
    on logic used in code to decide which git_tag to be used. If that changes, this also needs
    to be updated.
    '''
    captured = capsys.readouterr()
    git_branch = git_tag_for_env
    if not git_branch:
        git_branch = package.get(env_config.Key.git_tag.name, None)
    if not git_branch:
        git_branch = env_config_data.get(env_config.Key.git_tag_for_env.name, None)

    print(captured.out)

    assert "Clone cmd:  git clone" in captured.out
    if git_branch:
        assert "Checkout branch/tag command:  git checkout {}".format(git_branch) in captured.out

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
        mock_build_tree._clone_repo("https://bad_url", "/test/my_repo", None, None)
    assert "Unable to clone repository" in str(exc.value)

def test_check_runtime_package_field():
    '''
    Test for `runtime_package` field
    '''
    env_file = os.path.join(test_dir, 'test-env3.yaml')

    possible_variants = utils.make_variants("3.6", "cpu", "openmpi", "10.2")
    for variant in possible_variants:

        # test-env3.yaml has defined "runtime_package" for "package222".
        env_config_data_list = env_config.load_env_config_files([env_file], variant)
        for env_config_data in env_config_data_list:
            packages = env_config_data.get(env_config.Key.packages.name, [])
            for package in packages:
                if package.get(env_config.Key.feedstock.name) == "package222":
                    assert package.get(env_config.Key.runtime_package.name) == False

def test_check_recipe_path_package_field():
    '''
    Test for `runtime_package` field
    '''
    env_file = os.path.join(test_dir, 'test-env1.yaml')

    possible_variants = utils.make_variants("3.6", "cpu", "openmpi", "10.2")
    for variant in possible_variants:

        # test-env1.yaml has defined "recipe_path" as "package11_recipe_path" for "package11".
        env_config_data_list = env_config.load_env_config_files([env_file], variant)
        for env_config_data in env_config_data_list:
            packages = env_config_data.get(env_config.Key.packages.name, [])
            for package in packages:
                if package.get(env_config.Key.feedstock.name) == "package11":
                    assert package.get(env_config.Key.recipe_path.name) == "package11_recipe_path"

def sample_build_commands() :
    retval = networkx.DiGraph()
    node1 = build_tree.DependencyNode(packages=["package1a", "package1b"], build_command=build_tree.BuildCommand("recipe1",
                                                                                                                 "repo1",
                                                                                                                 ["package1a", "package1b"],
                                                                                                                 python="2.6",
                                                                                                                 build_type="cuda",
                                                                                                                 mpi_type="openmpi",
                                                                                                                 cudatoolkit="10.2"))
    node2 = build_tree.DependencyNode(packages=["package2a"], build_command=build_tree.BuildCommand("recipe2",
                                                                                                    "repo2",
                                                                                                    ["package2a"],
                                                                                                    python="2.6",
                                                                                                    build_type="cpu",
                                                                                                    mpi_type="openmpi",
                                                                                                    cudatoolkit="10.2"))
    node3 = build_tree.DependencyNode(packages=["package3a", "package3b"], build_command=build_tree.BuildCommand("recipe3",
                                                                                                                 "repo3",
                                                                                                                 ["package3a", "package3b"]))

    retval.add_node(node1)
    retval.add_node(node2)
    retval.add_node(node3)
    retval.add_edge(node1, node2)
    retval.add_edge(node1, node3)
    retval.add_edge(node3, node2)

    return retval

def test_get_dependency_names():
    '''
    Tests that the dependency names can be retrieved for each item in a BuildTree
    '''
    mock_build_tree = TestBuildTree([], "3.6", "cpu", "openmpi", "10.2")
    mock_build_tree._tree = sample_build_commands()

    output = ""
    for node in build_tree.traverse_build_commands(mock_build_tree._tree, return_node=True):
        output += ' '.join(dep.build_command.name() for dep in mock_build_tree._tree.successors(node)) + "\n"

    expected_output = "\nrecipe2-py2-6-cpu-openmpi-10-2\nrecipe2-py2-6-cpu-openmpi-10-2 recipe3\n"

    assert output == expected_output

def test_build_tree_len():
    '''
    Tests that the __len__ function works for BuildTree
    '''
    mock_build_tree = TestBuildTree([], "3.6", "cpu", "openmpi", "10.2")
    mock_build_tree._tree = sample_build_commands()

    assert len(mock_build_tree) == 3

def test_build_tree_cycle_fail():
    '''
    Tests that a cycle is detected in a build_tree.
    '''
    cycle_build_commands = networkx.DiGraph()
    node1 = build_tree.DependencyNode(packages=["package1a", "package1b"], build_command=build_tree.BuildCommand("recipe1",
                                                                                                                 "repo1",
                                                                                                                 ["package1a", "package1b"],
                                                                                                                 python="2.6",
                                                                                                                 build_type="cuda",
                                                                                                                 mpi_type="openmpi",
                                                                                                                 cudatoolkit="10.2"))
    node2 = build_tree.DependencyNode(packages=["package2a"], build_command=build_tree.BuildCommand("recipe2",
                                                                                                    "repo2",
                                                                                                    ["package2a"],
                                                                                                    python="2.6",
                                                                                                    build_type="cpu",
                                                                                                    mpi_type="openmpi",
                                                                                                    cudatoolkit="10.2"))
    node3 = build_tree.DependencyNode(packages=["package3a", "package3b"], build_command=build_tree.BuildCommand("recipe3",
                                                                                                                 "repo3",
                                                                                                                 ["package3a", "package3b"]))

    cycle_build_commands.add_node(node1)
    cycle_build_commands.add_node(node2)
    cycle_build_commands.add_node(node3)
    cycle_build_commands.add_edge(node1, node2)
    cycle_build_commands.add_edge(node1, node3)
    cycle_build_commands.add_edge(node2, node1)
    cycle_build_commands.add_edge(node3, node2)

    mock_build_tree = TestBuildTree([], "3.6", "cpu", "openmpi", "10.2")
    mock_build_tree._tree = sample_build_commands()

    mock_build_tree._detect_cycle() #Make sure there isn't a false positive.

    mock_build_tree._tree = cycle_build_commands

    with pytest.raises(OpenCEError) as exc:
        mock_build_tree._detect_cycle()

    assert "Build dependencies should form a Directed Acyclic Graph." in str(exc.value)
    assert any(["recipe1 -> recipe2 -> recipe1" in str(exc.value),
                "recipe2 -> recipe1 -> recipe2" in str(exc.value),
                "recipe1 -> recipe3 -> recipe2 -> recipe1" in str(exc.value),
                "recipe2 -> recipe1 -> recipe3 -> recipe2" in str(exc.value),
                "recipe3 -> recipe2 -> recipe1 -> recipe2" in str(exc.value)])

def test_get_installable_package_for_non_runtime_package():
    '''
    Tests that `get_installable_package` doesn't return the packages marked as
    non-runtime i.e. build command with runtime_package=False.
    '''
    build_commands = networkx.DiGraph()
    node1 = build_tree.DependencyNode(packages=["package1a"], build_command=build_tree.BuildCommand("recipe1",
                                                                                                                "repo1",
                                                                                                                ["package1a"],
                                                                                                                runtime_package=False,
                                                                                                                python="2.6",
                                                                                                                build_type="cuda",
                                                                                                                mpi_type="openmpi",
                                                                                                                cudatoolkit="10.2"))
    node2 = build_tree.DependencyNode(packages=["package2a"], build_command=build_tree.BuildCommand("recipe2",
                                                                                                    "repo2",
                                                                                                    ["package2a"],
                                                                                                    python="2.6",
                                                                                                    build_type="cpu",
                                                                                                    mpi_type="openmpi",
                                                                                                    cudatoolkit="10.2"))

    build_commands.add_node(node1)
    build_commands.add_node(node2)
    build_commands.add_edge(node1, node2)

    external_deps = ["external_pac1    1.2", "external_pack2", "external_pack3=1.2.3"]
    packages = build_tree.get_installable_packages(build_commands, external_deps)
    assert not "package1a" in packages

def test_get_installable_package_with_no_duplicates():
    '''
    This test verifies that get_installable_package doesn't return duplicate dependencies.
    '''
    build_commands = networkx.DiGraph()
    node1 = build_tree.DependencyNode(packages=["package1a"], build_command=build_tree.BuildCommand("recipe1",
                                                                                                    "repo1",
                                                                                                    ["package1a"],
                                                                                                    runtime_package=False,
                                                                                                    run_dependencies=["python 3.7", "pack1a==1.0"]))
    node2 = build_tree.DependencyNode(packages=["package2a"], build_command=build_tree.BuildCommand("recipe2",
                                                                                                    "repo2",
                                                                                                    ["package2a"],
                                                                                                    run_dependencies=["python 3.7", "pack1 ==1.0", "pack1", "pack2 <=2.0",
                                                                                                    "pack2 2.0", "pack3   3.0.*", "pack2"]))
    node3 = build_tree.DependencyNode(packages=["package3a", "package3b"], build_command=build_tree.BuildCommand("recipe3",
                                                                                                                "repo3",
                                                                                                                ["package3a", "package3b"],
                                                                                                                run_dependencies=["pack1 >=1.0", "pack1", "pack4 <=2.0",
                                                                                                                "pack2 2.0", "pack3   3.0.*", "pack4"]))

    build_commands.add_node(node1)
    build_commands.add_node(node2)
    build_commands.add_node(node3)

    external_deps = ["external_pac1    1.2"]
    packages = build_tree.get_installable_packages(build_commands, external_deps)
    assert not "package1a" in packages
    assert not "pack1a" in packages

    print("Packages: ", packages)

    expected_packages = ["package2a", "python 3.7.*", "pack1 ==1.0.*", "pack2 <=2.0", "pack3 3.0.*",
                         "package3a", "package3b", "pack4 <=2.0", "external_pac1 1.2.*"]
    assert Counter(packages) == Counter(expected_packages)

def test_get_build_copmmand_dependencies():
    mock_build_tree = TestBuildTree([], "3.6", "cpu", "openmpi", "10.2")
    mock_build_tree._initial_nodes = []
    mock_build_tree._tree = sample_build_commands()
    results = [mock_build_tree.build_command_dependencies(node) for node in mock_build_tree.BuildNodes()]
    assert "" in results
    assert "'recipe2-py2-6-cpu-openmpi-10-2'" in results
    assert "'recipe2-py2-6-cpu-openmpi-10-2', 'recipe3'" in results or "'recipe3', 'recipe2-py2-6-cpu-openmpi-10-2'" in results
