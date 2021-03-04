# *****************************************************************
# (C) Copyright IBM Corp. 2021. All Rights Reserved.
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
import pytest
import imp
import shutil

test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'open-ce'))
open_ce = imp.load_source('open_ce', os.path.join(test_dir, '..', 'open-ce', 'open-ce'))
import get_licenses
import utils
from errors import OpenCEError

def test_get_licenses(capsys):
    '''
    This is a complete test of `get_licenses`.
    '''
    output_folder = "get_licenses_output"
    open_ce._main(["get", get_licenses.COMMAND, "--conda_env_file", "tests/test-conda-env3.yaml", "--output_folder", output_folder])

    captured = capsys.readouterr()
    assert "Unable to clone source for libopus-1.3.1" in captured.out
    assert "Unable to download source for icu-58.2" in captured.out

    output_file = os.path.join(output_folder, utils.DEFAULT_LICENSES_FILE)
    assert os.path.exists(output_file)
    with open(output_file) as file_stream:
        license_contents = file_stream.read()

    print(license_contents)
    assert "pytest	6.2.2	https://github.com/pytest-dev/pytest/	MIT" in license_contents

    shutil.rmtree(output_folder)

def test_get_licenses_failed_conda_create(mocker):
    '''
    This tests that an exception is thrown when `conda env create` fails.
    '''
    output_folder = "get_licenses_output"
    mocker.patch('utils.run_command_capture', side_effect=[(False, "", "")])

    with pytest.raises(OpenCEError) as err:
        open_ce._main(["get", get_licenses.COMMAND, "--conda_env_file", "tests/test-conda-env3.yaml", "--output_folder", output_folder])

    assert "Error generating licenses file." in str(err.value)

def test_get_licenses_failed_conda_remove(mocker):
    '''
    This tests that an exception is thrown when `conda env remove` is called.
    '''
    output_folder = "get_licenses_output"
    mocker.patch('utils.run_command_capture', side_effect=[(True, "", ""), (False, "", "")])
    mocker.patch('get_licenses.LicenseGenerator._add_licenses_from_environment', return_value=[])

    with pytest.raises(OpenCEError) as err:
        open_ce._main(["get", get_licenses.COMMAND, "--conda_env_file", "tests/test-conda-env3.yaml", "--output_folder", output_folder])

    assert "Error generating licenses file." in str(err.value)

def test_get_licenses_no_conda_env():
    '''
    This test ensures that an exception is thrown when no conda environment is provided.
    '''
    with pytest.raises(OpenCEError) as err:
        open_ce._main(["get", get_licenses.COMMAND])

    assert "The \'--conda_env_file\' argument is required." in str(err.value)

def test_add_licenses_from_info_file(capsys):
    '''
    This is a complete test of the add_licenses_from_info_file method.
    '''
    output_folder = "get_licenses_output"
    gen = get_licenses.LicenseGenerator()
    gen.add_licenses_from_info_file(os.path.join("tests", "test-open-ce-info-1.yaml"))

    captured = capsys.readouterr()
    assert "Unable to clone source for bad_git_package" in captured.out
    assert "Unable to download source for bad_url" in captured.out

    gen.write_licenses_file(output_folder)

    output_file = os.path.join(output_folder, utils.DEFAULT_LICENSES_FILE)
    assert os.path.exists(output_file)
    with open(output_file) as file_stream:
        license_contents = file_stream.read()

    print(license_contents)
    assert "DefinitelyTyped.google.analytics\tebc69904eb78f94030d5d517b42db20867f679c0\thttps://raw.githubusercontent.com/DefinitelyTyped/DefinitelyTyped/ebc69904eb78f94030d5d517b42db20867f679c0/chai/chai.d.ts\tMIT\tCopyright Jed Mao <https://github.com/jedmao/>,, Copyright Bart van der Schoor <https://github.com/Bartvds>,, Copyright Andrew Brown <https://github.com/AGBrown>,, Copyright Olivier Chevet <https://github.com/olivr70>" in license_contents
    assert "bad_url\t1.2.3\tnot_a_url.tar.gz\tNO_LICENSE\tNot a real copy right" in license_contents
    assert "google-test\t1.7.0\thttps://github.com/google/googletest/archive/release-1.7.0.zip\tBSD-equivalent\tCopyright 2008, Google Inc. All rights reserved." in license_contents
    assert "kissfft\t36dbc057604f00aacfc0288ddad57e3b21cfc1b8\thttps://github.com/mborgerding/kissfft/archive/36dbc057604f00aacfc0288ddad57e3b21cfc1b8.tar.gz\tBSD-equivalent\tCopyright (c) 2003-2010 Mark Borgerding . All rights reserved." in license_contents

    # Make sure google-test only appears once
    assert license_contents.count("google-test\t1.7.0") == 1
    shutil.rmtree(output_folder)
    shutil.rmtree(utils.TMP_LICENSE_DIR)

def test_no_info_file():
    '''
    Test that an empty file is returned when an info file doesn't exist at the provided path.
    '''
    output_folder = "get_licenses_output"
    gen = get_licenses.LicenseGenerator()
    gen.add_licenses_from_info_file(os.path.join("tests", "no-file.yaml"))
    gen.write_licenses_file(output_folder)

    output_file = os.path.join(output_folder, utils.DEFAULT_LICENSES_FILE)
    assert os.path.exists(output_file)
    with open(output_file) as file_stream:
        license_contents = file_stream.read()

    assert license_contents == ""

    shutil.rmtree(output_folder)
