"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""

import os
import sys
from itertools import product

try:
    import conda_build.api
    from conda_build.config import get_or_merge_config
except ImportError as error:
    print("Cannot find `conda_build`, please see https://github.com/open-ce/open-ce#requirements"
          " for a list of requirements.")
    sys.exit(1)

import utils
import env_config
import build_feedstock
from utils import OpenCEError

DEFAULT_GIT_LOCATION = "https://github.com/open-ce"

class BuildCommand():
    """
    The BuildCommand class holds all of the information needed to call the build_feedstock
    function a single time.
    """
    #pylint: disable=too-many-instance-attributes,too-many-arguments
    def __init__(self,
                 recipe,
                 repository,
                 packages,
                 python=None,
                 build_type=None,
                 run_dependencies=None,
                 host_dependencies=None,
                 build_dependencies=None,
                 test_dependencies=None,
                 channels=None,
                 build_command_dependencies=None):
        self.recipe = recipe
        self.repository = repository
        self.packages = packages
        self.python = python
        self.build_type = build_type
        self.run_dependencies = run_dependencies
        self.host_dependencies = host_dependencies
        self.build_dependencies = build_dependencies
        self.test_dependencies = test_dependencies
        self.channels = channels
        self.build_command_dependencies = build_command_dependencies

    def feedstock_args(self):
        """
        Returns a list of strings that can be provided to the build_feedstock function to
        perform a build.
        """
        build_args = ["--working_directory", self.repository]

        for channel in self.channels:
            build_args += ["--channels", channel]

        build_args += ["--python_versions", self.python]
        build_args += ["--build_types", self.build_type]

        if self.recipe:
            build_args += ["--recipes", self.recipe]

        return build_args

    def name(self):
        """
        Returns a name representing the Build Command
        """
        result = self.recipe
        if self.python:
            result +=  "-py" + self.python
        if self.build_type:
            result +=  "-" + self.build_type
        return result

def _make_hash(to_hash):
    '''Generic hash function.'''
    return hash(str(to_hash))

def _create_recipes(repository, recipes, variant_config_files, variants, channels):
    """
    Create a recipe dictionary for each recipe within a repository. The dictionary
    will have all of the information needed to build the recipe, as well as to
    create the dependency tree.
    """
    saved_working_directory = os.getcwd()
    os.chdir(repository)

    config_data, _ = build_feedstock.load_package_config()
    outputs = []
    for recipe in config_data.get('recipes', []):
        if recipes and not recipe.get('name') in recipes:
            continue
        packages, run_deps, host_deps, build_deps, test_deps = _get_package_dependencies(recipe.get('path'),
                                                                                         variant_config_files,
                                                                                         variants)
        outputs.append(BuildCommand(recipe=recipe.get('name', None),
                                    repository=repository,
                                    packages=packages,
                                    python=variants['python'],
                                    build_type=variants['build_type'],
                                    run_dependencies=run_deps,
                                    host_dependencies=host_deps,
                                    build_dependencies=build_deps,
                                    test_dependencies=test_deps,
                                    channels=channels if channels else []))

    os.chdir(saved_working_directory)
    return outputs

def _get_package_dependencies(path, variant_config_files, variants):
    """
    Return a list of output packages and a list of dependency packages
    for the recipe at a given path. Uses conda-render to determine this information.
    """
    # Call conda-build's render tool to get a list of dictionaries representing
    # the recipe for each variant that will be built.
    config = get_or_merge_config(None)
    config.variant_config_files = variant_config_files
    config.verbose = False
    metas = conda_build.api.render(path,
                                   config=config,
                                   variants=variants,
                                   bypass_env_check=True,
                                   finalize=False)

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
        if 'test' in meta.meta:
            test_deps.update(meta.meta['test'].get('requires', []))

    return packages, run_deps, host_deps, build_deps, test_deps

def _add_build_command_dependencies(build_commands, start_index=0):
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
    for index, build_command in enumerate(build_commands):
        for package in build_command.packages:
            packages.update({ package : [start_index + index] + packages.get(package, []) })

    # Add a list of indices for dependency to a BuildCommand's `build_command_dependencies` value
    # Note: This will filter out all dependencies that aren't in the recipes list.
    for index, build_command in enumerate(build_commands):
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

