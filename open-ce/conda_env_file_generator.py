"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""

import re
import yaml
import utils

class CondaEnvFileGenerator():
    """
    The CondaEnvData class holds all of the information needed to generate a conda
    environment file while can be used to create a conda environment from the built packages.
    """

    #pylint: disable=too-many-instance-attributes,too-many-arguments
    def __init__(self,
                 python_versions=utils.DEFAULT_PYTHON_VERS,
                 build_types=utils.DEFAULT_BUILD_TYPES,
                 channels=None,
                 output_folder=None,
                 ):
        self.python_versions = python_versions
        self.build_types = build_types
        self.dependency_dict = {}
        self.channels = []
        self._initialize_dependency_dict()
        self._initialize_channels(channels, output_folder)

    def _initialize_dependency_dict(self):
        for py_version in self.python_versions:
            for build_type in self.build_types:
                key = "py" + py_version + "-" + build_type
                self.dependency_dict[key] = set()
        print("Dep list: ", self.dependency_dict.keys())

    def _initialize_channels(self, channels, output_folder):
        self.channels.append("file:/" + output_folder)
        if channels:
            self.channels.append(channels)
        self.channels.append("defaults")

    def write_conda_env_files(self):
        """
        This function writes conda environment files using the dependency dictionary
        created from all the buildcommands.
        """

        conda_env_files = []
        for key in self.dependency_dict:
            if len(self.dependency_dict[key]) == 0:
                continue
            conda_env_name = "opence-" + key
            conda_env_file = conda_env_name + ".yaml"
            data = dict(
                name = conda_env_name,
                channels = self.channels,
                dependencies = self.dependency_dict[key],
            )
            with open(conda_env_file, 'w') as outfile:
                yaml.dump(data, outfile, default_flow_style=False)
                conda_env_files.append(conda_env_file)

        return conda_env_files

    def _update_deps_lists(self, dependencies, key):
        for dep in dependencies:
            self.dependency_dict[key].add(_cleanup_depstring(dep))

    def update_conda_env_file_content(self, build_command, build_tree):
        """
        This function updates dependency dictionary for each build command with
        its dependencies both internal and external.
        """

        key = "py" + build_command.python + "-" + build_command.build_type
        self._update_deps_lists(build_command.run_dependencies, key)
        self._update_deps_lists(build_command.packages, key)

        variant = { 'python' : build_command.python, 'build_type' : build_command.build_type }
        self._update_deps_lists(build_tree.get_external_dependencies(variant), key)

def _cleanup_depstring(dep_string):
    """
    This function removes extra spaces between dependency name and version.
    It also corrects python version that comes from the recipes.
    """

    dep_string = re.sub(' +', ' ', dep_string)

    # Handling case when dep_string is like "python 3.6".
    # Conda package with name "python 3.6" doesn't exist as
    # python conda package name has minor version too specified in it like 3.6.12.
    py_matched = re.match(r'(python )([=,>,<]*)(\d.*)', dep_string)
    if py_matched:
        dep_string = py_matched.group(1) + py_matched.group(2) + py_matched.group(3) + ".*"
    return dep_string
