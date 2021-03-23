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
import networkx
from open_ce import utils
from open_ce import env_config
from open_ce import validate_config
from open_ce import build_feedstock
from open_ce.errors import OpenCEError, Error
from open_ce.conda_env_file_generator import CondaEnvFileGenerator


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

class DependencyNode():
    """
    Contains information for the dependency tree.
    """
    def __init__(self,
                 packages=None,
                 build_command=None):
        self.packages = packages
        self.build_command = build_command

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "({} : {})".format(self.packages, self.build_command)

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        if not isinstance(other, DependencyNode):
            return False
        if self.build_command is not None and other.build_command is not None:
            return self.packages == other.packages and self.build_command == other.build_command
        return self.packages == other.packages

def traverse_build_commands(build_tree, starting_nodes=None, return_node=False):
    """
    Generator function that goes through a list of BuildCommand's dependency tree.
    """
    if starting_nodes is not None:
        false_start_node = "Starting Node"
        new_graph = build_tree.copy()
        new_graph.add_node(false_start_node)
        for dep in starting_nodes:
            new_graph.add_edge(false_start_node, dep)
        generator = networkx.dfs_postorder_nodes(new_graph, false_start_node)
    else:
        generator = networkx.dfs_postorder_nodes(build_tree)
    for current in generator:
        if isinstance(current, DependencyNode):
            if current.build_command is not None:
                if return_node:
                    yield current
                else:
                    yield current.build_command

def get_independent_runtime_deps(tree, node):
    """
    This function gets all run dependencies of a node that don't depend on
    any internal build commands.
    """
    deps = set()
    if node.build_command:
        run_deps = {x for x in node.build_command.run_dependencies
                                if utils.remove_version(x) not in map(utils.remove_version, node.packages)}
        for run_dep in run_deps:
            run_dep_node = next(x for x in tree.successors(node)
                                    if utils.remove_version(run_dep) in map(utils.remove_version, x.packages))
            if not {x for x in networkx.descendants(tree, run_dep_node) if x.build_command is not None}:
                deps.add(run_dep)
    return deps

def _make_hash(to_hash):
    '''Generic hash function.'''
    return hash(str(to_hash))

def _clean_dep(dep):
    return dep.lower()

def _clean_deps(deps):
    deps = [_clean_dep(dep) for dep in deps]

    return deps

def _get_package_dependencies(path, variant_config_files, variants):
    """
    Return a list of output packages and a list of dependency packages
    for the recipe at a given path. Uses conda-render to determine this information.
    """
    #pylint: disable=import-outside-toplevel
    from open_ce import conda_utils

    metas = conda_utils.render_yaml(path, variants, variant_config_files)

    # Parse out the package names and dependencies from each variant
    packages = []
    versions = []
    run_deps = set()
    host_deps = set()
    build_deps = set()
    test_deps = set()
    output_files = []
    for meta,_,_ in metas:
        packages.append(_clean_dep(meta.meta['package']['name']))
        versions.append(meta.meta['package']['version'])
        run_deps.update(_clean_deps(meta.meta['requirements'].get('run', [])))
        host_deps.update(_clean_deps(meta.meta['requirements'].get('host', [])))
        build_deps.update(_clean_deps(meta.meta['requirements'].get('build', [])))
        output_files += conda_utils.get_output_file_paths(meta, variants=variants)
        if 'test' in meta.meta:
            test_deps.update(_clean_deps(meta.meta['test'].get('requires', [])))

    return packages, versions, run_deps, host_deps, build_deps, test_deps, output_files

