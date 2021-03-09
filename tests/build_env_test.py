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
import pathlib
import pytest
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

test_dir = pathlib.Path(__file__).parent.absolute()

spec = spec_from_loader("opence", SourceFileLoader("opence", os.path.join(test_dir, '..', 'open_ce', 'open-ce')))
opence = module_from_spec(spec)
spec.loader.exec_module(opence)

import helpers
import open_ce.build_env as build_env
import open_ce.utils as utils
from open_ce.errors import OpenCEError
from build_tree_test import TestBuildTree
import open_ce.test_feedstock as test_feedstock

class PackageBuildTracker(object):
    def __init__(self):
        self.built_packages = set()

    def validate_build_feedstock(self, build_command, package_deps = None, conditions=None):
        '''
        Used to mock the `build_feedstock` function and ensure that packages are built in a valid order.
        '''
        if package_deps:
            self.built_packages = self.built_packages.union(build_command.packages)
            for package in build_command.packages:
                for dependency in package_deps[package]:
                    assert dependency in self.built_packages
        if conditions:
            for condition in conditions:
                assert condition(build_command)

def test_build_env(mocker, capsys):
    '''
    This is a complete test of `build_env`.
    It uses `test-env2.yaml` which has a dependency on `test-env1.yaml`, and specifies a chain of package dependencies.
    That chain of package dependencies is used by the mocked build_feedstock to ensure that the order of builds is correct.
    '''
    dirTracker = helpers.DirTracker()
    mocker.patch(
        'os.system',
        side_effect=(lambda x: helpers.validate_cli(x, possible_expect=["git clone", "git checkout"], retval=0)) #At this point all system calls are git clones. If that changes this should be updated.
    )
    mocker.patch(
        'os.getcwd',
        side_effect=dirTracker.mocked_getcwd
    )
    mocker.patch(
        'os.chdir',
        side_effect=dirTracker.validate_chdir
    )
    mocker.patch(
        'open_ce.validate_config.validate_build_tree'
    )
    #            +-------+
    #     +------+   15  +-----+
    #     |      +---+---+     |     +-------+
    # +---v---+      |         +----->  16   |
    # |   11  |      |               +---+---+
    # +----+--+      |                   |
    #      |         |     +-------+     |
    #      |         +----->   14  <-----+
    #      |               +-+-----+
    #  +---v---+             |
    #  |  12   |             |
    #  +--+----+             |
    #     |            +-----v--+
    #     +------------>   13   |
    #                  +---+----+
    #                      |
    #                 +----v----+
    #                 |   21    |
    #                 +---------+
    package_deps = {"package11": ["package15"],
                    "package12": ["package11"],
                    "package13": ["package12", "package14"],
                    "package14": ["package15", "package16"],
                    "package15": [],
                    "package16": ["package15"],
                    "package21": ["package13"],
                    "package22": ["package15"]}
    #---The first test specifies a python version that isn't supported in the env file by package21.
    mocker.patch(
        'conda_build.api.render',
        side_effect=(lambda path, *args, **kwargs: helpers.mock_renderer(os.getcwd(), package_deps))
    )
    mocker.patch(
        'conda_build.api.get_output_file_paths',
        side_effect=(lambda meta, *args, **kwargs: helpers.mock_get_output_file_paths(meta))
    )

    py_version = "2.0"
    buildTracker = PackageBuildTracker()
    mocker.patch( # This ensures that 'package21' is not built when the python version is 2.0.
        'open_ce.build_feedstock.build_feedstock_from_command',
        side_effect=(lambda x, *args, **kwargs: buildTracker.validate_build_feedstock(x, package_deps,
                     conditions=[(lambda command: command.python == py_version),
                                 (lambda command: command.recipe != "package21-feedstock")]))
    )

    env_file = os.path.join(test_dir, 'test-env2.yaml')
    opence._main(["build", build_env.COMMAND, env_file, "--python_versions", py_version, "--run_tests"])
    validate_conda_env_files(py_version)

    #---The second test specifies a python version that is supported in the env file by package21.
    py_version = "2.1"
    channel = "my_channel"
    package_deps = {"package11": ["package15"],
                    "package12": ["package11"],
                    "package13": ["package12", "package14"],
                    "package14": ["package15", "package16"],
                    "package15": [],
                    "package16": ["package15"],
                    "package21": ["package13"],
                    "package22": ["package21"]}
    mocker.patch(
        'conda_build.api.render',
        side_effect=(lambda path, *args, **kwargs: helpers.mock_renderer(os.getcwd(), package_deps))
    )
    buildTracker = PackageBuildTracker()
    mocker.patch(
        'open_ce.build_feedstock.build_feedstock_from_command',
        side_effect=(lambda x, *args, **kwargs: buildTracker.validate_build_feedstock(x, package_deps,
                     conditions=[(lambda command: command.python == py_version and channel in command.channels)]))
    )

    env_file = os.path.join(test_dir, 'test-env2.yaml')
    opence._main(["build", build_env.COMMAND, env_file, "--python_versions", py_version, "--channels", channel])
    validate_conda_env_files(py_version)

    #---The third test verifies that the repository_folder argument is working properly.
    buildTracker = PackageBuildTracker()
    mocker.patch(
        'open_ce.build_feedstock.build_feedstock_from_command',
        side_effect=(lambda x, *args, **kwargs: buildTracker.validate_build_feedstock(x, package_deps,
                     conditions=[(lambda command: command.repository.startswith("repo_folder"))]))
    )
    py_version = "2.1"
    env_file = os.path.join(test_dir, 'test-env2.yaml')
    opence._main(["build", build_env.COMMAND, env_file, "--repository_folder", "repo_folder", "--python_versions", py_version])
    validate_conda_env_files(py_version)

    #---The fourth test verifies that builds are skipped properly if they already exist.
    mocker.patch(
        'open_ce.build_env._all_outputs_exist',
        return_value=True)

    captured = capsys.readouterr()
    opence._main(["build", build_env.COMMAND, env_file])
    captured = capsys.readouterr()
    assert "Skipping build of" in captured.out
    mocker.patch(
        'open_ce.build_env._all_outputs_exist',
        return_value=False)

    #---The fifth test specifies a cuda version that isn't supported in the env file by package21.
    mocker.patch(
        'conda_build.api.render',
        side_effect=(lambda path, *args, **kwargs: helpers.mock_renderer(os.getcwd(), package_deps))
    )
    mocker.patch(
        'conda_build.api.get_output_file_paths',
        side_effect=(lambda meta, *args, **kwargs: helpers.mock_get_output_file_paths(meta))
    )

    cuda_version = "9.1"
    package_deps = {"package11": ["package15"],
                    "package12": ["package11"],
                    "package13": ["package12", "package14"],
                    "package14": ["package15", "package16"],
                    "package15": [],
                    "package16": ["package15"],
                    "package21": ["package13"],
                    "package22": ["package15"]}
    buildTracker = PackageBuildTracker()
    mocker.patch( # This ensures that 'package21' is not built when the cuda version is 9.1
        'open_ce.build_feedstock.build_feedstock_from_command',
        side_effect=(lambda x, *args, **kwargs: buildTracker.validate_build_feedstock(x, package_deps,
                     conditions=[(lambda command: command.recipe != "package21-feedstock")]))
    )

    env_file = os.path.join(test_dir, 'test-env2.yaml')
    opence._main(["build", build_env.COMMAND, env_file, "--cuda_versions", cuda_version, "--run_tests"])
    validate_conda_env_files(cuda_versions=cuda_version)

    #---The sixth test specifies a cuda version that is supported in the env file by package21.
    cuda_version = "9.2"
    package_deps = {"package11": ["package15"],
                    "package12": ["package11"],
                    "package13": ["package12", "package14"],
                    "package14": ["package15", "package16"],
                    "package15": [],
                    "package16": ["package15"],
                    "package21": ["package13"],
                    "package22": ["package21"]}
    mocker.patch(
        'conda_build.api.render',
        side_effect=(lambda path, *args, **kwargs: helpers.mock_renderer(os.getcwd(), package_deps))
    )
    buildTracker = PackageBuildTracker()
    mocker.patch(
        'open_ce.build_feedstock.build_feedstock_from_command',
        side_effect=(lambda x, *args, **kwargs: buildTracker.validate_build_feedstock(x, package_deps,
                     conditions=[(lambda command: command.cudatoolkit == cuda_version)]))
    )

    env_file = os.path.join(test_dir, 'test-env2.yaml')
    opence._main(["build", build_env.COMMAND, env_file, "--cuda_versions", cuda_version])
    validate_conda_env_files(cuda_versions=cuda_version)

    #---The seventh test specifies specific packages that should be built (plus their dependencies)
    package_deps = {"package11": ["package15"],
                    "package12": ["package11"],
                    "package13": ["package12", "package14"],
                    "package14": ["package15", "package16"],
                    "package15": [],
                    "package16": ["package15"],
                    "package21": ["package13"],
                    "package22": ["package21"]}
    mocker.patch(
        'conda_build.api.render',
        side_effect=(lambda path, *args, **kwargs: helpers.mock_renderer(os.getcwd(), package_deps))
    )
    buildTracker = PackageBuildTracker()
    mocker.patch(
        'open_ce.build_feedstock.build_feedstock_from_command',
        side_effect=(lambda x, *args, **kwargs: buildTracker.validate_build_feedstock(x, package_deps,
                     conditions=[(lambda command: not command.recipe in ["package11-feedstock",
                                                                         "package12-feedstock",
                                                                         "package13-feedstock",
                                                                         "package21-feedstock",
                                                                         "package22-feedstock"])]))
    )

    env_file = os.path.join(test_dir, 'test-env2.yaml')
    captured = capsys.readouterr()
    opence._main(["build", build_env.COMMAND, env_file, "--python_versions", py_version, "--packages", "package14,package35"])
    captured = capsys.readouterr()
    assert "No recipes were found for package35" in captured.out

    #---The eighth test makes sure that relative URL paths work.
    package_deps = {"package11": ["package15"],
                    "package12": ["package11"],
                    "package13": ["package12", "package14"],
                    "package14": ["package15", "package16"],
                    "package15": [],
                    "package16": ["package15"],
                    "package21": ["package13"],
                    "package22": ["package15"]}
    mocker.patch(
        'conda_build.api.render',
        side_effect=(lambda path, *args, **kwargs: helpers.mock_renderer(os.getcwd(), package_deps))
    )
    buildTracker = PackageBuildTracker()
    mocker.patch(
        'open_ce.build_feedstock.build_feedstock_from_command',
        side_effect=(lambda x, *args, **kwargs: buildTracker.validate_build_feedstock(x, package_deps))
    )
    mocker.patch(
        'urllib.request.urlretrieve',
        side_effect=(lambda x, filename=None: (os.path.join(test_dir, os.path.basename(x)), None))
    )

    env_file = 'https://test.com/test-env2.yaml'
    opence._main(["build", build_env.COMMAND, env_file])

