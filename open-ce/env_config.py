"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""

import os
from enum import Enum, unique, auto

import utils
from errors import OpenCEError, Error

utils.check_if_conda_build_exists()
import conda_utils  # pylint: disable=wrong-import-position, wrong-import-order

@unique
class Key(Enum):
    '''Enum for Env Config Keys'''
    imported_envs = auto()
    channels = auto()
    packages = auto()
    git_tag_for_env = auto()
    git_tag = auto()
    feedstock = auto()
    recipes = auto()
    external_dependencies = auto()

_PACKAGE_SCHEMA ={
    Key.feedstock.name: utils.make_schema_type(str, True),
    Key.git_tag.name: utils.make_schema_type(str),
    Key.recipes.name: utils.make_schema_type([str]),
    Key.channels.name: utils.make_schema_type([str])
}

_ENV_CONFIG_SCHEMA = {
    Key.imported_envs.name: utils.make_schema_type([str]),
    Key.channels.name: utils.make_schema_type([str]),
    Key.git_tag_for_env.name: utils.make_schema_type(str),
    Key.external_dependencies.name: utils.make_schema_type([str]),
    Key.packages.name: utils.make_schema_type([_PACKAGE_SCHEMA])
}

def _validate_config_file(env_file, variants):
    '''Perform some validation on the environment file after loading it.'''
    try:
        meta_obj = conda_utils.render_yaml(env_file, variants=variants)
        if not (Key.packages.name in meta_obj.keys() or Key.imported_envs.name in meta_obj.keys()):
            raise OpenCEError(Error.CONFIG_CONTENT)
        utils.validate_dict_schema(meta_obj, _ENV_CONFIG_SCHEMA)
        return meta_obj
    except (Exception, SystemExit) as exc: #pylint: disable=broad-except
        raise OpenCEError(Error.ERROR, "Error in {}:\n  {}".format(env_file, str(exc))) from exc

def load_env_config_files(config_files, variants):
    '''
    Load all of the environment config files, plus any that come from "imported_envs"
    within an environment config file.
    '''
    env_config_files = [os.path.abspath(e) for e in config_files]
    env_config_data_list = []
    loaded_files = []
    while env_config_files:
        # Load the environment config files using conda-build's API. This will allow for the
        # filtering of text using selectors and jinja2 functions
        env = _validate_config_file(env_config_files[0], variants)

        # Examine all of the imported_envs items and determine if they still need to be loaded.
        new_config_files = []
        imported_envs = env.get(Key.imported_envs.name, [])
        if not imported_envs:
            imported_envs = []
        for imported_env in imported_envs:
            imported_env = os.path.expanduser(imported_env)
            if not os.path.isabs(imported_env):
                imported_env = os.path.join(os.path.dirname(env_config_files[0]), imported_env)
            if not imported_env in env_config_files and not imported_env in loaded_files:
                new_config_files += [imported_env]

        # If there are new files to load, add them to the env_conf_files list.
        # Otherwise, remove the current file from the env_conf_files list and
        # add its data to the env_config_data_list.
        if new_config_files:
            env_config_files = new_config_files + env_config_files
        else:
            env_config_data_list += [env]
            loaded_files += [env_config_files[0]]
            env_config_files.pop(0)

    return env_config_data_list
