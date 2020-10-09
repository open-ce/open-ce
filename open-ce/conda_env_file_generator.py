"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""

import os
import utils

class CondaEnvFileGenerator():
    """
    The CondaEnvData class holds all of the information needed to generate a conda
    environment file while can be used to create a conda environment from the built packages.
    """

    def _initialize_dependency_dict():
        for py_version in python_versions:
            for build_type in build_types:
                key = "py" + py_version + "-" + build_type
                self._dependency_dict[key] = set()
        print("Dep list: ", self._dependency_dict.keys())

    def _initialize_channels(channels, output_folder):
        self._channels.append("file:/" + output_folder)
        self._channels.append("defaults")

    #pylint: disable=too-many-instance-attributes,too-many-arguments
    def __init__(self,
                 python_versions=utils.DEFAULT_PYTHON_VERS,
                 build_types=utils.DEFAULT_BUILD_TYPES,
                 channels=None,
                 output_folder=None,
                 ):
        self.python_versions = python_versions
        self.build_types = build_types
        _initialize_dependency_dict()
        _initialize_channels(channels, output_folder)

    def write_conda_env_files():
        conda_env_files = []
        for key in self._dependency_dict.keys():
            conda_env_name = "opence-" + key
            conda_env_file = conda_env_name + ".yaml"

            data = dict(
                name = conda_env_name,
                channels = self._channels,
                dependencies = self._dependency_dict[key],
            )
            with open(conda_env_file, 'w') as outfile:
                yaml.dump(data, outfile, default_flow_style=False)
                conda_env_files.append(conda_env_file)

        return conda_env_files

    def _cleanup_depstring(dep_string):
        dep_string = re.sub(' +', ' ', dep_string)

        # Handling case when dep_string is like "python 3.6".
        # Conda package with name "python 3.6" doesn't exist as
        # python conda package name has minor version too specified in it like 3.6.12.
        m = re.match(r'(python )([=,>,<]*)(\d.*)', dep_string)
        if m:
            dep_string = m.group(1) + m.group(2) + m.group(3) + ".*"
        return dep_string

    def _update_deps_lists(dependencies, key):
        for dep in dependencies:
            self._dependency_dict[key].add(cleanup_depstring(dep))

    def update_conda_env_file_content(build_command, build_tree):

        key = "py" + build_command.python + "-" + build_command.build_type
        _update_deps_lists(build_command.run_dependencies, key)
        _update_deps_lists(build_command.packages, key)

        variant = { 'python' : build_command.python, 'build_type' : build_command.build_type }
        update_deps_lists(build_tree.get_external_dependencies(variant), key)
 
