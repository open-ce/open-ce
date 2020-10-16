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
from itertools import product
import pathlib
from collections import Counter

test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'open-ce'))

import build_tree
import conda_env_file_generator
import utils

class TestBuildTree(build_tree.BuildTree):
    '''
    Test class that inherits BuildTree class
    '''
    __test__ = False
    def __init__(self,
                 env_config_files,
                 python_versions,
                 build_types,
                 external_depends=dict(),
                 repository_folder="./",
                 git_location=utils.DEFAULT_GIT_LOCATION,
                 git_tag_for_env="master",
                 conda_build_config=utils.DEFAULT_CONDA_BUILD_CONFIG):
        self._env_config_files = env_config_files
        self._repository_folder = repository_folder
        self._git_location = git_location
        self._git_tag_for_env = git_tag_for_env
        self._conda_build_config = conda_build_config
        self._external_dependencies = external_depends

class TestCondaEnvFileGenerator(conda_env_file_generator.CondaEnvFileGenerator):
    '''
    Test class that inherits CondaEnvFileGenerator class
    '''
    __test__ = False
    def __init__(self,
                 python_versions,
                 build_types,
                 channels,
                 output_folder):
        super().__init__(python_versions, build_types, channels, output_folder)

sample_build_commands = [build_tree.BuildCommand("recipe1",
                                    "repo1",
                                    ["package1a", "package1b"],
                                    python="3.6",
                                    build_type="cuda",
                                    run_dependencies=["python     >=3.6", "pack1    1.0", "pack2   >=2.0"]),
                         build_tree.BuildCommand("recipe2",
                                    "repo2",
                                    ["package2a"],
                                    python="3.6",
                                    build_type="cpu",
                                    run_dependencies=["python ==3.6", "pack1 >=1.0", "pack2   ==2.0"]),
                         build_tree.BuildCommand("recipe3",
                                    "repo3",
                                    ["package3a", "package3b"],
                                    python="3.7",
                                    build_type="cpu",
                                    run_dependencies=["python 3.7", "pack1==1.0", "pack2 <=2.0", "pack3   3.0.*"]),
                         build_tree.BuildCommand("recipe4",
                                    "repo4",
                                    ["package4a", "package4b"],
                                    python="3.7",
                                    build_type="cuda",
                                    run_dependencies=["pack1==1.0", "pack2 <=2.0", "pack3-suffix 3.0"])]


external_deps = {}
variants = { 'python' : ['3.6', '3.7'], 'build_type' : ['cpu', 'cuda'] }
possible_variants = [dict(zip(variants,y)) for y in product(*variants.values())]
for variant in possible_variants:
    external_deps[str(variant)] = ["external_pac1    1.2", "external_pack2", "external_pack3=1.2.3"]
TMP_OPENCE_DIR="/tmp/opence-test/"

def test_conda_env_file_content():
    '''
    Tests that the conda env file content are being populated correctly
    '''
    python_versions = "3.6,3.7"
    build_types = "cpu,cuda"
    mock_build_tree = TestBuildTree([], python_versions, build_types, external_deps)
    mock_build_tree.build_commands = sample_build_commands

    output_dir = os.path.join(test_dir, '../condabuild' )
    mock_conda_env_file_generator = TestCondaEnvFileGenerator(python_versions,
                                                              build_types,
                                                              ["some channel"],
                                                              output_dir) 
    expected_channels = ["file:/{}".format(output_dir), "some channel", "defaults"]
    actual_channels = mock_conda_env_file_generator.channels
    assert actual_channels == expected_channels

    expected_keys = [utils.variant_key(py_vers, build_type) for py_vers in utils.parse_arg_list(python_versions)
                                                            for build_type in utils.parse_arg_list(build_types)]
    print("Expected keys: ", expected_keys)
    actual_keys = list(mock_conda_env_file_generator.dependency_dict.keys())
    assert Counter(actual_keys) == Counter(expected_keys)

    for build_command in mock_build_tree:
        mock_conda_env_file_generator.update_conda_env_file_content(build_command, mock_build_tree)

    validate_dependencies(mock_conda_env_file_generator, expected_keys)
    mock_conda_env_file_generator.write_conda_env_files(TMP_OPENCE_DIR)

    # Check if conda env files are created for both built types as no build type was specified above
    for py_version in utils.parse_arg_list(python_versions):
        for build_type in utils.parse_arg_list(build_types):
            cuda_env_file = os.path.join(TMP_OPENCE_DIR,
                            "{}{}.yaml".format(utils.CONDA_ENV_FILENAME_PREFIX,
                                               utils.variant_key(py_version, build_type)))
            assert os.path.exists(cuda_env_file)

    cleanup()
    assert not os.path.exists(TMP_OPENCE_DIR)

