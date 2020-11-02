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
                 mpi_types,
                 cuda_versions,
                 external_depends=None,
                 repository_folder="./",
                 git_location=utils.DEFAULT_GIT_LOCATION,
                 git_tag_for_env="master",
                 conda_build_config=utils.DEFAULT_CONDA_BUILD_CONFIG):
        super().__init__(env_config_files, python_versions, build_types, mpi_types,
                         cuda_versions, repository_folder, git_location, conda_build_config)
        if external_depends:
            self._external_dependencies = external_depends
        else:
            dict()

class TestCondaEnvFileGenerator(conda_env_file_generator.CondaEnvFileGenerator):
    '''
    Test class that inherits CondaEnvFileGenerator class
    '''
    __test__ = False
    def __init__(self,
                 python_versions,
                 build_types,
                 mpi_types,
                 cuda_versions,
                 channels,
                 output_folder):
        super().__init__(python_versions, build_types, mpi_types, cuda_versions, channels, output_folder)

sample_build_commands = [build_tree.BuildCommand("recipe1",
                                    "repo1",
                                    ["package1a", "package1b"],
                                    python="3.6",
                                    build_type="cuda",
                                    mpi_type="openmpi",
                                    cudatoolkit="10.2",
                                    run_dependencies=["python     >=3.6", "pack1    1.0", "pack2   >=2.0"]),
                         build_tree.BuildCommand("recipe2",
                                    "repo2",
                                    ["package2a"],
                                    python="3.6",
                                    build_type="cpu",
                                    mpi_type="system",
                                    cudatoolkit="10.2",                                    
                                    run_dependencies=["python ==3.6", "pack1 >=1.0", "pack2   ==2.0", "pack3 3.3 build"]),
                         build_tree.BuildCommand("recipe3",
                                    "repo3",
                                    ["package3a", "package3b"],
                                    python="3.7",
                                    build_type="cpu",
                                    mpi_type="openmpi",
                                    cudatoolkit="10.2",
                                    run_dependencies=["python 3.7", "pack1==1.0", "pack2 <=2.0", "pack3   3.0.*"]),
                         build_tree.BuildCommand("recipe4",
                                    "repo4",
                                    ["package4a", "package4b"],
                                    python="3.7",
                                    build_type="cuda",
                                    mpi_type="system",
                                    cudatoolkit="10.2",
                                    run_dependencies=["pack1==1.0", "pack2 <=2.0", "pack3-suffix 3.0"])]


external_deps = {}
possible_variants = utils.make_variants(['3.6', '3.7'], ['cpu', 'cuda'], 'openmpi', '10.2')
for variant in possible_variants:
    external_deps[str(variant)] = ["external_pac1    1.2", "external_pack2", "external_pack3=1.2.3"]
TMP_OPENCE_DIR="/tmp/opence-test/"

def test_conda_env_file_content():
    '''
    Tests that the conda env file content are being populated correctly
    '''
    python_versions = "3.6,3.7"
    build_types = "cpu,cuda"
    mpi_types = "openmpi,system"
    cuda_versions = "10.2"
    mock_build_tree = TestBuildTree([], python_versions, build_types, mpi_types, cuda_versions, external_deps)
    mock_build_tree.build_commands = sample_build_commands

    output_dir = os.path.join(test_dir, '../condabuild' )
    mock_conda_env_file_generator = TestCondaEnvFileGenerator(python_versions,
                                                              build_types,
                                                              mpi_types,
                                                              cuda_versions,
                                                              ["some channel"],
                                                              output_dir)
    expected_channels = ["file:/{}".format(output_dir), "some channel", "defaults"]
    actual_channels = mock_conda_env_file_generator.channels
    assert actual_channels == expected_channels

    variants = utils.make_variants(python_versions, build_types, mpi_types)
    expected_keys = [utils.variant_string(variant['python'], variant['build_type'], variant['mpi_type'], variant['cudatoolkit'])
                     for variant in variants]
    actual_keys = list(mock_conda_env_file_generator.dependency_dict.keys())
    assert Counter(actual_keys) == Counter(expected_keys)

    for build_command in mock_build_tree:
        mock_conda_env_file_generator.update_conda_env_file_content(build_command, mock_build_tree)

    files_generated_for_keys = []
    validate_dependencies(mock_conda_env_file_generator, expected_keys, files_generated_for_keys)
    mock_conda_env_file_generator.write_conda_env_files(TMP_OPENCE_DIR)

    # Check if conda env files are created for all variants
    for key in files_generated_for_keys:
        cuda_env_file = os.path.join(TMP_OPENCE_DIR,
                            "{}{}.yaml".format(utils.CONDA_ENV_FILENAME_PREFIX,
                                               key))
        assert os.path.exists(cuda_env_file)

    cleanup()
    assert not os.path.exists(TMP_OPENCE_DIR)

