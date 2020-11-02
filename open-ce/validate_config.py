#!/usr/bin/env python

"""
*****************************************************************
Licensed Materials - Property of IBM
(C) Copyright IBM Corp. 2020. All Rights Reserved.
US Government Users Restricted Rights - Use, duplication or
disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
*****************************************************************
"""

import sys
import utils
from errors import OpenCEError, Error

utils.check_if_conda_build_exists()

import build_tree # pylint: disable=wrong-import-position

def make_parser():
    ''' Parser input arguments '''
    arguments = [utils.Argument.CONDA_BUILD_CONFIG, utils.Argument.ENV_FILE,
                 utils.Argument.REPOSITORY_FOLDER, utils.Argument.PYTHON_VERSIONS,
                 utils.Argument.BUILD_TYPES, utils.Argument.MPI_TYPES]
    parser = utils.make_parser(arguments,
                               description = 'Perform validation on a conda_build_config.yaml file.')
    return parser

def validate_config(arg_strings=None):
    '''
    Entry function.
    '''
    args = make_parser().parse_args(arg_strings)
    variants = utils.make_variants(args.python_versions, args.build_types, args.mpi_types)
    for variant in variants:
        print('Validating {} for {}'.format(args.conda_build_config, variant))
        for env_file in args.env_config_file:
            print('Validating {} for {} : {}'.format(args.conda_build_config, env_file, variant))
            try:
                recipes = build_tree.BuildTree([env_file],
                                               variant['python'],
                                               variant['build_type'],
                                               variant['mpi_type'],
                                               variant['cuda_versions'],
                                               repository_folder=args.repository_folder,
                                               conda_build_config=args.conda_build_config)
            except OpenCEError as err:
                raise OpenCEError(Error.VALIDATE_CONFIG, args.conda_build_config, env_file, variant, err.msg) from err

            packages = [package for recipe in recipes for package in recipe.packages]
            channels = {channel for recipe in recipes for channel in recipe.channels}
            deps = {dep for recipe in recipes for dep in recipe.run_dependencies}
            deps.update(recipes.get_external_dependencies(variant))

            pkg_args = " ".join(["\"{}\"".format(utils.generalize_version(dep)) for dep in deps
                                                                          if not utils.remove_version(dep) in packages])

            channel_args = " ".join({"-c \"{}\"".format(channel) for channel in channels})

            cli = "conda create --dry-run -n test_conda_dependencies {} {}".format(channel_args, pkg_args)

            retval = utils.run_and_log(cli)

            if retval != 0:
                raise OpenCEError(Error.VALIDATE_CONFIG, args.conda_build_config, env_file, variant, "")

            print('Successfully validated {} for {} : {}'.format(args.conda_build_config, env_file, variant))

        print('Successfully validated {} for {}'.format(args.conda_build_config, variant))

    print("{} Successfully validated!".format(args.conda_build_config))

if __name__ == '__main__':
    try:
        validate_config()
    except OpenCEError as err:
        print(err.msg, file=sys.stderr)
        sys.exit(1)

    sys.exit(0)
