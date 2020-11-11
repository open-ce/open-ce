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

DESCRIPTION = 'Test a feedstock as part of Open-CE'

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
    def __init__(self, name, conda_env=None, bash_command="", create_env=False, clean_env=False, working_dir=os.getcwd()):
        self.bash_command = bash_command
        self.conda_env = conda_env
        self.name = name
        self.create_env = create_env
        self.clean_env = clean_env
        self.working_dir = working_dir

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

def gen_test_commands(test_file=utils.DEFAULT_TEST_CONFIG_FILE, working_dir=os.getcwd()):
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

def make_parser():
    ''' Parser for input arguments '''
    arguments = [utils.Argument.CONDA_ENV_FILE, utils.Argument.TEST_WORKING_DIRECTORY]
    parser = utils.make_parser(arguments, description = DESCRIPTION)

    return parser

def _test_feedstock_parsed(args):
    test_commands = gen_test_commands(working_dir=args.test_working_dir)
    failed_tests = run_test_commands(args.conda_env_file, test_commands)
    display_failed_tests(failed_tests)

    return len(failed_tests)

def test_feedstock(arg_strings=None):
    '''
    Entry function.
    '''
    parser = make_parser()
    args = parser.parse_args(arg_strings)
    return _test_feedstock_parsed(args)

if __name__ == '__main__':
    try:
        sys.exit(test_feedstock())
    except OpenCEError as err:
        print(err.msg, file=sys.stderr)
        sys.exit(1)