def validate_conda_env_files(py_versions=utils.DEFAULT_PYTHON_VERS,
                             build_types=utils.DEFAULT_BUILD_TYPES,
                             mpi_types=utils.DEFAULT_MPI_TYPES,
                             cuda_versions=utils.DEFAULT_CUDA_VERS):
    # Check if conda env files are created for given python versions and build variants
    variants = utils.make_variants(py_versions, build_types, mpi_types, cuda_versions)
    for variant in variants:
        cuda_env_file = os.path.join(os.getcwd(), utils.DEFAULT_OUTPUT_FOLDER,
                                     "{}{}.yaml".format(utils.CONDA_ENV_FILENAME_PREFIX,
                                     utils.variant_string(variant['python'], variant['build_type'], variant['mpi_type'], variant['cudatoolkit'])))
        assert os.path.exists(cuda_env_file)
        # Remove the file once it's existence is verified
        os.remove(cuda_env_file)

def test_env_validate(mocker):
    '''
    This is a negative test of `build_env`, which passes an invalid env file.
    '''
    dirTracker = helpers.DirTracker()
    mocker.patch(
        'os.mkdir',
        return_value=0 #Don't worry about making directories.
    )
    mocker.patch(
        'os.system',
        side_effect=(lambda x: helpers.validate_cli(x, expect=["git clone"], retval=0)) #At this point all system calls are git clones. If that changes this should be updated.
    )
    mocker.patch(
        'os.getcwd',
        side_effect=dirTracker.mocked_getcwd
    )
    mocker.patch(
        'conda_build.api.render',
        side_effect=(lambda path, *args, **kwargs: helpers.mock_renderer(os.getcwd(), []))
    )
    mocker.patch(
        'os.chdir',
        side_effect=dirTracker.validate_chdir
    )
    buildTracker = PackageBuildTracker()
    mocker.patch(
        'open_ce.build_feedstock.build_feedstock',
        side_effect=buildTracker.validate_build_feedstock
    )
    env_file = os.path.join(test_dir, 'test-env-invalid1.yaml')
    with pytest.raises(OpenCEError) as exc:
        opence._main(["build", build_env.COMMAND, env_file])
    assert "Unexpected key chnnels was found in " in str(exc.value)