class BuildTree(): #pylint: disable=too-many-instance-attributes
    """
    An interable container of BuildCommands.

    Creating a BuildTree will:
    1. Clone all of the repositories listed in the provided `env_config_files`
       into the directory `repository_folder`.
    2. Build commands will be generated for each recipe listed in the provided
       `env_config_files` for each combination of python_versions and build_types.
    3. Dependency information will be added to each BuildCommand.

    Iterating over a BuildTree will always return BuildCommands before a BuildCommand
    that depends on it. Note: If there is a circular dependency within the provided
    recipes, infinite recursion can occur.
    """

    #pylint: disable=too-many-arguments, too-many-locals
    def __init__(self,
                 env_config_files,
                 python_versions,
                 build_types,
                 mpi_types,
                 cuda_versions,
                 repository_folder="./",
                 channels=None,
                 git_location=utils.DEFAULT_GIT_LOCATION,
                 git_tag_for_env=utils.DEFAULT_GIT_TAG,
                 conda_build_config=utils.DEFAULT_CONDA_BUILD_CONFIG,
                 packages=None):

        self._env_config_files = env_config_files
        self._repository_folder = repository_folder
        self._channels = channels if channels else []
        self._git_location = git_location
        self._git_tag_for_env = git_tag_for_env
        self._conda_build_config = conda_build_config
        self._external_dependencies = dict()
        self._conda_env_files = dict()
        self._test_feedstocks = dict()
        self._initial_nodes = []

        # Create a dependency tree that includes recipes for every combination
        # of variants.
        self._possible_variants = utils.make_variants(python_versions, build_types, mpi_types, cuda_versions)
        self._tree = networkx.DiGraph()
        for variant in self._possible_variants:
            try:
                variant_tree, external_deps = self._create_nodes(variant)
                variant_tree = _create_edges(variant_tree)
                variant_tree = self._create_remote_deps(variant_tree)
                self._tree = networkx.compose(self._tree, variant_tree)
            except OpenCEError as exc:
                raise OpenCEError(Error.CREATE_BUILD_TREE, exc.msg) from exc
            variant_string = utils.variant_string(variant["python"], variant["build_type"],
                                                  variant["mpi_type"], variant["cudatoolkit"])
            self._external_dependencies[variant_string] = external_deps

            self._detect_cycle()

            variant_start_nodes = {n for n,d in variant_tree.in_degree() if d==0}

            # If the packages argument is provided, find the indices into the build_commands for all
            # of the packages that were requested.
            if packages:
                for package in packages:
                    if not {n for n in variant_start_nodes if package in n.packages}:
                        print("INFO: No recipes were found for " + package + " for variant " + variant_string)
                variant_start_nodes = {n for n in variant_start_nodes if n.packages.intersection(packages)}

            self._initial_nodes += variant_start_nodes

            validate_config.validate_build_tree(self._tree, external_deps, variant_start_nodes)
            installable_packages = get_installable_packages(self._tree, external_deps, variant_start_nodes)

            filtered_packages = [package for package in installable_packages
                                     if utils.remove_version(package) in {x for node in variant_start_nodes
                                                                            for x in node.build_command.packages} or
                                        utils.remove_version(package) in utils.KNOWN_VARIANT_PACKAGES]

            self._conda_env_files[variant_string] = CondaEnvFileGenerator(filtered_packages)
            self._test_feedstocks[variant_string] = []
            for build_command in traverse_build_commands(self._tree, variant_start_nodes):
                self._test_feedstocks[variant_string].append(build_command.repository)

    def _get_repo(self, env_config_data, package):
        # If the feedstock value starts with any of the SUPPORTED_GIT_PROTOCOLS, treat it as a url. Otherwise
        # combine with git_location and append "-feedstock.git"
        feedstock_value = package[env_config.Key.feedstock.name]
        if any(feedstock_value.startswith(protocol) for protocol in utils.SUPPORTED_GIT_PROTOCOLS):
            git_url = feedstock_value
            if not git_url.endswith(".git"):
                git_url += ".git"
            repository = os.path.splitext(os.path.basename(git_url))[0]
        else:
            git_url = "{}/{}-feedstock.git".format(self._git_location, feedstock_value)

            repository = feedstock_value + "-feedstock"

        # Check if the directory for the feedstock already exists.
        # If it doesn't attempt to clone the repository.
        if self._repository_folder:
            repo_dir = os.path.join(self._repository_folder, repository)
        else:
            repo_dir = repository

        if not os.path.exists(repo_dir):
            self._clone_repo(git_url, repo_dir, env_config_data, package)

        return repo_dir

    def _create_nodes(self, variants):
        '''
        Create a recipe dictionary for each recipe needed for a given environment file.
        '''
        env_config_data_list = env_config.load_env_config_files(self._env_config_files, variants)
        feedstocks_seen = set()
        external_deps = []
        retval = networkx.DiGraph()
        # Create recipe dictionaries for each repository in the environment file
        for env_config_data in env_config_data_list:
            channels = self._channels + env_config_data.get(env_config.Key.channels.name, [])
            feedstocks = env_config_data.get(env_config.Key.packages.name, [])
            if not feedstocks:
                feedstocks = []
            for feedstock in feedstocks:
                if _make_hash(feedstock) in feedstocks_seen:
                    continue

                repo_dir = self._get_repo(env_config_data, feedstock)
                runtime_package = feedstock.get(env_config.Key.runtime_package.name, True)
                retval = networkx.compose(retval,
                                          _create_commands(repo_dir,
                                                            runtime_package,
                                                            feedstock.get(env_config.Key.recipe_path.name),
                                                            feedstock.get(env_config.Key.recipes.name),
                                                            [os.path.abspath(self._conda_build_config)],
                                                            variants,
                                                            channels))

                feedstocks_seen.add(_make_hash(feedstock))

            current_deps = env_config_data.get(env_config.Key.external_dependencies.name, [])
            if current_deps:
                external_deps += current_deps
        return retval, external_deps

    def _create_remote_deps(self, dep_graph):
        #pylint: disable=import-outside-toplevel
        from open_ce import conda_utils
        deps = {dep for dep in dep_graph.nodes() if dep.build_command is None}
        seen = set()
        try:
            while deps:
                node = deps.pop()
                for package in node.packages:
                    package_name = utils.remove_version(package)
                    if package_name in seen:
                        continue
                    seen.add(package_name)
                    package_info = conda_utils.get_latest_package_info(self._channels, package)
                    dep_graph.add_node(DependencyNode({package}))
                    for dep in package_info['depends']:
                        dep_name = utils.remove_version(dep)
                        local_dest = {dest_node for dest_node in dep_graph.nodes()
                                                if dep_name in map(utils.remove_version, dest_node.packages)}
                        if local_dest:
                            dep_graph.add_edge(node, local_dest.pop())
                        else:
                            new_dep = DependencyNode({dep})
                            dep_graph.add_edge(node, new_dep)
                            deps.add(new_dep)
            return dep_graph
        except OpenCEError as err:
            raise OpenCEError(Error.REMOTE_PACKAGE_DEPENDENCIES, deps, err.msg) from err

    def _clone_repo(self, git_url, repo_dir, env_config_data, package):
        """
        Clone the git repo at repository.
        """
        # Priority is given to command line specified tag, if it is not
        # specified then package specific tag, and when even that is not specified
        # then top level git tag specified for env in the env file. And if nothing is
        # at all specified then fall back to default branch of the repo.

        git_tag = self._git_tag_for_env
        if git_tag is None:
            git_tag_for_package = package.get(env_config.Key.git_tag.name, None) if package else None
            if git_tag_for_package:
                git_tag = git_tag_for_package
            else:
                git_tag = env_config_data.get(env_config.Key.git_tag_for_env.name, None) if env_config_data else None

        clone_successful = utils.git_clone(git_url, git_tag, repo_dir)

        if clone_successful:
            patches = package.get(env_config.Key.patches.name, []) if package else []
            if len(patches) > 0:
                cur_dir = os.getcwd()
                os.chdir(repo_dir)
                for patch in patches:
                    if os.path.isabs(patch) and os.path.exists(patch):
                        patch_file = patch
                    else:
                        # Look for patch relative to where the Open-CE environment file is
                        patch_file = os.path.join(os.path.dirname(env_config_data.get(
                                                  env_config.Key.opence_env_file_path.name)), patch)
                    patch_apply_cmd = "git apply {}".format(patch_file)
                    print("Patch apply command: ", patch_apply_cmd)
                    patch_apply_res = os.system(patch_apply_cmd)
                    if patch_apply_res != 0:
                        raise OpenCEError(Error.PATCH_APPLICATION, patch, package[env_config.Key.feedstock.name])
                os.chdir(cur_dir)

    def __iter__(self):
        """
        Generator function that goes through every recipe in a list.
        If a recipe has dependencies, those recipes will be returned
        first.
        """
        yield from traverse_build_commands(self._tree, self._initial_nodes)

    def __getitem__(self, key):
        return self._tree[key]

    def __len__(self):
        return len({x for x in self._tree.nodes() if x.build_command is not None})

    def get_external_dependencies(self, variant):
        '''Return the list of external dependencies for the given variant.'''
        variant_string = utils.variant_string(variant["python"], variant["build_type"],
                                              variant["mpi_type"], variant["cudatoolkit"])
        return self._external_dependencies.get(variant_string, [])

    def write_conda_env_files(self,
                              output_folder=None,
                              env_file_prefix=utils.CONDA_ENV_FILENAME_PREFIX,
                              path=os.getcwd()):
        """
        Write a conda environment file for each variant.
        """
        conda_env_files = dict()
        for variant, conda_env_file in self._conda_env_files.items():
            conda_env_files[variant] = conda_env_file.write_conda_env_file(variant, self._channels,
                                                                   output_folder, env_file_prefix, path)

        return conda_env_files

    def get_test_feedstocks(self, variant_string):
        """
        Return a list of feedstocks to run tests on, for a given variant.
        """
        return self._test_feedstocks[variant_string]

    def _detect_cycle(self):
        cycle_print = ""
        cycles = networkx.simple_cycles(self._tree)

        for cycle in cycles:
            if any(node.build_command for node in cycle):
                cycle_print += " -> ".join(node.build_command.recipe if node.build_command else str(node.packages)
                                                        for node in cycle + [cycle[0]]) + "\n"
        if cycle_print:
            raise OpenCEError(Error.BUILD_TREE_CYCLE, cycle_print)

