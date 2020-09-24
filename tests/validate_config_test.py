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
import validate_config

def make_render_result(package_name, build_reqs=[], run_reqs=[], host_reqs=[], test_reqs=[]):
    '''
    Creates a YAML string that is a mocked result of `conda_build.api.render`.
    '''
    retval = [(helpers.Namespace(meta={
                            'package': {'name': package_name, 'version': '1.2.3'},
                            'source': {'git_url': 'https://github.com/'+package_name+'.git', 'git_rev': 'v0.19.5', 'patches': []},
                            'build': {'number': '1', 'string': 'py37_1'},
                            'requirements': {'build': build_reqs, 'host': host_reqs, 'run': run_reqs + ["upstreamdep1   2.3","upstreamdep2   2"], 'run_constrained': []},
                            'test': {'requires': test_reqs},
                            'about': {'home': 'https://github.com/'+package_name+'.git', 'license_file': 'LICENSE', 'summary': package_name},
                            'extra': {'final': True}}),
                      True,
                      None)]
    return retval

def mock_renderer(path, package_deps):
    '''
    Used to mock the `conda_build.api.render` function by extracting the package name from `path`
    and using that to get the dependencies from `package_deps`.
    '''
    package = os.path.basename(path)[:-10]
    return make_render_result(package, package_deps[package])

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
        side_effect=(lambda x: helpers.validate_cli(x, expect=["conda create --dry-run",
                                                               "upstreamdep1   2.3.*",
                                                               "upstreamdep2   2.*"],
                                                       reject=["package"],
                                                       ignore=["git clone"]))
    )
    mocker.patch(
        'os.getcwd',
        side_effect=helpers.mocked_getcwd
    )
    mocker.patch(
        'os.chdir',
        side_effect=helpers.validate_chdir
    )
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
        side_effect=(lambda path, *args, **kwargs: mock_renderer(os.getcwd(), package_deps))
    )
    env_file = os.path.join(test_dir, 'test-env2.yaml')
    assert validate_config.validate_config(["./conda_build_config.yaml", "--env_files", env_file, "--python_versions", "3.6", "--build_types", "cuda"]) == 0

def test_build_negative(mocker, capsys):
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
        side_effect=(lambda x: helpers.validate_cli(x, expect=["conda create --dry-run",
                                                               "upstreamdep1   2.3.*"], #Checks that the value from the default config file is used.
                                                       reject=["package"],
                                                       retval=1,
                                                       ignore=["git clone"]))
    )
    mocker.patch(
        'os.getcwd',
        side_effect=helpers.mocked_getcwd
    )
    mocker.patch(
        'os.chdir',
        side_effect=helpers.validate_chdir
    )
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
        side_effect=(lambda path, *args, **kwargs: mock_renderer(os.getcwd(), package_deps))
    )
    env_file = os.path.join(test_dir, 'test-env2.yaml')
    assert validate_config.validate_config(["./conda_build_config.yaml", "--env_files", env_file, "--python_versions", "3.6", "--build_types", "cuda"]) == 1
    captured = capsys.readouterr()
    assert "Error while validating ./conda_build_config.yaml for " in captured.out
