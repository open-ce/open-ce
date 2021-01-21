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

import sys
import os
import pathlib
from collections import Counter

test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'open-ce'))

import build_tree
import conda_env_file_generator
import utils

sample_build_commands = [build_tree.BuildCommand("recipe1",
                                    "repo1",
                                    ["package1a", "package1b"],
                                    python="3.6",
                                    build_type="cuda",
                                    mpi_type="openmpi",
                                    cudatoolkit="10.2",
                                    run_dependencies=["python     >=3.6", "pack1    1.0", "pack2   >=2.0", "pack3 9b"]),
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
                                    run_dependencies=["python 3.7", "pack1==1.0", "pack2 <=2.0", "pack3   3.0.*",
                                                      "pack4=1.15.0=py38h6ffa863_0"]),
                         build_tree.BuildCommand("recipe4",
                                    "repo4",
                                    ["package4a", "package4b"],
                                    python="3.7",
                                    build_type="cuda",
                                    mpi_type="system",
                                    cudatoolkit="10.2",
                                    run_dependencies=["pack1==1.0", "pack2 <=2.0", "pack3-suffix 3.0"])]


external_deps = ["external_pac1    1.2", "external_pack2", "external_pack3=1.2.3"]

def test_conda_env_file_content():
    '''
    Tests that the conda env file content are being populated correctly
    '''
    packages = build_tree.get_installable_packages([sample_build_commands[0]], external_deps)
    mock_conda_env_file_generator = conda_env_file_generator.CondaEnvFileGenerator(packages)
    expected_deps = set(["python >=3.6", "pack1 1.0.*", "pack2 >=2.0", "package1a", "package1b",
                         "pack3 9b", "external_pac1 1.2.*", "external_pack2", "external_pack3=1.2.3"])
    assert Counter(expected_deps) == Counter(mock_conda_env_file_generator._dependency_set)

    packages = build_tree.get_installable_packages([sample_build_commands[1]], [])
    mock_conda_env_file_generator = conda_env_file_generator.CondaEnvFileGenerator(packages)
    expected_deps = set(["python ==3.6.*", "pack1 >=1.0", "pack2 ==2.0.*", "package2a", "pack3 3.3.* build"])
    assert Counter(expected_deps) == Counter(mock_conda_env_file_generator._dependency_set)

    packages = build_tree.get_installable_packages([sample_build_commands[2]], external_deps)
    mock_conda_env_file_generator = conda_env_file_generator.CondaEnvFileGenerator(packages)
    expected_deps = set(["python 3.7.*", "pack1==1.0.*", "pack2 <=2.0", "pack3 3.0.*", "package3a", "package3b",
                     "pack4=1.15.0=py38h6ffa863_0", "external_pac1 1.2.*", "external_pack2", "external_pack3=1.2.3"])
    assert Counter(expected_deps) == Counter(mock_conda_env_file_generator._dependency_set)

    packages = build_tree.get_installable_packages([sample_build_commands[3]], [])
    mock_conda_env_file_generator = conda_env_file_generator.CondaEnvFileGenerator(packages)
    expected_deps = set(["pack1==1.0.*", "pack2 <=2.0", "pack3-suffix 3.0.*", "package4a", "package4b"])
    assert Counter(expected_deps) == Counter(mock_conda_env_file_generator._dependency_set)

def test_create_channels():
    output_dir = os.path.join(test_dir, '../condabuild' )
    expected_channels = ["file:/{}".format(output_dir), "some channel", "defaults"]

    assert expected_channels == conda_env_file_generator._create_channels(["some channel"], output_dir)

def test_get_variant_string(mocker):
    var_str = "py3.6-cuda-openmpi-10.2"
    test_env_file = "#" + utils.OPEN_CE_VARIANT + ":" + var_str + "\nsomething else"
    mocker.patch('builtins.open', mocker.mock_open(read_data=test_env_file))

    assert conda_env_file_generator.get_variant_string("some_file.yaml") == var_str

def test_get_variant_string_no_string(mocker):
    test_env_file = "some string without\n a variant string"
    mocker.patch('builtins.open', mocker.mock_open(read_data=test_env_file))

    assert conda_env_file_generator.get_variant_string("some_file.yaml") is None