class BuildTree():
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

    #pylint: disable=too-many-arguments 
    def __init__(self,
                 env_config_files,
                 python_versions,
                 build_types,
                 repository_folder="./",
                 git_location=DEFAULT_GIT_LOCATION,
                 git_tag_for_env="master",
                 conda_build_config=utils.DEFAULT_CONDA_BUILD_CONFIG):

        self._env_config_files = env_config_files
        self._repository_folder = repository_folder
        self._git_location = git_location
        self._git_tag_for_env = git_tag_for_env
        self._conda_build_config = conda_build_config

        # Create a dependency tree that includes recipes for every combination
        # of variants.
        variants = { 'python' : utils.parse_arg_list(python_versions),
                     'build_type' : utils.parse_arg_list(build_types) }
        variant_cart_product = [dict(zip(variants,y)) for y in product(*variants.values())]
        self.build_commands = []
        for variant in variant_cart_product:
            result, variant_recipes = self._create_all_recipes(variant)
            if result != 0:
                raise OpenCEError("Error creating Build Tree")

            # Add dependency tree information to the packages list
            _add_build_command_dependencies(variant_recipes, len(self.build_commands))
            self.build_commands += variant_recipes

    def _create_all_recipes(self, variants):
        '''
        Create a recipe dictionary for each recipe needed for a given environment file.
        '''

        result, env_config_data_list = env_config.load_env_config_files(self._env_config_files, variants)
        if result != 0:
            return result, []
        packages_seen = set()
        recipes = []
        # Create recipe dictionaries for each repository in the environment file
        for env_config_data in env_config_data_list:

            packages = env_config_data.get('packages', [])
            if not packages:
                packages = []
            for package in packages:
                if _make_hash(package) in packages_seen:
                    continue

                # If the feedstock value starts with https: or git@, treat it as a url. Otheriwse
                # combine with git_location and append "-feedstock.git"
                if package['feedstock'].startswith("https:") or package['feedstock'].startswith("git@"):
                    git_url = package['feedstock']
                    if not git_url.endswith(".git"):
                        git_url += ".git"
                    repository = os.path.splitext(os.path.basename(git_url))[0]
                else:
                    git_url = self._git_location + "/" + package['feedstock'] + "-feedstock.git"
                    repository = package['feedstock'] + "-feedstock"

                # Check if the directory for the feedstock already exists.
                # If it doesn't attempt to clone the repository.
                if self._repository_folder:
                    repo_dir = os.path.join(self._repository_folder, repository)
                else:
                    repo_dir = repository

                if not os.path.exists(repo_dir):
                    result = self._clone_repo(git_url, repo_dir, env_config_data, package.get('git_tag'))
                    if result != 0:
                        return result, []

                recipes += _create_recipes(repo_dir,
                                           package.get('recipes'),
                                           [os.path.abspath(self._conda_build_config)],
                                           variants,
                                           env_config_data.get('channels', None))
                packages_seen.add(_make_hash(package))
        return result, recipes

    def _clone_repo(self, git_url, repo_dir, env_config_data, git_tag_from_config):
        """
        Clone the git repo at repository.
        """
        # Priority is given to command line specified tag, if it is not
        # specified then package specific tag, and when even that is not specified
        # then top level git tag specified for env in the env file. And if nothing is
        # at all specified then fall back to default branch of the repo.

        git_tag = self._git_tag_for_env
        if git_tag is None:
            if git_tag_from_config:
                git_tag = git_tag_from_config
            else:
                git_tag = env_config_data.get('git_tag_for_env', None)

        if git_tag is None:
            clone_cmd = "git clone " + git_url + " " + repo_dir
        else:
            clone_cmd = "git clone -b " + git_tag + " --single-branch " + git_url + " " + repo_dir

        print("Clone cmd: ", clone_cmd)
        clone_result = os.system(clone_cmd)
        if clone_result != 0:
            print("Unable to clone repository: " + git_url + " " + str(clone_result))
            return 1

        return 0

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
