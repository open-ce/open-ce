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

class CondaEnvFileGenerator():
    """
    The CondaEnvData class holds all of the information needed to generate a conda
    environment file that can be used to create a conda environment from the built packages.
    """

    #pylint: disable=too-many-instance-attributes,too-many-arguments
    def __init__(self,
                 python_versions=utils.DEFAULT_PYTHON_VERS,
                 build_types=utils.DEFAULT_BUILD_TYPES,
                 mpi_types=utils.DEFAULT_MPI_TYPES,
                 cuda_versions=utils.DEFAULT_CUDA_VERS,
                 channels=None,
                 output_folder=None,
                 env_file_prefix=utils.CONDA_ENV_FILENAME_PREFIX,
                 ):
        self.python_versions = utils.parse_arg_list(python_versions)
        self.build_types = utils.parse_arg_list(build_types)
        self.mpi_types= utils.parse_arg_list(mpi_types)
        self.cuda_versions = utils.parse_arg_list(cuda_versions)
        self.env_file_prefix = env_file_prefix
        self.dependency_dict = {}
        self.channels = []
        self._initialize_dependency_dict()
        self._initialize_channels(channels, output_folder)

    def _initialize_dependency_dict(self):
        variants = utils.make_variants(self.python_versions, self.build_types, self.mpi_types, self.cuda_versions)
        for variant in variants:
            key = utils.variant_string(variant['python'], variant['build_type'], variant['mpi_type'], variant['cudatoolkit'])
            self.dependency_dict[key] = set()

    def _initialize_channels(self, channels, output_folder):
        self.channels.append("file:/" + output_folder)
        if channels is None:
            channels = []
        for channel in channels:
            self.channels.append(channel)
        self.channels.append("defaults")

    def write_conda_env_files(self, path=os.getcwd()):
        """
        This function writes conda environment files using the dependency dictionary
        created from all the buildcommands.
        """

        conda_env_files = []
        for key in self.dependency_dict:
            if len(self.dependency_dict[key]) == 0:
                continue
            if not os.path.exists(path):
                os.mkdir(path)
            conda_env_name = self.env_file_prefix + key
            conda_env_file = conda_env_name + ".yaml"
            conda_env_file = os.path.join(path, conda_env_file)
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
        if not dependencies is None:
            for dep in dependencies:
                self.dependency_dict[key].add(utils.generalize_version(dep))

    def update_conda_env_file_content(self, build_command, build_tree):
        """
        This function updates dependency dictionary for each build command with
        its dependencies both internal and external.
        """
        key = utils.variant_string(build_command.python, build_command.build_type, build_command.mpi_type,
        build_command.cudatoolkit)

        self._update_deps_lists(build_command.run_dependencies, key)
        self._update_deps_lists(build_command.packages, key)

        variant = { 'python' : build_command.python, 'build_type' : build_command.build_type,
                    'mpi_type' : build_command.mpi_type , 'cudatoolkit' : build_command.cudatoolkit}
        self._update_deps_lists(build_tree.get_external_dependencies(str(variant)), key)
