# *****************************************************************
#
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2020. All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# *****************************************************************

import sys
import os
import pathlib
import imp

test_dir = pathlib.Path(__file__).parent.absolute()
sys.path.append(os.path.join(test_dir, '..', 'open-ce'))

open_ce = imp.load_source('open_ce', os.path.join(test_dir, '..', 'open-ce', 'open-ce'))
import test_env

def test_test_env(mocker):
    '''
    This is a test for test_env. Since test_env is a wrapper for build_env, we are mainly relying
    on the tests for build_env.
    '''
    def validate_build_env(args):
        assert args.skip_build_packages == True
        assert args.run_tests == True

    mocker.patch('build_env.build_env', side_effect=validate_build_env)

    open_ce._main(["test", test_env.COMMAND, "some_env_file.yaml"])