def validate_dependencies(env_file_generator, variant_keys, files_generated_for):
    '''
    Validates the exact dependencies for each environment
    '''
    py36_cpu_openmpi_deps = set()
    actual_deps = env_file_generator.dependency_dict[variant_keys[0]]
    assert Counter(py36_cpu_openmpi_deps) == Counter(actual_deps)

    py36_cpu_system_deps = ["python ==3.6.*", "pack1 >=1.0", "pack2 ==2.0.*", "package2a", "pack3 3.3.* build"]
    actual_deps = env_file_generator.dependency_dict[variant_keys[1]]
    assert Counter(py36_cpu_system_deps) == Counter(actual_deps)
    files_generated_for.append(variant_keys[1])

    py36_cuda_openmpi_deps = ["python >=3.6", "pack1 1.0.*", "pack2 >=2.0", "package1a", "package1b",
                      "external_pac1 1.2.*", "external_pack2", "external_pack3=1.2.3"]
    actual_deps = env_file_generator.dependency_dict[variant_keys[2]]
    assert Counter(py36_cuda_openmpi_deps) == Counter(actual_deps)
    files_generated_for.append(variant_keys[2])

    py36_cuda_system_deps = set()
    actual_deps = env_file_generator.dependency_dict[variant_keys[3]]
    assert Counter(py36_cuda_system_deps) == Counter(actual_deps)

    py37_cpu_openmpi_deps = ["python 3.7.*", "pack1==1.0.*", "pack2 <=2.0", "pack3 3.0.*", "package3a", "package3b",
                     "external_pac1 1.2.*", "external_pack2", "external_pack3=1.2.3"]
    actual_deps = env_file_generator.dependency_dict[variant_keys[4]]
    assert Counter(py37_cpu_openmpi_deps) == Counter(actual_deps)
    files_generated_for.append(variant_keys[4])

    py37_cpu_system_deps = set()
    actual_deps = env_file_generator.dependency_dict[variant_keys[5]]
    assert Counter(py37_cpu_system_deps) == Counter(actual_deps)

    py37_cuda_openmpi_deps = set()
    actual_deps = env_file_generator.dependency_dict[variant_keys[6]]
    assert Counter(py37_cuda_openmpi_deps) == Counter(actual_deps)

    py37_cuda_system_deps = ["pack1==1.0.*", "pack2 <=2.0", "pack3-suffix 3.0.*", "package4a", "package4b"]
    actual_deps = env_file_generator.dependency_dict[variant_keys[7]]
    assert Counter(py37_cuda_system_deps) == Counter(actual_deps)
    files_generated_for.append(variant_keys[7])

def test_conda_env_file_for_only_selected_py():
    '''
    Tests that the conda env file is generated only for selected configurations.
    '''
    python_versions = "3.7"
    build_types = "cpu,cuda"
    mpi_types = "openmpi,system"
    cuda_versions = "10.2"
    mock_build_tree = TestBuildTree([], python_versions, build_types, mpi_types, cuda_versions, external_deps)
    mock_build_tree.build_commands = sample_build_commands[2:4] # Build cmds for py3.7

    output_dir = os.path.join(test_dir, '../condabuild' )
    mock_conda_env_file_generator = TestCondaEnvFileGenerator(python_versions, build_types, mpi_types, cuda_versions, None, output_dir)

    expected_channels = ["file:/{}".format(output_dir), "defaults"]
    actual_channels = mock_conda_env_file_generator.channels
    assert actual_channels == expected_channels

    variants = utils.make_variants(python_versions, build_types, mpi_types)
    expected_keys = [utils.variant_string(variant['python'], variant['build_type'], variant['mpi_type'], variant['cudatoolkit'])
                     for variant in variants]

    actual_keys = list(mock_conda_env_file_generator.dependency_dict.keys())
    assert Counter(actual_keys) == Counter(expected_keys)

    for build_command in mock_build_tree:
        mock_conda_env_file_generator.update_conda_env_file_content(build_command, mock_build_tree)

    mock_conda_env_file_generator.write_conda_env_files(TMP_OPENCE_DIR)

    # Conda env files should be generated only for py3.7-cpu-openmpi and py3.7-cuda-system variants
    expected_files_keys = [utils.variant_string("3.7", "cpu", "openmpi", "10.2"), utils.variant_string("3.7", "cuda", "system", "10.2")]

    # Check if conda env files are created for expected_files_keys
    for file_keys in expected_files_keys:
        cuda_env_file = os.path.join(TMP_OPENCE_DIR,
                                         "{}{}.yaml".format(utils.CONDA_ENV_FILENAME_PREFIX,
                                         file_keys))
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
    mpi_types = "openmpi"
    cuda_versions = "10.2"
    mock_build_tree = TestBuildTree([], python_versions, build_types, mpi_types, cuda_versions)

    mock_build_tree.build_commands = [build_tree.BuildCommand("recipe1",
                                      "repo1",
                                      [], # packages is intentionally kept empty
                                      python=python_versions,
                                      build_type=build_types,
                                      mpi_type=mpi_types,
                                      cudatoolkit=cuda_versions,
                                      run_dependencies=None)]

    output_dir = os.path.join(test_dir, '../condabuild' )
    mock_conda_env_file_generator = TestCondaEnvFileGenerator(python_versions, build_types, mpi_types, cuda_versions, [], output_dir)

    expected_keys = ["py3.7-cuda-openmpi"]
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
