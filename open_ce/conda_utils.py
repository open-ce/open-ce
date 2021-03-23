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
import pathlib
import subprocess
import yaml

# Disabling pylint warning "cyclic-import" locally here doesn't work. So, added it in .pylintrc
# according to https://github.com/PyCQA/pylint/issues/59
from open_ce.utils import validate_dict_schema, check_if_conda_build_exists, run_command_capture, generalize_version # pylint: disable=cyclic-import
from open_ce.errors import OpenCEError, Error

check_if_conda_build_exists()

# pylint: disable=wrong-import-position,wrong-import-order
import conda_build.api
from conda_build.config import get_or_merge_config
import conda_build.metadata
# pylint: enable=wrong-import-position,wrong-import-order

def render_yaml(path, variants=None, variant_config_files=None, schema=None, permit_undefined_jinja=False):
    """
    Call conda-build's render tool to get a list of dictionaries of the
    rendered YAML file for each variant that will be built.
    """
    config = get_or_merge_config(None, variant=variants)
    config.variant_config_files = variant_config_files
    config.verbose = False

    if not os.path.isfile(path):
        metas = conda_build.api.render(path,
                                       config=config,
                                       bypass_env_check=True,
                                       finalize=False)
    else:
        # api.render will only work if path is pointing to a meta.yaml file.
        # For other files, use the MetaData class directly.
        # The absolute path is needed because MetaData seems to do some caching based on file name.
        metas = conda_build.metadata.MetaData(
                            os.path.abspath(path),
                            config=config).get_rendered_recipe_text(permit_undefined_jinja=permit_undefined_jinja)
    if schema:
        validate_dict_schema(metas, schema)
    return metas

def get_output_file_paths(meta, variants):
    """
    Get the paths of all of the generated packages for a recipe.
    """
    config = get_or_merge_config(None, variant=variants)
    config.verbose = False

    out_files = conda_build.api.get_output_file_paths(meta, config=config)

    # Only return the package name and the parent directory. This will show where within the output
    # directory the package should be.
    result = []
    for out_file in out_files:
        path = pathlib.PurePath(out_file)
        result.append(os.path.join(path.parent.name, path.name))

    return result

def conda_package_info(channels, package):
    '''
    Get conda package info.
    '''
    pkg_args = "\"{}\"".format(generalize_version(package))
    channel_args = " ".join({"-c \"{}\"".format(channel) for channel in channels})

    cli = "conda search --json {} {} --info".format(channel_args, pkg_args)
    ret_code, std_out, _ = run_command_capture(cli, stderr=subprocess.STDOUT)
    if not ret_code:
        raise OpenCEError(Error.CONDA_DRY_RUN, cli, std_out)
    return std_out

def get_latest_package_info(channels, package):
    '''
    Get the conda package info for the most recent search result.
    '''
    results = yaml.safe_load(conda_package_info(channels, package))
    retval = results[list(results.keys())[0]][0]
    for result in results[list(results.keys())[0]]:
        if result["timestamp"] > retval["timestamp"]:
            retval = result
    return retval

def conda_dry_run(channels, packages):
    '''
    Perform a conda dry-run
    '''
    pkg_args = " ".join(["\"{}\"".format(generalize_version(dep)) for dep in packages])
    channel_args = " ".join({"-c \"{}\"".format(channel) for channel in channels})

    cli = "conda create --dry-run --json -n test_conda_dependencies {} {}".format(channel_args, pkg_args)
    ret_code, std_out, _ = run_command_capture(cli, stderr=subprocess.STDOUT)
    if not ret_code:
        raise OpenCEError(Error.CONDA_DRY_RUN, cli, std_out)
    return std_out
