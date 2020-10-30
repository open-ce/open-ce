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
import helpers
import build_env
import utils
from errors import OpenCEError

class PackageBuildTracker(object):
    def __init__(self):
        self.built_packages = set()

    def validate_build_feedstock(self, args, package_deps = None, expect=None, reject=None, retval = 0):
        '''
        Used to mock the `build_feedstock` function and ensure that packages are built in a valid order.
        '''
        if package_deps:
            package = args[-1][:-10]
            self.built_packages.add(package)
            for dependency in package_deps[package]:
                assert dependency in self.built_packages
        cli_string = " ".join(args)
        if expect:
            for term in expect:
                assert term in cli_string
        if reject:
            for term in reject:
                assert term not in cli_string
        return retval

def test_build_env(mocker):
    '''
    This is a complete test of `build_env`.
    It uses `test-env2.yaml` which has a dependency on `test-env1.yaml`, and specifies a chain of package dependencies.
    That chain of package dependencies is used by the mocked build_feedstock to ensure that the order of builds is correct.
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
        'os.chdir',
        side_effect=dirTracker.validate_chdir
    )
    mocker.patch(
        'validate_config.validate_env_config'
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
    py_version = "2.0"
    buildTracker = PackageBuildTracker()
    mocker.patch( # This ensures that 'package21' is not built when the python version is 2.0.
        'build_feedstock.build_feedstock',
        side_effect=(lambda x: buildTracker.validate_build_feedstock(x, package_deps,
                     expect=["--python_versions {}".format(py_version)], reject=["package21-feedstock"]))
    )

    env_file = os.path.join(test_dir, 'test-env2.yaml')
    build_env.build_env([env_file, "--python_versions", py_version])
    validate_conda_env_files(py_version)

    #---The second test specifies a python version that is supported in the env file by package21.
    py_version = "2.1"
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
        'build_feedstock.build_feedstock',
        side_effect=(lambda x: buildTracker.validate_build_feedstock(x, package_deps,
                     expect=["--python_versions {}".format(py_version)]))
    )

    env_file = os.path.join(test_dir, 'test-env2.yaml')
    build_env.build_env([env_file, "--python_versions", py_version])
    validate_conda_env_files(py_version)

     #---The third test verifies that the repository_folder argument is working properly.
    buildTracker = PackageBuildTracker()
    mocker.patch(
        'build_feedstock.build_feedstock',
        side_effect=(lambda x: buildTracker.validate_build_feedstock(x, package_deps, expect=["--working_directory repo_folder/"]))
    )
    py_version = "2.1"
    env_file = os.path.join(test_dir, 'test-env2.yaml')
    build_env.build_env([env_file, "--repository_folder", "repo_folder", "--python_versions", py_version])
    validate_conda_env_files(py_version)

def validate_conda_env_files(py_versions=utils.DEFAULT_PYTHON_VERS,
                             build_types=utils.DEFAULT_BUILD_TYPES,
                             mpi_types=utils.DEFAULT_MPI_TYPES):

    # Check if conda env files are created for given python versions and build variants
    variants = utils.make_variants(py_versions, build_types, mpi_types)
    for variant in variants:
        cuda_env_file = os.path.join(os.getcwd(),
                                     "{}{}.yaml".format(utils.CONDA_ENV_FILENAME_PREFIX,
                                     utils.variant_string(variant['python'], variant['build_type'], variant['mpi_type'])))

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
        'build_feedstock.build_feedstock',
        side_effect=buildTracker.validate_build_feedstock
    )
    env_file = os.path.join(test_dir, 'test-env-invalid1.yaml')
    with pytest.raises(OpenCEError) as exc:
        build_env.build_env([env_file])
    assert "Unexpected key chnnels was found in " in str(exc.value)

def test_build_env_docker_build(mocker):
    '''
    Test that passing the --docker_build argument calls docker_build.build_with_docker
    '''
    arg_strings = ["--docker_build", "my-env.yaml"]

    mocker.patch('docker_build.build_with_docker', return_value=0)

    mocker.patch('pkg_resources.get_distribution', return_value=None)

    build_env.build_env(arg_strings)

def test_build_env_if_no_conda_build(mocker):
    '''
    Test that build_env should fail if conda_build isn't present and no --docker_build
    '''
    arg_strings = ["my-env.yaml"]

    mocker.patch('pkg_resources.get_distribution', return_value=None)
    with pytest.raises(OpenCEError):
        build_env.build_env(arg_strings)

