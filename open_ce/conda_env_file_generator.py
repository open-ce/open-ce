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

import os

import open_ce.utils as utils

#pylint: disable=too-few-public-methods
class CondaEnvFileGenerator():
    """
    The CondaEnvData class holds all of the information needed to generate a conda
    environment file that can be used to create a conda environment from the built packages.
    """

    def __init__(self,
                 dependencies,
                 ):
        self._dependency_set = dependencies

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

        It returns the path to the file that was written.
        """
        #pylint: disable=import-outside-toplevel
        import yaml

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
            outfile.write("#" + utils.OPEN_CE_VARIANT + ":" + variant_string + "\n")
            yaml.dump(data, outfile, default_flow_style=False)
            file_name = conda_env_file

        return file_name

def get_variant_string(conda_env_file):
    """
    Return the variant string from a conda environment file that was added by CondaEnvFileGenerator.
    If a variant string was not added to the conda environment file, None will be returned.
    """
    with open(conda_env_file, 'r') as stream:
        first_line = stream.readline().strip()[1:]
        values = first_line.split(':')
        if values[0] == utils.OPEN_CE_VARIANT:
            return values[1]

    return None


def _create_channels(channels, output_folder):
    result = []

    result.append("file:/" + output_folder)
    if channels:
        result += channels
    result.append("defaults")

    return result
