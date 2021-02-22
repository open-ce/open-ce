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
import glob
import yaml
import tarfile
import zipfile
import requests
import shutil
from subprocess import CalledProcessError
import conda_build.source

from errors import OpenCEError, Error
from inputs import Argument

COMMAND = 'licenses'

DESCRIPTION = 'Gather license information for a group of packages'

ARGUMENTS = [Argument.OUTPUT_FOLDER, Argument.CONDA_ENV_FILE]

COPYRIGHT_STRINGS = ["Copyright", "copyright (C)"]
SECONDARY_COPYRIGHT_STRINGS = ["All rights reserved"]
EXCLUDE_STRINGS = ["Grant of Copyright License", "Copyright [y", "Copyright {y", "Copyright (C) <y", "\"Copyright", "Copyright (C) year", "Copyright Notice", "the Copyright", "Our Copyright", "Copyright (c) <y", "our Copyright", "Copyright and", "Copyright remains"]

class LicenseGenerator():
    """
    The LicenseGenerator class is used to generate license information about all of
    the packages installed within a conda environment.
    """
    class LicenseInfo():
        """
        The LicenseInfo class holds license information for a single package.
        """
        def __init__(self, name, version, url, license_type, copyrights):
            self.name = name
            self.version = version
            self.url = url
            self.license_type = license_type
            self.copyrights = copyrights

        def __str__(self):
            return "{}\t{}\t{}\t{}\t{}".format(self.name, self.version, self.url, self.license_type, ", ".join(self.copyrights))

        def __lt__(self, other):
            return self.name + str(self.version) < other.name + str(other.version)

        def __hash__(self):
            return hash(self.name + str(self.version))

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

    def add_licenses_from_file(self, license_file):
        with open(license_file) as file_stream:
            license_data = yaml.safe_load(file_stream)

        if not license_data.get("packages"):
            return

        for package in license_data.get("packages"):
            print("Downloading: " + package["name"])
            source_folder = os.path.join(utils.TMP_LICENSE_DIR, package["name"] + "-" + str(package["version"]))
            if not os.path.exists(source_folder):
                os.makedirs(source_folder)
            urls = package["license_url"] if "license_url" in package else package["url"]
            if not isinstance(urls, list):
                urls = [urls]
            for url in urls:
                if url.endswith(".git"):
                    try:
                        utils.git_clone(url, package["version"], source_folder)
                    except OpenCEError:
                        print("Unable to clone source for " + package["name"])
                else:
                    try:
                        res = requests.get(url)
                        local_path = os.path.join(source_folder, os.path.basename(url))
                        with open(local_path, 'wb') as file_stream:
                            file_stream.write(res.content)

                        if tarfile.is_tarfile(local_path):
                            tar_file = tarfile.open(local_path)
                            tar_file.extractall(source_folder)
                            tar_file.close()
                        elif zipfile.is_zipfile(local_path):
                            with zipfile.ZipFile(local_path, 'r') as zip_stream:
                                zip_stream.extractall(source_folder)

                    except Exception:
                        print("Unable to download source for " + package["name"])

            license_files = []

            license_files += glob.glob(os.path.join(source_folder, "**", "*LICENSE*"), recursive=True)
            license_files += glob.glob(os.path.join(source_folder, "**", "*LICENCE*"), recursive=True)
            license_files += glob.glob(os.path.join(source_folder, "**", "*COPYING*"), recursive=True)
            license_files += glob.glob(os.path.join(source_folder, "**", "*d.ts"), recursive=True)

            if "copyright_string" in package:
                copyright_string = [package["copyright_string"]]
            else:
                copyright_string = self._get_copyrights_from_files(license_files)

            info = LicenseGenerator.LicenseInfo(package["name"],
                                                package["version"],
                                                package["url"],
                                                package["license"],
                                                copyright_string)
            self._licenses.add(info)

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

    def _get_source(self, pkg_dir):
        source_folder = os.path.join(utils.TMP_LICENSE_DIR, os.path.basename(pkg_dir))
        if not os.path.exists(source_folder):
            os.makedirs(source_folder)

        with open(os.path.join(pkg_dir, "info", "recipe", "meta.yaml")) as file_stream:
            recipe_data = yaml.safe_load(file_stream)

        if not recipe_data.get("source"):
            return source_folder

        sources = recipe_data["source"]
        if not isinstance(sources, list):
            sources = [sources]

        for source in sources:
            if source.get("url"):
                try:
                    local_path, _ = conda_build.source.download_to_cache(source_folder, pkg_dir, source, False)
                    if tarfile.is_tarfile(local_path):
                        tar_file = tarfile.open(local_path)
                        tar_file.extractall(source_folder)
                        tar_file.close()
                except RuntimeError:
                    print("Unable to download source for " + pkg_dir)
            elif source.get("git_url"):
                try:
                    utils.git_clone(source["git_url"], source.get("git_rev"), source_folder)
                except OpenCEError:
                    print("Unable to clone source for " + pkg_dir)

        return source_folder

    def _get_copyrights(self, meta_data, about_data):
        license_files = set()
        pkg_dir = meta_data["extracted_package_dir"]

        # Get every file in the licenses directory
        for root, _, files in os.walk(os.path.join(pkg_dir, "info", "licenses")):
            for file in files:
                license_files.add(os.path.join(root,file))

        # Get every file within the package directory with LICENSE in its name
        license_files.update(glob.glob(os.path.join(pkg_dir, "info", "*LICENSE*")))
        license_files.update(glob.glob(os.path.join(pkg_dir, "info", "*COPYING*")))
        #license_files.update(glob.glob(os.path.join(pkg_dir, "**", "*LICENSE*"), recursive=True))

        if not license_files:
            source_folder = self._get_source(pkg_dir)
            license_files.update(glob.glob(os.path.join(source_folder, "**", "*LICENSE*"), recursive=True))
            license_files.update(glob.glob(os.path.join(source_folder, "**", "*COPYING*"), recursive=True))

        if not license_files:
            return "Missing File"

        return self._get_copyrights_from_files(license_files)

    def _get_copyrights_from_ts(self, ts_file):
        ts_start = "// Definitions by:"
        ts_end = "// Definitions:"
        copyrights = []
        with open(ts_file, 'r') as file_stream:
            for line in file_stream.readlines():
                if line.startswith(ts_start):
                    copyrights.append("Copyright " + line[len(ts_start):].strip())
                elif line.startswith(ts_end):
                    return copyrights
                elif copyrights:
                    copyrights.append("Copyright " + line[2:].strip())
        return copyrights
    
    def _clean_copyright_string(self, copyright, primary=True):
        copyright_str = copyright.strip()
        copyright_index = copyright_str.find(next(filter(str.isalpha, copyright_str)))
        copyright_str = copyright_str[copyright_index:]
        
        if primary:
            for copyright in COPYRIGHT_STRINGS:
                copyright_index = copyright_str.find(copyright)
                if copyright_index >= 0:
                  return copyright_str[copyright_index:]

        return copyright_str

    def _get_copyrights_from_files(self, license_files):
        copyright_notices = []
        for license_file in license_files:
            if not os.path.isfile(license_file):
                continue
            if license_file.endswith(".d.ts"):
                copyright_notices += self._get_copyrights_from_ts(license_file)
                continue  
            with open(license_file, 'r', errors='ignore') as file_stream:
                just_found = False
                for line in file_stream.readlines():
                    if any(copyright in line for copyright in COPYRIGHT_STRINGS) and all(not exclude in line for exclude in EXCLUDE_STRINGS):
                        cleaned_line = self._clean_copyright_string(line)
                        #if any(cleaned_line.startswith(copyright) for copyright in COPYRIGHT_STRINGS):
                        copyright_notices.append(cleaned_line)
                        just_found = True
                    elif just_found and any(copyright in line for copyright in SECONDARY_COPYRIGHT_STRINGS):
                        copyright_notices[-1] = copyright_notices[-1] + " " + self._clean_copyright_string(line, primary=False)
                    else:
                        just_found = False

        return list(copyright_notices)

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
                                                about_data.get("license", "none"),
                                                self._get_copyrights(meta_data, about_data))
            self._licenses.add(info)

        if os.path.exists(utils.TMP_LICENSE_DIR):
            shutil.rmdir(utils.TMP_LICENSE_DIR)


def get_licenses(args):
    """
    Entry point for `get licenses`.
    """
    #if not args.conda_env_file:
    #    raise OpenCEError(Error.CONDA_ENV_FILE_REQUIRED)

    gen = LicenseGenerator()
    #gen.add_licenses(args.conda_env_file)
    gen.add_licenses_from_file("static.yaml")
    gen.write_licenses_file(args.output_folder)

ENTRY_FUNCTION = get_licenses

