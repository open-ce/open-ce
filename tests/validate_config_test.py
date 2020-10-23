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
import validate_config
from utils import OpenCEError

def test_validate_config(mocker):
    '''
    This is a complete test of `validate_config`.
    '''
    dirTracker = helpers.DirTracker()
    mocker.patch(
        'os.mkdir',
        return_value=0 #Don't worry about making directories.
    )
    mocker.patch(
        'os.system',
        side_effect=(lambda x: helpers.validate_cli(x, expect=["conda create --dry-run",
                                                               "upstreamdep1 2.3.*",
                                                               "upstreamdep2 2.*"],
                                                       reject=["package"], #No packages from the env files should show up in the create command.
                                                       ignore=["git clone"]))
    )
    mocker.patch(
        'os.getcwd',
        side_effect=dirTracker.mocked_getcwd
    )
    mocker.patch(
        'os.chdir',
        side_effect=dirTracker.validate_chdir
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
        side_effect=(lambda path, *args, **kwargs: helpers.mock_renderer(os.getcwd(), package_deps))
    )
    env_file = os.path.join(test_dir, 'test-env2.yaml')
    validate_config.validate_config(["--conda_build_config", "./conda_build_config.yaml", env_file, "--python_versions", "3.6", "--build_types", "cuda"])

def test_validate_negative(mocker):
    '''
    This is a negative test of `validate_config` where the dry-run fails.
    '''
    dirTracker = helpers.DirTracker()
    mocker.patch(
        'os.mkdir',
        return_value=0 #Don't worry about making directories.
    )
    mocker.patch(
        'os.system',
        side_effect=(lambda x: helpers.validate_cli(x, expect=["conda create --dry-run",
                                                               "upstreamdep1 2.3.*", #Checks that the value from the default config file is used.
                                                               "external_dep1", # Checks that the external dependencies were used.
                                                               "external_dep2 5.2.*", # Checks that the external dependencies were used.
                                                               "external_dep3=5.6.*"], # Checks that the external dependencies were used.
                                                       reject=["package"],
                                                       retval=1,
                                                       ignore=["git clone"]))
    )
    mocker.patch(
        'os.getcwd',
        side_effect=dirTracker.mocked_getcwd
    )
    mocker.patch(
        'os.chdir',
        side_effect=dirTracker.validate_chdir
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
        side_effect=(lambda path, *args, **kwargs: helpers.mock_renderer(os.getcwd(), package_deps))
    )
    env_file = os.path.join(test_dir, 'test-env2.yaml')
    with pytest.raises(OpenCEError) as err:
        validate_config.validate_config(["--conda_build_config", "./conda_build_config.yaml", env_file, "--python_versions", "3.6", "--build_types", "cuda"])
    assert "Error while validating ./conda_build_config.yaml for " in str(err.value)

def test_validate_bad_env(mocker):
    '''
    This is a negative test of `validate_config` where the env file is bad.
    '''
    dirTracker = helpers.DirTracker()
    mocker.patch(
        'os.mkdir',
        return_value=0 #Don't worry about making directories.
    )
    mocker.patch(
        'os.system',
        return_value=0
    )
    mocker.patch(
        'os.getcwd',
        side_effect=dirTracker.mocked_getcwd
    )
    mocker.patch(
        'os.chdir',
        side_effect=dirTracker.validate_chdir
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
        side_effect=(lambda path, *args, **kwargs: helpers.mock_renderer(os.getcwd(), package_deps))
    )
    env_file = os.path.join(test_dir, 'test-env-invalid1.yaml')
    with pytest.raises(OpenCEError) as err:
        validate_config.validate_config(["--conda_build_config", "./conda_build_config.yaml", env_file, "--python_versions", "3.6", "--build_types", "cuda"])
    assert "Error while validating ./conda_build_config.yaml for " in str(err.value)
    assert "Unexpected key chnnels was found in " in str(err.value)
