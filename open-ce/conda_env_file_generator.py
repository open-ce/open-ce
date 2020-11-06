"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""

import os

import yaml
import utils

#pylint: disable=too-few-public-methods
class CondaEnvFileGenerator():
    """
    The CondaEnvData class holds all of the information needed to generate a conda
    environment file that can be used to create a conda environment from the built packages.
    """

    def __init__(self,
                 build_commands,
                 external_dependencies,
                 ):
        self._dependency_set = set()
        self._external_dependencies = external_dependencies

        for build_command in build_commands:
            self._update_conda_env_file_content(build_command)

    #pylint: disable=too-many-arguments
    def write_conda_env_file(self,
                             variant_string,
                             channels=None,
                             output_folder=None,
                             env_file_prefix=utils.CONDA_ENV_FILENAME_PREFIX,
                             path=utils.DEFAULT_OUTPUT_FOLDER ):
        """
        This function writes conda environment files using the dependency dictionary
        created from all the buildcommands.

        It returns a list of paths to the files that were writeen.
        """

        if not os.path.exists(path):
            os.mkdir(path)

        conda_env_name = env_file_prefix + variant_string
        conda_env_file = conda_env_name + ".yaml"
        conda_env_file = os.path.join(path, conda_env_file)

        channels = _create_channels(channels, output_folder)

        data = dict(
            name = conda_env_name,
            channels = channels,
            dependencies = self._dependency_set,
        )
        with open(conda_env_file, 'w') as outfile:
            yaml.dump(data, outfile, default_flow_style=False)
            file_name = conda_env_file

        return file_name

    def _update_deps_lists(self, dependencies):
        if not dependencies is None:
            for dep in dependencies:
                self._dependency_set.add(utils.generalize_version(dep))

    def _update_conda_env_file_content(self, build_command):
        """
        This function updates dependency dictionary for each build command with
        its dependencies both internal and external.
        """
        self._update_deps_lists(build_command.run_dependencies)
        self._update_deps_lists(build_command.packages)

        self._update_deps_lists(self._external_dependencies)

def _create_channels(channels, output_folder):
    result = []

    result.append("file:/" + output_folder)
    if channels:
        result += channels
    result.append("defaults")

    return result
