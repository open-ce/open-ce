#!/usr/bin/env python

import argparse
import os
import sys
import conda_build.metadata

variants = { 'python' : ['3.6','3.7'], 'build_type' : ['cpu', 'cuda'] }

def make_parser():
    ''' Parser input arguments '''
    parser = argparse.ArgumentParser(
        description = 'Lint Environment Files',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        'env_files',
        nargs='+',
        type=str,
        help="""Files to Lint.""")

    return parser

def main(arg_strings=None):
    parser = make_parser()
    args = parser.parse_args(arg_strings)

    retval = 0
    for env_file in args.env_files:
        try:
            meta_obj = conda_build.metadata.MetaData(env_file, variant=variants)
            if not ("packages" in meta_obj.meta.keys() or "imported_envs" in meta_obj.meta.keys()):
                raise Exception("Content Error!", "An environment file needs to specify packages or import another environment file.")
        except (Exception, SystemExit) as e:
            retval = 1
            print('***** Error in %s:\n  %s' % (env_file, e), file=sys.stderr)

    return retval

if __name__ == '__main__':
    sys.exit(main())