def validate_dependencies(env_file_generator, variant_keys):
    '''
    Validates the exact dependencies for each environment
    '''
    py36_cpu_deps = ["python ==3.6.*", "pack1 >=1.0", "pack2 ==2.0.*", "package2a",
                     "external_pac1 1.2.*", "external_pack2", "external_pack3=1.2.3.*"]
    actual_deps = env_file_generator.dependency_dict[variant_keys[0]]
    assert Counter(py36_cpu_deps) == Counter(actual_deps)

    py36_cuda_deps = ["python >=3.6", "pack1 1.0.*", "pack2 >=2.0", "package1a", "package1b",
                      "external_pac1 1.2.*", "external_pack2", "external_pack3=1.2.3.*"]
    actual_deps = env_file_generator.dependency_dict[variant_keys[1]]
    assert Counter(py36_cuda_deps) == Counter(actual_deps)

    py37_cpu_deps = ["python 3.7.*", "pack1==1.0.*", "pack2 <=2.0", "pack3 3.0.*", "package3a", "package3b",
                     "external_pac1 1.2.*", "external_pack2", "external_pack3=1.2.3.*"]
    actual_deps = env_file_generator.dependency_dict[variant_keys[2]]
    assert Counter(py37_cpu_deps) == Counter(actual_deps)

    py37_cuda_deps = ["pack1==1.0.*", "pack2 <=2.0", "pack3-suffix 3.0.*", "package4a", "package4b",
                      "external_pac1 1.2.*", "external_pack2", "external_pack3=1.2.3.*"]
    actual_deps = env_file_generator.dependency_dict[variant_keys[3]]
    assert Counter(py37_cuda_deps) == Counter(actual_deps)

def test_conda_env_file_for_only_selected_py():
    '''
    Tests that the conda env file is generated only for selected configurations.
    '''
    python_versions = "3.7"
    build_types = "cpu,cuda"
    mock_build_tree = TestBuildTree([], python_versions, build_types, external_deps)
    mock_build_tree.build_commands = sample_build_commands[2:4] # Build cmds for py3.7

    output_dir = os.path.join(test_dir, '../condabuild' )
    mock_conda_env_file_generator = TestCondaEnvFileGenerator(python_versions, build_types, None, output_dir)

    expected_channels = ["file:/{}".format(output_dir), "defaults"]
    actual_channels = mock_conda_env_file_generator.channels
    assert actual_channels == expected_channels

    expected_keys = [utils.variant_key(py_vers, build_type) for py_vers in utils.parse_arg_list(python_versions)
                                                            for build_type in utils.parse_arg_list(build_types)]

    actual_keys = list(mock_conda_env_file_generator.dependency_dict.keys())
    assert Counter(actual_keys) == Counter(expected_keys)

    for build_command in mock_build_tree:
        mock_conda_env_file_generator.update_conda_env_file_content(build_command, mock_build_tree)
 
    mock_conda_env_file_generator.write_conda_env_files(TMP_OPENCE_DIR)

    # Check if conda env files are created for both built types and single python version
    for py_version in utils.parse_arg_list(python_versions):
        for build_type in utils.parse_arg_list(build_types):
            cuda_env_file = os.path.join(TMP_OPENCE_DIR,
                                         "{}{}.yaml".format(utils.CONDA_ENV_FILENAME_PREFIX,
                                         utils.variant_key(py_version, build_type)))
            assert os.path.exists(cuda_env_file)

    # Check that no other env file exists other than the two expected ones
    for (_, _, files) in os.walk(TMP_OPENCE_DIR, topdown=True):
        assert len(files) == 2
 
    cleanup()
    assert not os.path.exists(TMP_OPENCE_DIR)

def test_conda_env_file_for_inapplicable_conf():
    '''
    Tests that the conda env file is not generated if build is triggered for
    inapplicable configurations. For e.g. cpu variant build is selected for cuda only
    packages like TensorRT
    '''
    python_versions = "3.7"
    build_types = "cuda"
    mock_build_tree = TestBuildTree([], python_versions, build_types)

    mock_build_tree.build_commands = [build_tree.BuildCommand("recipe1",
                                      "repo1",
                                      [], # packages is intentionally kept empty
                                      python="3.7",
                                      build_type="cuda",
                                      run_dependencies=None)]

    output_dir = os.path.join(test_dir, '../condabuild' )
    mock_conda_env_file_generator = TestCondaEnvFileGenerator(python_versions, build_types, [], output_dir)

    expected_keys = ["py3.7-cuda"]
    actual_keys = list(mock_conda_env_file_generator.dependency_dict.keys())
    assert actual_keys == expected_keys

    for build_command in mock_build_tree:
        mock_conda_env_file_generator.update_conda_env_file_content(build_command, mock_build_tree)

    mock_conda_env_file_generator.write_conda_env_files(TMP_OPENCE_DIR)

    # Check that no conda env file is created
    for (root, _, _) in os.walk(TMP_OPENCE_DIR, topdown=True):
        assert len(root) == 0

    cleanup()
    assert not os.path.exists(TMP_OPENCE_DIR)

def cleanup():
    '''
    Deletes the temp directory in which conda env files are created during tests
    '''
    os.system("rm -rf {}".format(TMP_OPENCE_DIR))
