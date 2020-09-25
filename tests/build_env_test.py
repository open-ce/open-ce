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
import helpers
import build_env

built_packages = set()
def validate_build_feedstock(args, package_deps = None, expect=[], reject=[], retval = 0):
    '''
    Used to mock the `build_feedstock` function and ensure that packages are built in a valid order.
    '''
    global built_packages
    if package_deps:
        package = args[-1][:-10]
        built_packages.add(package)
        for dependency in package_deps[package]:
            assert dependency in built_packages
    cli_string = " ".join(args)
    for term in expect:
        assert term in cli_string
    for term in reject:
        assert term not in cli_string
    return retval

def test_clone_repo(mocker):
    '''
    Simple positive test for `_clone_repo`.
    '''
    git_location = build_env.DEFAULT_GIT_LOCATION

    mocker.patch(
        'os.system',
        side_effect=(lambda x: helpers.validate_cli(x, expect=["git clone",
                                                               "-b master",
                                                               "--single-branch",
                                                               git_location + "/my_repo.git",
                                                               "/test/my_repo"]))
    )

    assert build_env._clone_repo(git_location, "/test/my_repo", None, "master", "master") == 0

def test_clone_repo_failure(mocker, capsys):
    '''
    Simple negative test for `_clone_repo`.
    '''
    mocker.patch(
        'os.system',
        side_effect=(lambda x: helpers.validate_cli(x, expect=["git clone"], retval=1))
    )

    assert build_env._clone_repo(build_env.DEFAULT_GIT_LOCATION, "/test/my_repo", None, "master", None) == 1
    captured = capsys.readouterr()
    assert "Unable to clone repository" in captured.out

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

    create_recipes_result = build_env._create_recipes("/test/my_repo", None, "master", {'python' : ['3.6'], 'build_type' : ['cuda']}, [])
    assert create_recipes_result[0].get('packages') == {'horovod'}
    for dep in {'build_req1', 'build_req2            1.2'}:
        assert dep in create_recipes_result[0].get('build_dependencies')
    for dep in {'run_req1            1.3'}:
        assert dep in create_recipes_result[0].get('run_dependencies')
    for dep in {'host_req1            1.0', 'host_req2'}:
        assert dep in create_recipes_result[0].get('host_dependencies')
    for dep in {'test_req1'}:
        assert dep in create_recipes_result[0].get('test_dependencies')

def test_build_env(mocker):
    '''
    This is a complete test of `build_env`.
    It uses `test-env2.yaml` which has a dependency on `test-env1.yaml`, and specifies a chain of package dependencies.
    That chain of package dependencies is used by the mocked build_feedstock to ensure that the order of builds is correct.
    '''
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
        side_effect=helpers.mocked_getcwd
    )
    mocker.patch(
        'os.chdir',
        side_effect=helpers.validate_chdir
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
    mocker.patch( # This ensures that 'package21' is not built when the python version is 2.0.
        'build_feedstock.build_feedstock',
        side_effect=(lambda x: validate_build_feedstock(x, package_deps, expect=["--python_versions 2.0"], reject=["package21-feedstock"]))
    )
    env_file = os.path.join(test_dir, 'test-env2.yaml')
    assert build_env.build_env([env_file, "--python_versions", "2.0"]) == 0

    #---The second test specifies a python version that is supported in the env file by package21.
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
    mocker.patch(
        'build_feedstock.build_feedstock',
        side_effect=(lambda x: validate_build_feedstock(x, package_deps, expect=["--python_versions 2.1"]))
    )
    env_file = os.path.join(test_dir, 'test-env2.yaml')
    assert build_env.build_env([env_file, "--python_versions", "2.1"]) == 0

     #---The third test verifies that the repository_folder argument is working properly.
    mocker.patch(
        'build_feedstock.build_feedstock',
        side_effect=(lambda x: validate_build_feedstock(x, package_deps, expect=["--working_directory repo_folder/"]))
    )
    env_file = os.path.join(test_dir, 'test-env2.yaml')
    assert build_env.build_env([env_file, "--repository_folder", "repo_folder"]) == 0

def test_env_validate(mocker, capsys):
    '''
    This is a negative test of `build_env`, which passes an invalid env file.
    '''
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
        side_effect=helpers.mocked_getcwd
    )
    mocker.patch(
        'conda_build.api.render',
        side_effect=(lambda path, *args, **kwargs: helpers.mock_renderer(os.getcwd(), package_deps))
    )
    mocker.patch(
        'os.chdir',
        side_effect=helpers.validate_chdir
    )
    mocker.patch(
        'build_feedstock.build_feedstock',
        side_effect=(lambda x: validate_build_feedstock(x))
    )
    env_file = os.path.join(test_dir, 'test-env-invalid1.yaml')
    assert build_env.build_env([env_file]) == 1
    captured = capsys.readouterr()
    assert "chnnels is not a valid key in the environment file." in captured.err

def test_build_env_docker_build(mocker):
    '''
    Test that passing the --docker_build argument calls docker_build.build_with_docker
    '''
    arg_strings = ["--docker_build", "my-env.yaml"]

    mocker.patch('docker_build.build_with_docker', return_value=0)

    assert build_env.build_env(arg_strings) == 0