def test_build_env_container_build(mocker):
    '''
    Test that passing the --container_build argument calls container_build.build_with_container_tool
    '''
    arg_strings = ["build", build_env.COMMAND, "--container_build", "my-env.yaml"]

    mocker.patch('open_ce.container_build.build_with_container_tool', return_value=0)

    mocker.patch('pkg_resources.get_distribution', return_value=None)

    opence._main(arg_strings)

def test_build_env_container_build_multiple_cuda_versions():
    '''
    Tests that passing mutiple values in --cuda_versions argument with container_build fails.
    '''

    arg_strings = ["build", build_env.COMMAND, "--container_build",
                   "--cuda_versions", "10.2,11.0", "my-env.yaml"]

    with pytest.raises(OpenCEError) as exc:
        opence._main(arg_strings)
    assert "Only one cuda version" in str(exc.value)

def test_build_env_container_build_cuda_versions(mocker):
    '''
    Tests that passing --cuda_versions argument with container_build argument works correctly.
    '''
    dirTracker = helpers.DirTracker()
    mocker.patch(
        'os.getcwd',
        side_effect=dirTracker.mocked_getcwd
    )
    mocker.patch('open_ce.container_build.build_with_container_tool', return_value=0)

    cuda_version = "10.2"
    arg_strings = ["build", build_env.COMMAND, "--container_build",
                   "--cuda_versions", cuda_version, "my-env.yaml"]
    opence._main(arg_strings)
    validate_conda_env_files(cuda_versions=cuda_version)

