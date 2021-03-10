#!/usr/bin/env python
"""
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
"""

import datetime
import os
import tempfile
import subprocess
from enum import Enum, unique, auto

from open_ce import utils
from open_ce import conda_env_file_generator
from open_ce import inputs
from open_ce.inputs import Argument
from open_ce.errors import OpenCEError, Error

COMMAND = 'feedstock'
DESCRIPTION = 'Test a feedstock as part of Open-CE'
ARGUMENTS = [Argument.CONDA_ENV_FILE, Argument.TEST_WORKING_DIRECTORY, Argument.TEST_LABELS,
             Argument.WORKING_DIRECTORY]

@unique
class Key(Enum):
    '''Enum for Test File Keys'''
    tests = auto()
    name = auto()
    command = auto()

_TEST_SCHEMA ={
    Key.name.name: utils.make_schema_type(str, True),
    Key.command.name: utils.make_schema_type(str, True)
}

_TEST_FILE_SCHEMA = {
    Key.tests.name: utils.make_schema_type([_TEST_SCHEMA])
}

class TestCommand():
    """
    Contains a test to run within a given conda environment.

    Args:
        name (str): The name describing the test.
        conda_env (str): The name of the conda environment that the test will be run in.
        bash_command (str): The bash command to run.
        create_env (bool): Whether this is the command to create a new conda environment.
        clean_env (bool): Whether this is the command to remove a conda environment.
        working_dir (str): Working directory to be used when executing the bash command.
    """
    #pylint: disable=too-many-arguments
    def __init__(self, name, conda_env=None, bash_command="",
                 create_env=False, clean_env=False, working_dir=os.getcwd()):
        self.bash_command = bash_command
        self.conda_env = conda_env
        self.name = name
        self.create_env = create_env
        self.clean_env = clean_env
        self.working_dir = working_dir
        self.feedstock_dir = os.getcwd()

    def get_test_command(self, conda_env_file=None):
        """"
        Returns a string of the test command.

        Args:
            conda_env_file (str): The name of the original conda environment file.
                                  This is only needed when create_env is True.
        """
        output = ""
        if self.create_env:
            output += "conda env create -f " + conda_env_file + " -n " + self.conda_env + "\n"
            return output

        if self.clean_env:
            output += "conda env remove -y -n " + self.conda_env + "\n"
            return output

        output += "CONDA_BIN=$(dirname $(which conda))\n"
        output += "source ${CONDA_BIN}/../etc/profile.d/conda.sh\n"
        output += "conda activate " + self.conda_env + "\n"
        output += "export FEEDSTOCK_DIR=" + self.feedstock_dir + "\n"
        output += self.bash_command + "\n"

        return output

    def run(self, conda_env_file):
        """
        Runs the test.

        Creates a temporary bash file, and writes the contents to `get_test_command` into it.
        Runs the generated bash file.
        Removes the temporary bash file.

        Args:
            conda_env_file (str): The name of the original conda environment file.
        """
        print("Running: " + self.name)
        # Create file containing bash commands
        if not os.path.exists(self.working_dir):
            os.mkdir(self.working_dir)
        with tempfile.NamedTemporaryFile(mode='w+t', dir=self.working_dir, delete=False) as temp:
            temp.write("set -e\n")
            temp.write(self.get_test_command(conda_env_file))
            temp_file_name = temp.name

        # Execute file
        retval,output,_ = utils.run_command_capture("bash {}".format(temp_file_name),
                                                    stderr=subprocess.STDOUT,
                                                    cwd=self.working_dir)

        # Remove file containing bash commands
        os.remove(temp_file_name)

        result = TestResult(self.name, retval, output)

        if not retval:
            result.display_failed()

        return result

class TestResult():
    """
    Contains the results of running a test.

    Args:
        name (str): The name of the test that was run.
        returncode (int): The return code of the test that was run.
        output (str): The resuling output from running the test.
    """
    def __init__(self, name, returncode, output):
        self.name = name
        self.output = output
        self.returncode = returncode

    def display_failed(self):
        """
        Display the output from a failed test.
        """
        if self.failed():
            print("--------------------------------")
            print("Failed test: " + self.name)
            print(self.output)
            print("--------------------------------")

    def failed(self):
        """
        Returns whether or not a test failed.
        """
        return not self.returncode