def _create_edges(tree):
    # Use set() to create a copy of the nodes since they change during the loop.
    for node in set(tree.nodes()):
        if node.build_command is not None:
            for dependency in node.build_command.get_all_dependencies():
                local_dest = {dest_node for dest_node in tree.nodes()
                                        if utils.remove_version(dependency)
                                            in map(utils.remove_version, dest_node.packages)}
                if local_dest:
                    dest_node = local_dest.pop()
                    if node != dest_node:
                        tree.add_edge(node, dest_node)
                else:
                    new_node = DependencyNode({dependency})
                    tree.add_node(new_node)
                    tree.add_edge(node, new_node)
    return tree

#pylint: disable=too-many-locals,too-many-arguments
def _create_commands(repository, runtime_package, recipe_path,
                    recipes, variant_config_files, variants, channels):
    """
    Returns:
        A tree of nodes containing BuildCommands for each recipe within a repository.
    """
    retval = networkx.DiGraph()
    saved_working_directory = os.getcwd()
    os.chdir(repository)

    config_data, _ = build_feedstock.load_package_config(variants=variants, recipe_path=recipe_path)
    combined_config_files = variant_config_files

    feedstock_conda_build_config_file = build_feedstock.get_conda_build_config()
    if feedstock_conda_build_config_file:
        combined_config_files.append(feedstock_conda_build_config_file)

    recipes_from_config = config_data.get('recipes', [])
    if recipes_from_config is None:
        recipes_from_config = []
    for recipe in recipes_from_config:
        if recipes and not recipe.get('name') in recipes:
            continue
        packages, version, run_deps, host_deps, build_deps, test_deps, output_files = _get_package_dependencies(
                                                                                        recipe.get('path'),
                                                                                        combined_config_files,
                                                                                        variants)
        build_command = BuildCommand(recipe=recipe.get('name', None),
                                    repository=repository,
                                    packages=packages,
                                    version=version,
                                    recipe_path=recipe_path,
                                    runtime_package=runtime_package,
                                    output_files=output_files,
                                    python=variants['python'],
                                    build_type=variants['build_type'],
                                    mpi_type=variants['mpi_type'],
                                    cudatoolkit=variants['cudatoolkit'],
                                    run_dependencies=run_deps,
                                    host_dependencies=host_deps,
                                    build_dependencies=build_deps,
                                    test_dependencies=test_deps,
                                    channels=channels)
        package_node = DependencyNode(set(packages), build_command)
        retval.add_node(package_node)

    os.chdir(saved_working_directory)
    return retval

