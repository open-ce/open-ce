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
sys.path.append(os.path.join(pathlib.Path(__file__).parent.absolute(), '..', 'open-ce'))

import helpers
import build_feedstock

def test_build_feedstock_default(mocker):
    """
    Tests that the default arguments for 'build_feedstock' generate the correct 'conda-build' command.
    """
    mocker.patch(
        'os.getcwd',
        return_value="/test/test_recipe"
    )
    mocker.patch(
        'os.path.exists',
        return_value=False
    )
    mocker.patch(
        'os.system',
        side_effect=(lambda x: helpers.validate_cli(x, expect=["conda-build",
                                                               "--output-folder condabuild",
                                                               "conda_build_config.yaml",
                                                               "recipe"]))
    )

    arg_input = []
    assert build_feedstock.build_feedstock(arg_input) == 0

def test_build_feedstock_failure(mocker, capsys):
    """
    Tests that a 'conda-build' failure is handled correctly.
    """
    mocker.patch(
        'os.getcwd',
        return_value="/test/test_recipe"
    )
    mocker.patch(
        'os.path.exists',
        return_value=False
    )
    mocker.patch(
        'os.system',
        side_effect=(lambda x: helpers.validate_cli(x, expect=["conda-build"], retval=1)) # Retval is 1 to simulate a failure.
    )

    arg_input = ""
    assert build_feedstock.build_feedstock(arg_input) == 1
    captured = capsys.readouterr()
    assert "Failure building recipe: test_recipe" in captured.out

def test_build_feedstock_working_dir(mocker):
    """
    Tests that the 'working_dir' argument is correctly handled and the original working directory is restored after execution.
    """
    dirTracker = helpers.DirTracker("/test/starting_dir")
    mocker.patch(
        'os.getcwd',
        side_effect=dirTracker.mocked_getcwd
    )
    mocker.patch(
        'os.path.exists',
        return_value=False
    )
    mocker.patch(
        'os.system',
        side_effect=(lambda x: helpers.validate_cli(x, expect=["conda-build"]))
    )
    mocker.patch(
        'os.chdir',
        side_effect=(lambda x: dirTracker.validate_chdir(x, expected_dirs=["/test/my_work_dir", # First the working directory should be changed to the arg.
                                                                           "/test/starting_dir"])) # And then changed back to the starting directory.
    )

    arg_input = ["--working_directory", "/test/my_work_dir"]
    assert build_feedstock.build_feedstock(arg_input) == 0

def test_build_feedstock_config_file(mocker):
    """
    Tests that the 'recipe_config_file' argument is correctly handled..
    """
    mocker.patch(
        'os.getcwd',
        return_value="/test/test_recipe"
    )
    mocker.patch(
        'os.path.exists',
        return_value=True # 'path.exists' is mocked as true so that the input file is found to exist.
    )
    mocker.patch(
        'os.system',
        side_effect=(lambda x: helpers.validate_cli(x, expect=["conda-build",
                                                               "variants_from_config"])) #Checks that the value from the input config file is used.
    )

    #This is the data that is read in when 'open()' is called.
    test_recipe_config =b"""recipes:
    - name : my_variant
      path: variants_from_config"""

    mocker.patch(
        'builtins.open',
        mocker.mock_open(read_data=test_recipe_config)
    )

    arg_input = ["--recipe-config-file", "my_config.yml"]
    assert build_feedstock.build_feedstock(arg_input) == 0

def test_build_feedstock_default_config_file(mocker):
    """
    Tests that the default config file is loaded when no argument is specified.
    """
    mocker.patch(
        'os.getcwd',
        return_value="/test/test_recipe"
    )
    mocker.patch(
        'os.path.exists',
        return_value=True #True for default config file.
    )
    mocker.patch(
        'os.system',
        side_effect=(lambda x: helpers.validate_cli(x, expect=["conda-build",
                                                               "variants_from_default_config"]))#Checks that the value from the default config file is used.
    )

    test_recipe_config =b"""recipes:
    - name : my_variant
      path: variants_from_default_config"""

    mocker.patch(
        'builtins.open',
        mocker.mock_open(read_data=test_recipe_config)
    )

    arg_input = []
    assert build_feedstock.build_feedstock(arg_input) == 0

def test_build_feedstock_nonexist_config_file(mocker, capsys):
    """
    Tests that execution fails and the correct error message is shown if the default config file doesn't exist.
    """
    mocker.patch(
        'os.getcwd',
        return_value="/test/test_recipe"
    )
    mocker.patch(
        'os.path.exists',
        return_value=False
    )

    arg_input = ["--recipe-config-file", "my_config.yml"]
    assert build_feedstock.build_feedstock(arg_input) == 1
    captured = capsys.readouterr()
    assert "Unable to open provided config file: my_config.yml" in captured.out

def test_build_feedstock_local_src_dir_args(mocker):
    """
    Tests that providing the local_src_dir argument sets the LOCAL_SRC_DIR environment variable correctly.
    """
    mocker.patch(
        'os.path.exists',
        return_value=True
    )

    assert build_feedstock._set_local_src_dir("my_src_dir", None, None) == 0
    assert os.environ["LOCAL_SRC_DIR"] == "my_src_dir"

def test_build_feedstock_local_src_dir_args_fail(mocker, capsys):
    """
    Tests that providing the local_src_dir argument to a non-existant file fails properly.
    """
    mocker.patch(
        'os.path.exists',
        return_value=False
    )

    assert build_feedstock._set_local_src_dir("my_src_dir", { 'local_src_dir' : "my_other_src_dir" }, None) == 1
    captured = capsys.readouterr()
    assert "ERROR: local_src_dir path \"my_src_dir\" specified doesn't exist" in captured.out

def test_build_feedstock_local_src_dir_recipe(mocker):
    """
    Tests that providing the local_src_dir in a recipe sets the LOCAL_SRC_DIR environment variable correctly.
    """
    mocker.patch(
        'os.path.exists',
        return_value=True
    )

    assert build_feedstock._set_local_src_dir(None, { 'local_src_dir' : "my_other_src_dir" } , "/test/location/recipe.yaml") == 0
    assert os.environ["LOCAL_SRC_DIR"] == "/test/location/my_other_src_dir"

def test_build_feedstock_extra_args(mocker):
    """
    Tests that additional arguments add the expected values to the conda-build command.
    """
    mocker.patch(
        'os.getcwd',
        return_value="/test/test_recipe"
    )
    mocker.patch(
        'os.path.exists',
        return_value=True
    )
    mocker.patch(
        'os.system',
        side_effect=(lambda x: helpers.validate_cli(x, expect=["conda-build",
                                                               "-c test_channel",
                                                               "-c test_channel_2",
                                                               "-c test_channel_from_config",
                                                               "--variants \"{'python': ['3.6', '3.7'], 'build_type': ['cpu', 'gpu']}\""],
                                                       reject=["test_recipe_extra"]))
    )

    test_recipe_config =b"""recipes:
    - name : my_project
      path : recipe

    - name : my_variant
      path: variants

    - name : test_recipe_extra
      path: extra
channels:
    - test_channel_from_config"""

    mocker.patch(
        'builtins.open',
        mocker.mock_open(read_data=test_recipe_config)
    )

    arg_input = ["--channels", "test_channel",
                 "--channels", "test_channel_2",
                 "--recipes", "my_project,my_variant",
                 "--python_versions", "3.6,3.7",
                 "--build_types", "cpu,gpu"]
    assert build_feedstock.build_feedstock(arg_input) == 0
