#!/usr/bin/env python

import argparse
import os
import sys
import pathlib

test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'builder'))
import build_env

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

    retval,_ = build_env.load_env_config_files(args.env_files, variants)

    return retval

if __name__ == '__main__':
    sys.exit(main())