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
import utils
import build_feedstock

def test_build_feedstock_default(mocker):
    """
    Tests that the default arguments for 'build_feedstock' generate the correct 'conda_build.api.build' input args.
    """
    mocker.patch(
        'os.getcwd',
        return_value="/test/test_recipe"
    )
    mocker.patch(
        'os.path.exists',
        return_value=False
    )
    expect_recipe = os.path.join(os.getcwd(),'recipe')
    expect_config = {'variant_config_files' : [utils.DEFAULT_CONDA_BUILD_CONFIG],
                'output_folder' : utils.DEFAULT_OUTPUT_FOLDER}
    mocker.patch(
        'conda_build.api.build',
        side_effect=(lambda x, **kwargs: helpers.validate_conda_build_args(x, expect_recipe=expect_recipe, expect_config=expect_config, **kwargs))
    )

    arg_input = []
    assert build_feedstock.build_feedstock(arg_input) == 0

def test_build_feedstock_failure(mocker, capsys):
    """
    Tests that a 'conda_build.api.build' failure is handled correctly.
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
        'conda_build.api.build',
        side_effect=ValueError("invalid literal for int() with base 10: 'xy'") #using ValueError to simulate a failure.
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
        'conda_build.api.build',
        return_value=[]
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
    expect_recipe = os.path.join(os.getcwd(),'variants_from_config') #Checks that the value from the input config file is used.
    mocker.patch(
        'conda_build.api.build',
        side_effect=(lambda x, **kwargs: helpers.validate_conda_build_args(x, expect_recipe=expect_recipe, **kwargs))
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
    expect_recipe = os.path.join(os.getcwd(),'variants_from_default_config')#Checks that the value from the default config file is used.
    mocker.patch(
        'conda_build.api.build',
        side_effect=(lambda x, **kwargs: helpers.validate_conda_build_args(x, expect_recipe=expect_recipe, **kwargs))
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
    Tests that additional arguments add the expected values to the 'conda_build.api.build' arguments.
    """
    mocker.patch(
        'os.getcwd',
        return_value="/test/test_recipe"
    )
    mocker.patch(
        'os.path.exists',
        return_value=True
    )
    expect_config = { 'channel_urls' : ['test_channel', 'test_channel_2', 'test_channel_from_config']}
    expect_variants = {'python': ['3.6'], 'build_type': ['cpu'], 'mpi_type': ['openmpi']}
    reject_recipe = os.path.join(os.getcwd,'test_recipe_extra')
    mocker.patch(
        'conda_build.api.build',
        side_effect=(lambda x, **kwargs: helpers.validate_conda_build_args(x, expect_config=expect_config, expect_variants=expect_variants, reject_recipe=reject_recipe, **kwargs))
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
                 "--python_versions", "3.6",
                 "--build_types", "cpu",
                 "--mpi_type", "openmpi"]
    assert build_feedstock.build_feedstock(arg_input) == 0
