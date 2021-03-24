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
import imp

test_dir = pathlib.Path(__file__).parent.absolute()

import helpers
opence = imp.load_source('opence', os.path.join(test_dir, '..', 'open_ce', 'open-ce'))
import open_ce.validate_config as validate_config
from open_ce.errors import OpenCEError

def conda_search_json(package):
    retval = '{\n'
    retval += '  "{}": ['.format(package)
    retval += '''
    {
      "arch": null,
      "build": "py36habc2bb6_0",
      "build_number": 0,
      "channel": "https://repo.anaconda.com/pkgs/main/linux-ppc64le",
      "constrains": [],
      "depends": [],
      "timestamp": 1580920230562
    }
  ]
}'''
    return retval

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
        return_value=0
    )
    mocker.patch(
        'open_ce.utils.run_command_capture',
        side_effect=(lambda x: helpers.validate_cli(x, expect=["conda create --dry-run",
                                                               "upstreamdep1 2.3.*",
                                                               "upstreamdep2 2.*"],
                                                       reject=["package"], #No packages from the env files should show up in the create command.
                                                       retval=[True, "", ""]))
    )
    mocker.patch(
        'open_ce.conda_utils.conda_package_info',
        side_effect=(lambda channels, package: conda_search_json(package))
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
    mocker.patch(
        'conda_build.api.get_output_file_paths',
        side_effect=(lambda meta, *args, **kwargs: helpers.mock_get_output_file_paths(meta))
    )

    env_file = os.path.join(test_dir, 'test-env2.yaml')
    opence._main(["validate", validate_config.COMMAND, "--conda_build_config", "./conda_build_config.yaml", env_file, "--python_versions", "3.6", "--build_types", "cuda"])

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
        return_value=0
    )
    mocker.patch(
        'open_ce.utils.run_command_capture',
        side_effect=(lambda x: helpers.validate_cli(x, expect=["conda create --dry-run",
                                                               "upstreamdep1 2.3.*", #Checks that the value from the default config file is used.
                                                               "external_dep1", # Checks that the external dependencies were used.
                                                               "external_dep2 5.2.*", # Checks that the external dependencies were used.
                                                               "external_dep3=5.6.*"], # Checks that the external dependencies were used.
                                                       reject=["package"],
                                                       retval=[False, "", ""]))
    )
    mocker.patch(
        'open_ce.conda_utils.conda_package_info',
        side_effect=(lambda channels, package: conda_search_json(package))
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
    mocker.patch(
        'conda_build.api.get_output_file_paths',
        side_effect=(lambda meta, *args, **kwargs: helpers.mock_get_output_file_paths(meta))
    )

    env_file = os.path.join(test_dir, 'test-env2.yaml')
    with pytest.raises(OpenCEError) as err:
        opence._main(["validate", validate_config.COMMAND, "--conda_build_config", "./conda_build_config.yaml", env_file, "--python_versions", "3.6", "--build_types", "cuda"])
    assert "Error validating \"" in str(err.value)
    assert "conda_build_config.yaml\" for " in str(err.value)
    assert "Dependencies are not compatible.\nCommand:\nconda create" in str(err.value)

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
        opence._main(["validate", validate_config.COMMAND, "--conda_build_config", "./conda_build_config.yaml", env_file, "--python_versions", "3.6", "--build_types", "cuda"])
    assert "Error validating \"" in str(err.value)
    assert "conda_build_config.yaml\" for " in str(err.value)
    assert "Unexpected key chnnels was found in " in str(err.value)