def get_installable_packages(build_commands, external_deps, starting_nodes=None, independent=False):
    '''
    This function retrieves the list of unique dependencies that are needed at runtime, from the
    build commands and external dependencies that are passed to it.
    '''
    retval =  set()

    def check_matching(deps_set, dep_to_be_added):
        # If exact match already present in the set, no need to add again
        if dep_to_be_added in deps_set:
            return None

        # Check only dependency name if it is present
        # For e.g. If dep_to_be_added is tensorflow-base >=2.4.* and set has tensorflow-base
        dep_name_to_be_added = dep_to_be_added.split()[0]
        if dep_name_to_be_added in deps_set and len(dep_to_be_added.split()) > 1:
            deps_set.remove(dep_name_to_be_added)
            return dep_to_be_added

        # For e.g. If set has tensorflow-base 2.4.* and dep_to_be_added is
        # either just tensorflow-base or tensorflow-base >=2.4.*
        for dep in deps_set:
            dep_name_from_set = dep.split()[0]
            if dep_name_to_be_added == dep_name_from_set:
                return None

        # If no match found, just add it
        return dep_to_be_added

    def _get_unique_deps_names(dependencies):
        deps = set()
        if dependencies:
            for dep in dependencies:
                generalized_dep = utils.generalize_version(dep)
                dep_to_update = check_matching(deps, generalized_dep)
                if dep_to_update:
                    deps.add(dep_to_update)
        return deps

    def check_and_add(dependencies, parent_set):
        dependencies = _get_unique_deps_names(dependencies)
        for dep in dependencies:
            pack_to_add = check_matching(parent_set, dep)
            if pack_to_add:
                parent_set.add(pack_to_add)

        return parent_set

    for node in traverse_build_commands(build_commands, starting_nodes, True):
        build_command = node.build_command
        if build_command.runtime_package:
            if independent:
                run_deps = get_independent_runtime_deps(build_commands, node)
            else:
                run_deps = build_command.run_dependencies
            retval = check_and_add(run_deps, retval)
            if not independent:
                retval = check_and_add([package + (" " + build_command.version[i] if build_command.version else "")
                                                        for i, package in enumerate(build_command.packages)],
                                                    retval)

    retval = check_and_add(external_deps, retval)
    return sorted(retval, key=len)
