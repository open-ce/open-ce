"""
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
"""

import os
import json
import datetime
import utils
from errors import OpenCEError, Error
from inputs import Argument

COMMAND = 'licenses'

DESCRIPTION = 'Gather license information for a group of packages'

ARGUMENTS = [Argument.OUTPUT_FOLDER, Argument.CONDA_ENV_FILE]

class LicenseGenerator():
    """
    The LicenseGenerator class is used to generate license information about all of
    the packages installed within a conda environment.
    """
    class LicenseInfo():
        """
        The LicenseInfo class holds license information for a single package.
        """
        def __init__(self, name, version, url, license_type):
            self.name = name
            self.version = version
            self.url = url
            self.license_type = license_type

        def __str__(self):
            return "{}\t{}\t{}\t{}".format(self.name, self.version, self.url, self.license_type)

        def __lt__(self, other):
            return self.name < other.name

        def __hash__(self):
            return hash(self.name)

    def __init__(self):
        self._licenses = set()

    def add_licenses(self, conda_env_file):
        """
        Add all of the license information for every package within a given conda
        environment file.
        """
        # Create a conda environment from the provided file
        time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        conda_env_path = os.path.join(os.getcwd(), "license_env_file_" + time_stamp)
        cli = "conda env create -p {} -f {}".format(conda_env_path, conda_env_file)
        ret_code, std_out, std_err = utils.run_command_capture(cli)
        if not ret_code:
            raise OpenCEError(Error.GET_LICENSES, cli, std_out, std_err)

        # Get all of the licenses from the file
        self._add_licenses_from_environment(conda_env_path)

        # Delete the generated conda environment
        cli = "conda env remove -p {}".format(conda_env_path)
        ret_code, std_out, std_err = utils.run_command_capture(cli)
        if not ret_code:
            raise OpenCEError(Error.GET_LICENSES, cli, std_out, std_err)

    def write_licenses_file(self, output_folder):
        """
        Write all of the license information to the provided path.
        """
        result = ""
        for lic in sorted(self._licenses):
            result += str(lic) + "\n"

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        licenses_file = os.path.join(output_folder, utils.DEFAULT_LICENSES_FILE)

        with open(licenses_file, 'w') as file_stream:
            file_stream.write(result)

        print("INFO: Licenses file generated: " + licenses_file)

    def _add_licenses_from_environment(self, conda_env):
        # For each meta-pkg within an environment, find its about.json file.
        meta_files = [meta_file for meta_file in os.listdir(os.path.join(conda_env, "conda-meta"))
                          if meta_file.endswith('.json')]

        for meta_file in meta_files:
            # Find the extracted_package_dir
            with open(os.path.join(conda_env, "conda-meta", meta_file)) as file_stream:
                meta_data = json.load(file_stream)

            with open(os.path.join(meta_data["extracted_package_dir"], "info", "about.json")) as file_stream:
                about_data = json.load(file_stream)

            info = LicenseGenerator.LicenseInfo(meta_data["name"],
                                                meta_data["version"],
                                                about_data.get("dev_url", about_data.get("home", "none")),
                                                about_data.get("license", "none"))
            self._licenses.add(info)


def get_licenses(args):
    """
    Entry point for `get licenses`.
    """
    if not args.conda_env_file:
        raise OpenCEError(Error.CONDA_ENV_FILE_REQUIRED)

    gen = LicenseGenerator()
    gen.add_licenses(args.conda_env_file)
    gen.write_licenses_file(args.output_folder)

ENTRY_FUNCTION = get_licenses
