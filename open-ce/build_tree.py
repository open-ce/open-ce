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
import conda_utils
import env_config
import validate_config
import build_feedstock
from errors import OpenCEError, Error
from conda_env_file_generator import CondaEnvFileGenerator
import test_feedstock


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
                 channels=None,
                 build_command_dependencies=None):
        self.recipe = recipe
        self.repository = repository
        self.packages = packages
        self.runtime_package = runtime_package
        self.output_files = output_files
        self.python = python
        self.build_type = build_type
        self.mpi_type = mpi_type
        self.cudatoolkit = cudatoolkit
        self.run_dependencies = run_dependencies
        self.host_dependencies = host_dependencies
        self.build_dependencies = build_dependencies
        self.test_dependencies = test_dependencies
        self.channels = channels
        self.build_command_dependencies = build_command_dependencies
        if self.build_command_dependencies is None:
            self.build_command_dependencies = []

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


    def __key(self):
        return (self.recipe, self.output_files)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if not isinstance(other, BuildCommand):
            return False
        return self.__key() == other.__key()  # pylint: disable=protected-access 

def _make_hash(to_hash):
    '''Generic hash function.'''
    return hash(str(to_hash))

def _create_commands(repository, runtime_package, recipes, variant_config_files, variants, channels, test_labels):#pylint: disable=too-many-locals,too-many-arguments
    """
    Returns:
        A list of BuildCommands for each recipe within a repository.
        A list of TestCommands for an entire repository.
    """
    saved_working_directory = os.getcwd()
    os.chdir(repository)

    config_data, _ = build_feedstock.load_package_config(variants=variants)
    combined_config_files = variant_config_files

    feedstock_conda_build_config_file = build_feedstock.get_conda_build_config()
    if feedstock_conda_build_config_file:
        combined_config_files.append(feedstock_conda_build_config_file)
    build_commands = []
    recipes_from_config = config_data.get('recipes', [])
    if recipes_from_config is None:
        recipes_from_config = []
    for recipe in recipes_from_config:
        if recipes and not recipe.get('name') in recipes:
            continue
        packages, run_deps, host_deps, build_deps, test_deps, output_files = _get_package_dependencies(
                                                                                         recipe.get('path'),
                                                                                         combined_config_files,
                                                                                         variants)

        build_commands.append(BuildCommand(recipe=recipe.get('name', None),
                                    repository=repository,
                                    packages=packages,
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
                                    channels=channels if channels else []))

    variant_copy = dict(variants)
    if test_labels:
        for test_label in test_labels:
            variant_copy[test_label] = True
    test_commands = test_feedstock.gen_test_commands(variants=variant_copy)

    os.chdir(saved_working_directory)
    return build_commands, test_commands

def _get_package_dependencies(path, variant_config_files, variants):
    """
    Return a list of output packages and a list of dependency packages
    for the recipe at a given path. Uses conda-render to determine this information.
    """
    metas = conda_utils.render_yaml(path, variants, variant_config_files)

    # Parse out the package names and dependencies from each variant
    packages = set()
    run_deps = set()
    host_deps = set()
    build_deps = set()
    test_deps = set()
    for meta,_,_ in metas:
        packages.add(meta.meta['package']['name'])
        run_deps.update(meta.meta['requirements'].get('run', []))
        host_deps.update(meta.meta['requirements'].get('host', []))
        build_deps.update(meta.meta['requirements'].get('build', []))
        output_files = conda_utils.get_output_file_paths(meta, variants=variants)
        if 'test' in meta.meta:
            test_deps.update(meta.meta['test'].get('requires', []))

    return packages, run_deps, host_deps, build_deps, test_deps, output_files

