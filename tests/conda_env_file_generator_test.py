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


external_deps = ["external_pac1    1.2", "external_pack2", "external_pack3=1.2.3"]

def test_conda_env_file_content():
    '''
    Tests that the conda env file content are being populated correctly
    '''
    mock_conda_env_file_generator = conda_env_file_generator.CondaEnvFileGenerator([sample_build_commands[0]], external_deps)
    expected_deps = set(["python >=3.6", "pack1 1.0.*", "pack2 >=2.0", "package1a", "package1b",
                      "external_pac1 1.2.*", "external_pack2", "external_pack3=1.2.3"])
    assert Counter(expected_deps) == Counter(mock_conda_env_file_generator._dependency_set)

    mock_conda_env_file_generator = conda_env_file_generator.CondaEnvFileGenerator([sample_build_commands[1]], [])
    expected_deps = set(["python ==3.6.*", "pack1 >=1.0", "pack2 ==2.0.*", "package2a", "pack3 3.3.* build"])
    assert Counter(expected_deps) == Counter(mock_conda_env_file_generator._dependency_set)

    mock_conda_env_file_generator = conda_env_file_generator.CondaEnvFileGenerator([sample_build_commands[2]], external_deps)
    expected_deps = set(["python 3.7.*", "pack1==1.0.*", "pack2 <=2.0", "pack3 3.0.*", "package3a", "package3b",
                     "external_pac1 1.2.*", "external_pack2", "external_pack3=1.2.3"])
    assert Counter(expected_deps) == Counter(mock_conda_env_file_generator._dependency_set)

    mock_conda_env_file_generator = conda_env_file_generator.CondaEnvFileGenerator([sample_build_commands[3]], [])
    expected_deps = set(["pack1==1.0.*", "pack2 <=2.0", "pack3-suffix 3.0.*", "package4a", "package4b"])
    assert Counter(expected_deps) == Counter(mock_conda_env_file_generator._dependency_set)

def test_create_channels():
    output_dir = os.path.join(test_dir, '../condabuild' )
    expected_channels = ["file:/{}".format(output_dir), "some channel", "defaults"]

    assert expected_channels == conda_env_file_generator._create_channels(["some channel"], output_dir)
