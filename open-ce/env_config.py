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
import conda_build.metadata

def _validate_config_file(env_file, variants):
    '''Perform some validation on the environment file after loading it.'''
    possible_keys = {'imported_envs', 'channels', 'packages', 'git_tag_for_env', 'git_tag'}
    try:
        meta_obj = conda_build.metadata.MetaData(env_file, variant=variants)
        if not ("packages" in meta_obj.meta.keys() or "imported_envs" in meta_obj.meta.keys()):
            raise Exception("Content Error!",
                            "An environment file needs to specify packages or "
                            "import another environment file.")
        for key in meta_obj.meta.keys():
            if not key in possible_keys:
                raise Exception("Key Error!", key + " is not a valid key in the environment file.")
        return meta_obj
    except (Exception, SystemExit) as exc: #pylint: disable=broad-except
        print('***** Error in %s:\n  %s' % (env_file, exc), file=sys.stderr)
        return None

def load_env_config_files(config_files, variants):
    '''
    Load all of the environment config files, plus any that come from "imported_envs"
    within an environment config file.
    '''
    env_config_files = [os.path.abspath(e) for e in config_files]
    env_config_data_list = []
    loaded_files = []
    retval = 0
    while env_config_files:
        # Load the environment config files using conda-build's API. This will allow for the
        # filtering of text using selectors and jinja2 functions
        meta_obj = _validate_config_file(env_config_files[0], variants)
        if meta_obj is None:
            retval = 1
            loaded_files += [env_config_files[0]]
            env_config_files.pop(0)
            continue
        env = meta_obj.get_rendered_recipe_text()

        # Examine all of the imported_envs items and determine if they still need to be loaded.
        new_config_files = []
        for imported_env in env.get('imported_envs', []):
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

    return retval, env_config_data_list