def _add_build_command_dependencies(variant_build_commands, build_commands, start_index=0):
    """
    Create a dependency tree for a list of build commands.

    Each build_command will contain a `build_command_dependencies` key which contains a list of integers.
    Each integer in the list represents the index of the dependencies build_commands within the
    list.

    The start_index indicates the value that the dependency indices should start
    counting from.
    """

    # Create a packages dictionary that uses all of a recipe's packages as key, with
    # the recipes index as values.
    packages = dict()
    index = 0

    #save indices of build commands which are already present in build_commands
    duplicates = []
    for var_index, build_command in enumerate(variant_build_commands):
        if build_command in build_commands:
            alt_index = build_commands.index(build_command)
            duplicates.append(var_index)
            for package in build_command.packages:
                packages.update({ package : [alt_index] + packages.get(package, []) })
        else:
            for package in build_command.packages:
                packages.update({ package : [start_index + index] + packages.get(package, []) })
            index +=1

    # remove build commands that are already added to build_commands
    variant_build_commands = [i for j, i in enumerate(variant_build_commands) if j not in duplicates]

    # Add a list of indices for dependency to a BuildCommand's `build_command_dependencies` value
    # Note: This will filter out all dependencies that aren't in the recipes list.
    for index, build_command in enumerate(variant_build_commands):
        deps = []
        dependencies = set()
        dependencies.update({utils.remove_version(dep) for dep in build_command.run_dependencies})
        dependencies.update({utils.remove_version(dep) for dep in build_command.build_dependencies})
        dependencies.update({utils.remove_version(dep) for dep in build_command.host_dependencies})
        dependencies.update({utils.remove_version(dep) for dep in build_command.test_dependencies})
        for dep in dependencies:
            if dep in packages:
                deps += filter(lambda x: x != start_index + index, packages[dep])
        build_command.build_command_dependencies = deps

    return variant_build_commands

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
                 git_location=utils.DEFAULT_GIT_LOCATION,
                 git_tag_for_env=utils.DEFAULT_GIT_TAG,
                 conda_build_config=utils.DEFAULT_CONDA_BUILD_CONFIG,
                 test_labels=None):

        self._env_config_files = env_config_files
        self._repository_folder = repository_folder
        self._git_location = git_location
        self._git_tag_for_env = git_tag_for_env
        self._conda_build_config = conda_build_config
        self._external_dependencies = dict()
        self._conda_env_files = dict()
        self._test_commands = dict()
        self._test_labels = test_labels

        # Create a dependency tree that includes recipes for every combination
        # of variants.
        self._possible_variants = utils.make_variants(python_versions, build_types, mpi_types, cuda_versions)
        self.build_commands = []
        for variant in self._possible_variants:
            try:
                build_commands, external_deps, test_commands = self._create_all_commands(variant)
            except OpenCEError as exc:
                raise OpenCEError(Error.CREATE_BUILD_TREE, exc.msg) from exc
            variant_string = utils.variant_string(variant["python"], variant["build_type"],
                                                  variant["mpi_type"], variant["cudatoolkit"])
            self._external_dependencies[variant_string] = external_deps
            self._test_commands[variant_string] = test_commands
            validate_config.validate_build_tree(build_commands, external_deps)

            installable_packages = get_installable_packages(build_commands, external_deps)
            self._conda_env_files[variant_string] = CondaEnvFileGenerator(installable_packages)

            # Add dependency tree information to the packages list and
            # remove build commands from build_commands that are already in self.build_commands
            build_commands = _add_build_command_dependencies(build_commands, self.build_commands,
                                        len(self.build_commands))
            self.build_commands += build_commands

        self._detect_cycle()

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

        return repository, repo_dir

    def _create_all_commands(self, variants):
        '''
        Create a recipe dictionary for each recipe needed for a given environment file.
        '''

        env_config_data_list = env_config.load_env_config_files(self._env_config_files, variants)
        packages_seen = set()
        build_commands = []
        external_deps = []
        test_commands = dict()
        # Create recipe dictionaries for each repository in the environment file
        for env_config_data in env_config_data_list:

            packages = env_config_data.get(env_config.Key.packages.name, [])
            if not packages:
                packages = []
            for package in packages:
                if _make_hash(package) in packages_seen:
                    continue

                repository, repo_dir = self._get_repo(env_config_data, package)
                runtime_package = package.get(env_config.Key.runtime_package.name, True)
                repo_build_commands, repo_test_commands = _create_commands(repo_dir,
                                                            runtime_package,
                                                            package.get(env_config.Key.recipes.name),
                                                            [os.path.abspath(self._conda_build_config)],
                                                            variants,
                                                            env_config_data.get(env_config.Key.channels.name, None),
                                                            self._test_labels)

                build_commands += repo_build_commands
                if repo_test_commands and not repository in self._test_commands:
                    test_commands[repository] = repo_test_commands

                packages_seen.add(_make_hash(package))

            current_deps = env_config_data.get(env_config.Key.external_dependencies.name, [])
            if current_deps:
                external_deps += current_deps

        return build_commands, external_deps, test_commands

    #pylint: disable=too-many-branches
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

        clone_cmd = "git clone " + git_url + " " + repo_dir
        print("Clone cmd: ", clone_cmd)
        clone_result = os.system(clone_cmd)

        cur_dir = os.getcwd()
        clone_successful = clone_result == 0
        if clone_successful:
            if not git_tag is None:
                os.chdir(repo_dir)
                checkout_cmd = "git checkout " + git_tag
                print("Checkout branch/tag command: ", checkout_cmd)
                checkout_res = os.system(checkout_cmd)
                os.chdir(cur_dir)
                clone_successful = checkout_res == 0
        else:
            raise OpenCEError(Error.CLONE_REPO, git_url)

        if clone_successful:
            patches = package.get(env_config.Key.patches.name, []) if package else []
            if len(patches) > 0:
                os.chdir(repo_dir)
                for patch in patches:
                    if os.path.isabs(patch) and os.path.exists(patch):
                        patch_file = patch
                    else:
                        # Look for patch relative to where the Open-CE environment file is
                        patch_file = os.path.join(os.path.dirname(env_config_data.get(
                                                  env_config.Key.opence_env_file_path)), patch)
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
        is_seen = [False for i in range(len(self.build_commands))]
        yield from self._traverse_deps_tree(is_seen, range(len(self.build_commands)))

    def _traverse_deps_tree(self, is_seen, deps):
        """
        Generator function that goes through a recipes dependency tree.
        """
        for dep in deps:
            if is_seen[dep]:
                continue
            yield from self._traverse_deps_tree(is_seen, self.build_commands[dep].build_command_dependencies)
            yield self.build_commands[dep]
            is_seen[dep] = True

    def __getitem__(self, key):
        return self.build_commands[key]

    def __len__(self):
        return len(self.build_commands)

    def get_external_dependencies(self, variant):
        '''Return the list of external dependencies for the given variant.'''
        variant_string = utils.variant_string(variant["python"], variant["build_type"],
                                              variant["mpi_type"], variant["cudatoolkit"])
        return self._external_dependencies.get(variant_string, [])

    def write_conda_env_files(self,
                              channels=None,
                              output_folder=None,
                              env_file_prefix=utils.CONDA_ENV_FILENAME_PREFIX,
                              path=os.getcwd()):
        """
        Write a conda environment file for each variant.
        """
        conda_env_files = dict()
        for variant, conda_env_file in self._conda_env_files.items():
            conda_env_files[variant] = conda_env_file.write_conda_env_file(variant, channels,
                                                                   output_folder, env_file_prefix, path)

        return conda_env_files

    def get_test_commands(self, variant_string):
        """
        Return a dictionary of test commands, where each key is the repository name.
        """
        return self._test_commands[variant_string]

    def _detect_cycle(self, max_cycles=10):
        extract_build_tree = [x.build_command_dependencies for x in self.build_commands]
        cycles = []
        for start in range(len(self.build_commands)): # Check to see if there are any cycles that start anywhere in the tree.
            cycles += find_all_cycles(extract_build_tree, start)
            if len(cycles) >= max_cycles:
                break
        if cycles:
            cycle_print = "\n".join([" -> ".join([self.build_commands[i].recipe
                                                                    for i in cycle])
                                                                    for cycle in cycles[:min(max_cycles, len(cycles))]])
            if len(cycles) > max_cycles:
                cycle_print += "\nCycles truncated after {}...".format(max_cycles)
            raise OpenCEError(Error.BUILD_TREE_CYCLE, cycle_print)

def find_all_cycles(tree, current=0, seen=None):
    '''
    This function performs a depth first search of a tree from current, returning all cycles
    starting at current.
    '''
    if not seen:
        seen = []
    current_branch = seen + [current]
    if len(current_branch) != len(set(current_branch)):
        return [current_branch]
    result = []
    for dependency in tree[current]:
        next_step = find_all_cycles(tree, dependency, current_branch)
        if next_step:
            result += next_step
    return result

def get_installable_packages(build_commands, external_deps):
    '''
    This function retrieves the list of unique dependencies that are needed at runtime, from the
    build commands and external dependencies that are passed to it.
    '''
    installable_packages =  set()

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

    for build_command in build_commands:
        if build_command.runtime_package:
            installable_packages = check_and_add(build_command.run_dependencies, installable_packages)
            installable_packages = check_and_add(build_command.packages, installable_packages)

    installable_packages = check_and_add(external_deps, installable_packages)
    return sorted(installable_packages, key=len)
