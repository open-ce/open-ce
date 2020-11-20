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

utils.check_if_conda_build_exists()

# pylint: disable=wrong-import-position
import conda_build.api
from conda_build.config import get_or_merge_config
import conda_build.metadata
# pylint: enable=wrong-import-position

def render_yaml(path, variants=None, variant_config_files=None, schema=None, permit_undefined_jinja=False):
    """
    Call conda-build's render tool to get a list of dictionaries of the
    rendered YAML file for each variant that will be built.
    """
    config = get_or_merge_config(None)
    config.variant_config_files = variant_config_files
    config.verbose = False

    if not os.path.isfile(path):
        metas = conda_build.api.render(path,
                                       config=config,
                                       variants=variants,
                                       bypass_env_check=True,
                                       finalize=False)
    else:
        # api.render will only work if path is pointing to a meta.yaml file.
        # For other files, use the MetaData class directly.
        # The absolute path is needed because MetaData seems to do some caching based on file name.
        metas = conda_build.metadata.MetaData(os.path.abspath(path),
                                              variant=variants,
                                              config=config).get_rendered_recipe_text(permit_undefined_jinja=permit_undefined_jinja)
    if schema:
        utils.validate_dict_schema(metas, schema)
    return metas
