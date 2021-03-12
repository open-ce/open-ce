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
import glob
import tarfile
import zipfile
import shutil
from enum import Enum, unique, auto
import urllib.parse
from collections import defaultdict

import requests
import yaml
from jinja2 import Environment, FileSystemLoader

from open_ce import utils
from open_ce.errors import OpenCEError, Error
from open_ce.inputs import Argument, parse_arg_list

COMMAND = 'licenses'

DESCRIPTION = 'Gather license information for a group of packages'

ARGUMENTS = [Argument.OUTPUT_FOLDER, Argument.CONDA_ENV_FILE, Argument.TEMPLATE_FILES]

COPYRIGHT_STRINGS = ["Copyright", "copyright (C)", "copyright (c)"]
SECONDARY_COPYRIGHT_STRINGS = ["All rights reserved"]
EXCLUDE_STRINGS = ["Grant of Copyright License", "Copyright [y", "Copyright {y",
                   "Copyright (C) <y", "\"Copyright", "Copyright (C) year",
                   "Copyright Notice", "the Copyright", "Our Copyright",
                   "Copyright (c) <y", "our Copyright", "Copyright and", "Copyright remains",
                   "Copyright (C) ____", "Copyright laws", "Copyright Treaty",
                   "Copyright to"]
CONNECTOR_STRINGS = [",", "and", "by"]

@unique
class Key(Enum):
    '''Enum for Open-CE Info Keys'''
    third_party_packages = auto()
    name = auto()
    version = auto()
    license = auto()
    url = auto()
    license_url = auto()
    copyright_string = auto()

_THIRD_PARTY_PACKAGE_SCHEMA ={
    Key.name.name: utils.make_schema_type(str, True),
    Key.version.name: utils.make_schema_type(str, True),
    Key.license.name: utils.make_schema_type(str, True),
    Key.url.name: utils.make_schema_type([str], True),
    Key.license_url.name: utils.make_schema_type(str),
    Key.copyright_string.name: utils.make_schema_type(str),
}

_OPEN_CE_INFO_SCHEMA = {
    Key.third_party_packages.name: utils.make_schema_type([_THIRD_PARTY_PACKAGE_SCHEMA]),
}