def test_build_env_container_build_with_build_args(mocker):
    '''
    Tests that passing --container_build_args argument with container_build argument works correctly.
    '''
    dirTracker = helpers.DirTracker()
    mocker.patch(
        'os.getcwd',
        side_effect=dirTracker.mocked_getcwd
    )
    mocker.patch('open_ce.container_build.build_with_container_tool', return_value=0)

    # with docker_build 
    arg_strings = ["build", build_env.COMMAND, "--docker_build",
                   "--container_build_args", "--build-args ENV1=test1 some_setting=1", "my-env.yaml"]
    opence._main(arg_strings)

    # with container_build
    arg_strings = ["build", build_env.COMMAND, "--container_build",
                   "--container_build_args", "--build-args ENV1=test1 some_setting=1", "my-env.yaml"]
    opence._main(arg_strings)

def test_build_env_container_build_with_container_tool(mocker):
    '''
    Tests that passing --container_tool argument works correctly.
    '''
    dirTracker = helpers.DirTracker()
    mocker.patch(
        'os.getcwd',
        side_effect=dirTracker.mocked_getcwd
    )
    mocker.patch('open_ce.container_build.build_with_container_tool', return_value=0)

    #with docker_build argument
    arg_strings = ["build", build_env.COMMAND, "--docker_build",
                   "--container_tool", "podman", "my-env.yaml"]
    opence._main(arg_strings)

    #with container_build argument
    arg_strings = ["build", build_env.COMMAND, "--container_build",
                   "--container_tool", "podman", "my-env.yaml"]
    opence._main(arg_strings)

