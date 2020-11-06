#!/usr/bin/env python
"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""

import datetime
import os
import tempfile
import sys
import subprocess

import yaml

import utils
from utils import OpenCEError

class TestCommand():
    """
    Contains a test to run within a given conda environment.

    Args:
        name (str): The name describing the test.
        conda_env (str): The name of the conda environment that the test will be run in.
        bash_command (str): The bash command to run.
        create_env (bool): Whether this is the command to create a new conda environment.
        clean_env (bool): Whether this is the command to remove a conda environment.
    """
    #pylint: disable=too-many-arguments
    def __init__(self, name, conda_env=None, bash_command="", create_env=False, clean_env=False):
        self.bash_command = bash_command
        self.conda_env = conda_env
        self.name = name
        self.create_env = create_env
        self.clean_env = clean_env

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
        with tempfile.NamedTemporaryFile(mode='w+t', dir=os.getcwd(), delete=False) as temp:
            temp.write("set -e\n")
            temp.write(self.get_test_command(conda_env_file))
            temp_file_name = temp.name

        # Execute file
        test_process = subprocess.run(["bash", temp_file_name], stdout=subprocess.PIPE, check=False,
                                      stderr=subprocess.STDOUT, universal_newlines=True)

        # Remove file containing bash commands
        os.remove(temp_file_name)

        result = TestResult(self.name, test_process.returncode, test_process.stdout)

        if test_process.returncode != 0:
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
        return self.returncode != 0

def load_test_file(test_file):
    """
    Load a given test file.

    Args:
        test_file (str): Path to the test file to load.
    """
    if not os.path.exists(test_file):
        return None

    with open(test_file, 'r') as stream:
        test_file_data = yaml.safe_load(stream)

    return test_file_data

def gen_test_commands(test_file=utils.DEFAULT_TEST_CONFIG_FILE):
    """
    Generate a list of test commands from the provided test file.

    Args:
        test_file (str): Path to the test file.
    """
    test_data = load_test_file(test_file)
    if not test_data:
        return []

    time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    conda_env = utils.CONDA_ENV_FILENAME_PREFIX + time_stamp

    test_commands = []

    # Create conda environment for testing
    test_commands.append(TestCommand(name="Create conda environment " + conda_env,
                                     conda_env=conda_env,
                                     create_env=True))

    for test in test_data['tests']:
        test_commands.append(TestCommand(name=test.get('name'), conda_env=conda_env, bash_command=test.get('command')))

    test_commands.append(TestCommand(name="Remove conda environment " + conda_env,
                                     conda_env=conda_env,
                                     clean_env=True))

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

def make_parser():
    ''' Parser for input arguments '''
    arguments = [utils.Argument.CONDA_ENV_FILE]
    parser = utils.make_parser(arguments, description = 'Test a feedstock as part of Open-CE')

    return parser

def test_feedstock(arg_strings=None):
    '''
    Entry function.
    '''
    parser = make_parser()
    args = parser.parse_args(arg_strings)

    test_commands = gen_test_commands()
    failed_tests = run_test_commands(args.conda_env_file, test_commands)
    display_failed_tests(failed_tests)

    return len(failed_tests)

if __name__ == '__main__':
    try:
        sys.exit(test_feedstock())
    except OpenCEError as err:
        print(err.msg, file=sys.stderr)
        sys.exit(1)