class LicenseGenerator():
    """
    The LicenseGenerator class is used to generate license information about all of
    the packages installed within a conda environment.
    """
    class LicenseInfo():
        """
        The LicenseInfo class holds license information for a single package.
        """
        #pylint: disable=too-many-arguments
        def __init__(self, name, version, url, license_type, copyrights):
            self.name = name
            self.version = version
            self.url = url if isinstance(url, list) else [url]
            self.license_type = _clean_license_type(license_type)
            self.copyrights = copyrights

        def __str__(self):
            return "{}\t{}\t{}\t{}\t{}".format(self.name,
                                               self.version,
                                               ", ".join(self.url),
                                               ", ".join(self.license_type),
                                               ", ".join(self.copyrights))

        def __lt__(self, other):
            return self.name + str(self.version) < other.name + str(other.version)

        def __eq__(self, other):
            return self.name + str(self.version) == other.name + str(other.version)

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

    def add_licenses_from_info_file(self, license_file):
        """
        Add all of the licensing information from an info file.
        """
        if not os.path.exists(license_file):
            return

        with open(license_file) as file_stream:
            license_data = yaml.safe_load(file_stream)

        utils.validate_dict_schema(license_data, _OPEN_CE_INFO_SCHEMA)

        for package in license_data.get(Key.third_party_packages.name, []):
            source_folder = os.path.join(utils.TMP_LICENSE_DIR,
                                         package[Key.name.name] + "-" + str(package[Key.version.name]))
            if not os.path.exists(source_folder):
                os.makedirs(source_folder)

                urls = [package[Key.license_url.name]] if Key.license_url.name in package else package[Key.url.name]

                # Download the source from each URL
                for url in urls:
                    if url.endswith(".git"):
                        try:
                            utils.git_clone(url, package[Key.version.name], source_folder)
                        except OpenCEError:
                            print("Unable to clone source for " + package[Key.name.name])
                    else:
                        try:
                            res = requests.get(url)
                            local_path = os.path.join(source_folder, os.path.basename(url))
                            with open(local_path, 'wb') as file_stream:
                                file_stream.write(res.content)
                            _extract(local_path, source_folder)

                        #pylint: disable=broad-except
                        except Exception:
                            print("Unable to download source for " + package[Key.name.name])

            # Find every license file within the downloaded source
            license_files = _find_license_files(source_folder)

            # Get copyright information from the downloaded source (unless the copyright string is provided)
            if Key.copyright_string.name in package:
                copyright_string = [package[Key.copyright_string.name]]
            else:
                copyright_string = _get_copyrights_from_files(license_files)

            info = LicenseGenerator.LicenseInfo(package[Key.name.name],
                                                package[Key.version.name],
                                                package[Key.url.name],
                                                package[Key.license.name],
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

    def gen_file_from_template(self, template, output_folder):
        """
        Fill in a jinja template file with license information and
        write the new file into the provided output_folder.
        """
        # Create dictionary with license_type as key
        license_dict = defaultdict(list)
        for info in self._licenses:
            for license_type in info.license_type:
                license_dict[license_type].append(info)

        file_loader = FileSystemLoader(os.path.dirname(template))
        env = Environment(loader=file_loader)
        jinja_template = env.get_template(os.path.basename(template))
        output = jinja_template.render(licenseInfo=license_dict)

        output_name = os.path.splitext(os.path.basename(template))[0] + ".txt"
        with open(os.path.join(output_folder, output_name), 'w') as stream:
            stream.write(output)

    def _add_licenses_from_environment(self, conda_env):
        # For each meta-pkg within an environment, find its about.json file.
        meta_files = [meta_file for meta_file in os.listdir(os.path.join(conda_env, "conda-meta"))
                          if meta_file.endswith('.json')]

        for meta_file in meta_files:
            # Find the extracted_package_dir
            with open(os.path.join(conda_env, "conda-meta", meta_file)) as file_stream:
                meta_data = json.load(file_stream)

            package_info_dir = os.path.join(meta_data["extracted_package_dir"], "info")
            with open(os.path.join(package_info_dir, "about.json")) as file_stream:
                about_data = json.load(file_stream)

            open_ce_info = os.path.join(package_info_dir, "recipe", utils.OPEN_CE_INFO_FILE)
            self.add_licenses_from_info_file(open_ce_info)

            info = LicenseGenerator.LicenseInfo(meta_data["name"],
                                                meta_data["version"],
                                                about_data.get("dev_url", about_data.get("home", "none")),
                                                about_data.get("license", "none"),
                                                _get_copyrights_from_conda_package(meta_data["extracted_package_dir"]))
            self._licenses.add(info)

        if os.path.exists(utils.TMP_LICENSE_DIR):
            shutil.rmtree(utils.TMP_LICENSE_DIR)

def _get_copyrights_from_conda_package(pkg_dir):
    """
    Find all of the Copyright infomation for a conda package
    """
    license_files = set()

    # Get every file in the licenses directory
    for root, _, files in os.walk(os.path.join(pkg_dir, "info", "licenses")):
        for file in files:
            license_files.add(os.path.join(root,file))

    # Get every file within the package directory that might be a license file
    search_dirs = [os.path.join(pkg_dir, "info"),
                   os.path.join(pkg_dir, "site-packages", "*-info"),
                   os.path.join(pkg_dir, "lib", "python*", "site-packages", "*-info")]
    potential_files = ["*LICENSE*", "*COPYING*"]
    for search_dir in search_dirs:
        for potential_file in potential_files:
            license_files.update(glob.glob(os.path.join(search_dir, potential_file)))

    if not license_files:
        # Find license files within source code of package
        source_folder = _get_source_from_conda_package(pkg_dir)
        license_files.update(_find_license_files(source_folder))

    return _get_copyrights_from_files(license_files)

def _get_source_from_conda_package(pkg_dir):
    """
    Download the source for a conda package
    """
    #pylint: disable=import-outside-toplevel
    import conda_build.source
    source_folder = os.path.join(utils.TMP_LICENSE_DIR, os.path.basename(pkg_dir))
    if not os.path.exists(source_folder):
        os.makedirs(source_folder)

        # Find the recipe's meta.yaml file and download the values within the "source" field.
        with open(os.path.join(pkg_dir, "info", "recipe", "meta.yaml")) as file_stream:
            recipe_data = yaml.safe_load(file_stream)

        if not recipe_data.get("source"):
            return source_folder

        sources = recipe_data["source"]
        if not isinstance(sources, list):
            sources = [sources]

        for source in sources:
            # If the source comes from a url, use conda-build's download_to_cache function.
            if source.get("url"):
                try:
                    local_path, _ = conda_build.source.download_to_cache(source_folder, pkg_dir, source, False)
                    _extract(local_path, source_folder)
                except RuntimeError:
                    print("Unable to download source for " + os.path.basename(pkg_dir))
            elif source.get("git_url"):
                git_url = source["git_url"]
                try:
                    utils.git_clone(git_url, source.get("git_rev"), source_folder)
                except OpenCEError as error:
                    try:
                        # If the URL is from a private GIT server, try and use an equivalent URL on GitHub
                        parsed_url = urllib.parse.urlsplit(git_url)
                        netloc = parsed_url.netloc.split(".")
                        if netloc[0] == "git":
                            parsed_url = parsed_url._replace(netloc="github.com")
                            parsed_url = parsed_url._replace(path=os.path.join(netloc[1], os.path.basename(parsed_url.path)))
                            git_url = urllib.parse.urlunsplit(parsed_url)
                            utils.git_clone(git_url, source.get("git_rev"), source_folder)
                        else:
                            raise error
                    except OpenCEError:
                        print("Unable to clone source for " + os.path.basename(pkg_dir))

    return source_folder

def _extract(archive, destination):
    """
    Extract the contents of an archive
    """
    if tarfile.is_tarfile(archive):
        tar_file = tarfile.open(archive)
        tar_file.extractall(destination)
        tar_file.close()
    elif zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive, 'r') as zip_stream:
            zip_stream.extractall(destination)