def test_build_env_if_no_conda_build(mocker):
    '''
    Test that build_env should fail if conda_build isn't present and no --container_build
    '''
    arg_strings = ["build", build_env.COMMAND, "my-env.yaml"]

    mocker.patch('pkg_resources.get_distribution', return_value=None)
    with pytest.raises(OpenCEError):
        opence._main(arg_strings)

def test_run_tests(mocker):
    '''
    Test that the _run_tests function works properly.
    '''
    dirTracker = helpers.DirTracker()
    mock_build_tree = TestBuildTree([], "3.6", "cpu,cuda", "openmpi", "10.2")
    mock_test_commands = [test_feedstock.TestCommand("Test1",
                                                      conda_env="test-conda-env2.yaml",
                                                      bash_command="echo Test1"),
                          test_feedstock.TestCommand("Test2",
                                                      conda_env="test-conda-env2.yaml",
                                                      bash_command="[ 1 -eq 2 ]")]

    mocker.patch("open_ce.test_feedstock.gen_test_commands", return_value=mock_test_commands)
    mocker.patch(
        'os.chdir',
        side_effect=dirTracker.validate_chdir
    )
    conda_env_files = dict()
    mock_build_tree._test_commands = dict()

    for variant in mock_build_tree._possible_variants:
        conda_env_files[str(variant)] = "tests/test-conda-env2.yaml"
        mock_build_tree._test_feedstocks[str(variant)] = ["feedstock1"]

    # Note: All of the tests should fail, since there isn't a real conda environment to activate
    with pytest.raises(OpenCEError) as exc:
        build_env._run_tests(mock_build_tree, [], conda_env_files)
    assert "There were 4 test failures" in str(exc.value)

def test_build_env_url(mocker):
    '''
    This tests that if a URL is passed in for an env file that it is downloaded.
    I mock urlretrieve to return the test-env-invalid1.yaml file so that I can check
    for the invalid channels identifier, ensuring that the download function was called.
    '''
    dirTracker = helpers.DirTracker()
    mocker.patch(
        'os.mkdir',
        return_value=0 #Don't worry about making directories.
    )
    mocker.patch(
        'os.system',
        side_effect=(lambda x: helpers.validate_cli(x, expect=["git clone"], retval=0)) #At this point all system calls are git clones. If that changes this should be updated.
    )
    mocker.patch(
        'os.getcwd',
        side_effect=dirTracker.mocked_getcwd
    )
    mocker.patch(
        'conda_build.api.render',
        side_effect=(lambda path, *args, **kwargs: helpers.mock_renderer(os.getcwd(), []))
    )
    mocker.patch(
        'os.chdir',
        side_effect=dirTracker.validate_chdir
    )
    buildTracker = PackageBuildTracker()
    mocker.patch(
        'open_ce.build_feedstock.build_feedstock',
        side_effect=buildTracker.validate_build_feedstock
    )
    mocker.patch(
        'urllib.request.urlretrieve',
        side_effect=(lambda x, filename=None: (os.path.join(test_dir, os.path.basename(x)), None))
    )

    env_file = 'https://test.com/test-env-invalid1.yaml'
    with pytest.raises(OpenCEError) as exc:
        opence._main(["build", build_env.COMMAND, env_file])
    assert "Unexpected key chnnels was found in " in str(exc.value)