def load_test_file(test_file, variants):
    """
    Load a given test file.

    Args:
        test_file (str): Path to the test file to load.
    """
    #pylint: disable=import-outside-toplevel
    from open_ce import conda_utils

    if not os.path.exists(test_file):
        return None

    test_file_data = conda_utils.render_yaml(test_file, variants, permit_undefined_jinja=True, schema=_TEST_FILE_SCHEMA)

    return test_file_data

def gen_test_commands(test_file=utils.DEFAULT_TEST_CONFIG_FILE, variants=None, working_dir=os.getcwd()):
    """
    Generate a list of test commands from the provided test file.

    Args:
        test_file (str): Path to the test file.
    """
    test_data = load_test_file(test_file, variants)
    if not test_data or not test_data['tests']:
        return []

    time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    conda_env = utils.CONDA_ENV_FILENAME_PREFIX + time_stamp

    test_commands = []

    # Create conda environment for testing
    test_commands.append(TestCommand(name="Create conda environment " + conda_env,
                                     conda_env=conda_env,
                                     create_env=True,
                                     working_dir=working_dir))

    for test in test_data['tests']:
        test_commands.append(TestCommand(name=test.get('name'),
                                         conda_env=conda_env,
                                         bash_command=test.get('command'),
                                         working_dir=working_dir))

    test_commands.append(TestCommand(name="Remove conda environment " + conda_env,
                                     conda_env=conda_env,
                                     clean_env=True,
                                     working_dir=working_dir))

    return test_commands

def run_test_commands(conda_env_file, test_commands):
    """
    Run a list of tests within a conda environment.

    Args:
        conda_env_file (str): The name of the conda environment file used to create the conda environment.
        test_commands (:obj:`list` of :obj:`TestCommand): List of test commands to run.
    """
    failed_tests = []
    for test_command in test_commands:
        test_result = test_command.run(conda_env_file)
        if test_result.failed():
            failed_tests.append(test_result)

    return failed_tests

def display_failed_tests(failed_tests):
    """
    Display a list of failed tests.

    Args:
        failed_tests (:obj:`list` of :obj:`TestResult`): A list of failed TestResult's.
    """
    # If any collected output, return 1, else return 0
    if failed_tests:
        for failed_test in failed_tests:
            failed_test.display_failed()
        print("The following tests failed: " + str([failed_test.name for failed_test in failed_tests]))
    else:
        print("All tests passed!")

def test_feedstock(conda_env_file, test_labels=None,
                   test_working_dir=utils.DEFAULT_TEST_WORKING_DIRECTORY, working_directory=None):
    """
    Test a particular feedstock, provided by the working_directory argument.
    """
    saved_working_directory = None
    if working_directory:
        saved_working_directory = os.getcwd()
        os.chdir(os.path.abspath(working_directory))

    conda_env_file = os.path.abspath(conda_env_file)
    var_string = conda_env_file_generator.get_variant_string(conda_env_file)
    if var_string:
        variant_dict = utils.variant_string_to_dict(var_string)
    else:
        variant_dict = dict()
    for test_label in inputs.parse_arg_list(test_labels):
        variant_dict[test_label] = True
    test_commands = gen_test_commands(working_dir=test_working_dir, variants=variant_dict)
    failed_tests = run_test_commands(conda_env_file, test_commands)

    if saved_working_directory:
        os.chdir(saved_working_directory)

    return failed_tests

def test_feedstock_entry(args):
    '''Entry Function'''
    if not args.conda_env_files:
        raise OpenCEError(Error.CONDA_ENV_FILE_REQUIRED)

    test_failures = []
    for conda_env_file in inputs.parse_arg_list(args.conda_env_files):
        test_failures += test_feedstock(conda_env_file,
                                       args.test_labels,
                                       args.test_working_dir,
                                       args.working_directory)

    if test_failures:
        display_failed_tests(test_failures)
        raise OpenCEError(Error.FAILED_TESTS, len(test_failures))

ENTRY_FUNCTION = test_feedstock_entry