def _find_license_files(directory):
    """
    Find all of the possible license files within a directory.
    """
    license_files = []

    license_files += glob.glob(os.path.join(directory, "**", "*LICENSE*"), recursive=True)
    license_files += glob.glob(os.path.join(directory, "**", "*LICENCE*"), recursive=True)
    license_files += glob.glob(os.path.join(directory, "**", "*COPYING*"), recursive=True)
    license_files += glob.glob(os.path.join(directory, "**", "*CopyrightNotice*"), recursive=True)
    license_files += glob.glob(os.path.join(directory, "**", "*d.ts"), recursive=True)

    return license_files

def _get_copyrights_from_files(license_files):
    """
    Get all of the copyright notifications from a list of files.
    """
    copyright_notices = []
    for license_file in license_files:
        # If the license_file is a folder, skip it
        if not os.path.isfile(license_file):
            continue
        # Special case for TypeScript files
        if license_file.endswith(".d.ts"):
            copyright_notices += _get_copyrights_from_ts(license_file)
            continue
        with open(license_file, 'r', errors='ignore') as file_stream:
            just_found = False
            for line in file_stream.readlines():
                if any(copyright in line for copyright in COPYRIGHT_STRINGS) and \
                       all(not exclude in line for exclude in EXCLUDE_STRINGS):
                    cleaned_line = _clean_copyright_string(line)
                    copyright_notices.append(cleaned_line)
                    just_found = True
                # Look for lines that come just after a copyright notification
                elif just_found and (any(copyright in line for copyright in SECONDARY_COPYRIGHT_STRINGS) or
                                     any(copyright_notices[-1].endswith(connector) for connector in CONNECTOR_STRINGS)):
                    copyright_notices[-1] = copyright_notices[-1] + " " + _clean_copyright_string(line, primary=False)
                else:
                    just_found = False

    # Remove duplicates
    return list(dict.fromkeys(copyright_notices))

def _get_copyrights_from_ts(ts_file):
    """
    Get copyright information from a TypeScript file.

    Assumes that copyright information is in the form:
    // Definitions by: owner1
    //                 owner2
    //                 owner3
    // Definitions:
    """
    ts_start = "// Definitions by:"
    ts_end = "// Definitions:"
    copyrights = []
    with open(ts_file, 'r') as file_stream:
        for line in file_stream.readlines():
            if line.startswith(ts_start):
                copyrights.append("Copyright " + line[len(ts_start):].strip())
            elif line.startswith(ts_end):
                break
            elif copyrights:
                copyrights.append("Copyright " + line[2:].strip())
    return copyrights

