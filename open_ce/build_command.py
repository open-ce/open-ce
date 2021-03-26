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
from open_ce import utils

class BuildCommand():
    """
    The BuildCommand class holds all of the information needed to call the build_feedstock
    function a single time.
    """
    #pylint: disable=too-many-instance-attributes,too-many-arguments,too-many-locals
    def __init__(self,
                 recipe,
                 repository,
                 packages,
                 version=None,
                 recipe_path=None,
                 runtime_package=True,
                 output_files=None,
                 python=None,
                 build_type=None,
                 mpi_type=None,
                 cudatoolkit=None,
                 run_dependencies=None,
                 host_dependencies=None,
                 build_dependencies=None,
                 test_dependencies=None,
                 channels=None):
        self.recipe = recipe
        self.repository = repository
        self.packages = packages
        self.version = version
        self.recipe_path = recipe_path
        self.runtime_package = runtime_package
        self.output_files = output_files
        if not self.output_files:
            self.output_files = []
        self.python = python
        self.build_type = build_type
        self.mpi_type = mpi_type
        self.cudatoolkit = cudatoolkit
        self.run_dependencies = run_dependencies
        self.host_dependencies = host_dependencies
        self.build_dependencies = build_dependencies
        self.test_dependencies = test_dependencies
        self.channels = channels

    def feedstock_args(self):
        """
        Returns a list of strings that can be provided to the build_feedstock function to
        perform a build.
        """
        build_args = ["--working_directory", self.repository]

        if self.channels:
            for channel in self.channels:
                build_args += ["--channels", channel]

        if self.python:
            build_args += ["--python_versions", self.python]
        if self.build_type:
            build_args += ["--build_types", self.build_type]
        if self.mpi_type:
            build_args += ["--mpi_types", self.mpi_type]
        if self.cudatoolkit:
            build_args += ["--cuda_versions", self.cudatoolkit]


        if self.recipe:
            build_args += ["--recipes", self.recipe]

        return build_args

    def all_outputs_exist(self, output_folder):
        """
        Returns true if all of the output_files already exist.
        """
        return all((os.path.exists(os.path.join(os.path.abspath(output_folder), package))
                    for package in self.output_files))

    def name(self):
        """
        Returns a name representing the Build Command
        """
        result = self.recipe
        variant_string = utils.variant_string(self.python, self.build_type, self.mpi_type, self.cudatoolkit)
        if variant_string:
            result += "-" + variant_string

        result = result.replace(".", "-")
        result = result.replace("_", "-")
        return result

    def __repr__(self):
        return str(self.__key())

    def __str__(self):
        return self.name()

    def __key(self):
        return (self.name(), ",".join(self.output_files))

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        if not isinstance(other, BuildCommand):
            return False
        return self.__key() == other.__key()  # pylint: disable=protected-access

    def get_all_dependencies(self):
        '''
        Return a union of all dependencies.
        '''
        return self.run_dependencies.union(self.host_dependencies, self.build_dependencies, self.test_dependencies)