def _clean_copyright_string(copyright_str, primary=True):
    """
    Clean a copyright string.
    """
    copyright_str = copyright_str.strip()
    copyright_index = -1
    for index, char in enumerate(copyright_str):
        if char.isalnum():
            copyright_index = index
            break
    if copyright_index < 0:
        return ""
    copyright_str = copyright_str[copyright_index:]

    if primary:
        for copyright_start in COPYRIGHT_STRINGS:
            copyright_index = copyright_str.find(copyright_start)
            if copyright_index >= 0:
                return copyright_str[copyright_index:]

    return copyright_str

def _clean_license_type(license_str):
    license_types =[("BSD-3-Clause", ["3-clause BSD", "BSD 3-Clause", "BSD-3-Clause", "BSD-3-clause",
                                      "BSD 3-clause", "BSD 3 Clause", "BSD3", "modified 3-clause BSD",
                                      "Google"]),
                    ("BSD-2-Clause", ["3-clause BSD", "BSD 2-Clause", "BSD-2-Clause", "BSD-2-clause",
                                      "BSD 2-clause", "BSD 2 Clause", "BSD2", "New BSD License"]),
                    ("BSD", ["BSD", "BSD Like"]),
                    ("Boost", ["BSL", "Boost", "BSL (Boost)"]),
                    ("Apache-2.0", ["Apache 2.0", "Apache License 2.0", "Apache-2", "apache-2", "Apache-2.0"]),
                    ("Curl", ["curl", "Curl", "MIT/X derivate (http://curl.haxx.se/docs/copyright.html)"]),
                    ("Eclipse", ["EPL", "Eclipse", "EPL (eclipse)"]),
                    ("FreeType", ["LicenseRef-FreeType", "FreeType"]),
                    ("MIT", ["MIT", "MIT License", "Free software (MIT-like)"]),
                    ("MPL-1.1", ["MPL-1.1", "MPL 1.1", "MPLv1.1", "Mozilla 1.1"]),
                    ("MPL-2.0", ["MPL", "MPL-2.0", "MPL 2.0", "MPLv2.0", "Mozilla", "Mozilla 2.0"]),
                    ("OpenLDAP", ["OpenLDAP", "OpenLDAP Public License"]),
                    ("PIL", ["PIL", "LicenseRef-PIL"]),
                    ("PSF-2.0", ["PSF", "PSF-2.0", "Python-2.0", "LicenseRef-PSF-based"]),
                    ("ZLIB", ["ZLIB", "zlib", "zlib/libpng"]),
                    ("GPL-2.0", ["GPL-2.0", "GPL-2.0-only", "GPL-2.0-or-later", "GPLv2", "GPL 2"]),
                    ("GPL-3.0", ["GPL-3.0", "GPL-3.0-only", "GPL-3.0-or-later", "GPLv3", "GPL 3"]),
                    ("LGPL-2.1", ["LGPL-2.1", "LGPL 2.1", "LGPL2", "LGPLv2", "LGPLv2.1", "LGPL-2.1-or-later"]),
                    ("LGPL-3.0", ["LGPL-3.0", "LGPL 3.0", "LGPL3", "LGPLv3", "LGPLv3.0", "LGPL-3.0-or-later"])]
    separators = [",", " AND ", " and ", " OR ", " or "]

    # Split up license types within a string if there are multiple license types provided.
    for separator in separators:
        licenses = license_str.split(separator)
        if len(licenses) > 1:
            result = []
            for lic_type in licenses:
                result += _clean_license_type(lic_type)
            return result

    # Convert variant names of different license types to a single value,
    # based on the table within license_types.
    license_str = license_str.strip()
    for license_type, potentials in license_types:
        if license_str in potentials:
            return [license_type]

    return [license_str]

def get_licenses(args):
    """
    Entry point for `get licenses`.
    """
    if not args.conda_env_files:
        raise OpenCEError(Error.CONDA_ENV_FILE_REQUIRED)

    gen = LicenseGenerator()

    for conda_env_file in parse_arg_list(args.conda_env_files):
        gen.add_licenses(conda_env_file)

    gen.write_licenses_file(args.output_folder)

    if args.template_files:
        for template_file in parse_arg_list(args.template_files):
            gen.gen_file_from_template(template_file, args.output_folder)

ENTRY_FUNCTION = get_licenses
