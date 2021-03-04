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

import os
import pathlib
import pytest
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

test_dir = pathlib.Path(__file__).parent.absolute()

spec = spec_from_loader("opence", SourceFileLoader("opence", os.path.join(test_dir, '..', 'open_ce', 'open-ce')))
opence = module_from_spec(spec)
spec.loader.exec_module(opence)

import helpers
import open_ce.utils as utils
from open_ce.errors import OpenCEError
import open_ce.build_feedstock as build_feedstock

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

    opence._main(["build", build_feedstock.COMMAND])

def test_build_feedstock_failure(mocker):
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

    with pytest.raises(OpenCEError) as exc:
        opence._main(["build", build_feedstock.COMMAND])
    assert "Unable to build recipe: test_recipe" in str(exc.value)

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
    working_dir = "/test/my_work_dir"
    mocker.patch(
        'os.chdir',
        side_effect=(lambda x: dirTracker.validate_chdir(x, expected_dirs=[working_dir, # First the working directory should be changed to the arg.
                                                                           "/test/starting_dir"])) # And then changed back to the starting directory.
    )

    opence._main(["build", build_feedstock.COMMAND, "--working_directory", working_dir])

def test_build_feedstock_config_file(mocker):
    """
    Tests that the 'recipe_config_file' argument is correctly handled..
    """
    expect_recipe = os.path.join(os.getcwd(),'cuda_recipe_path') #Checks that the value from the input config file is used.
    mocker.patch(
        'conda_build.api.build',
        side_effect=(lambda x, **kwargs: helpers.validate_conda_build_args(x, expect_recipe=expect_recipe, **kwargs))
    )

    opence._main(["build", build_feedstock.COMMAND, "--recipe-config-file", os.path.join(test_dir, "my_config.yaml"), "--build_type", "cuda"])

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

    test_recipe_config = {'recipes' : [{'name' : 'my_variant', 'path' : 'variants_from_default_config'}]}

    mocker.patch('open_ce.conda_utils.render_yaml', return_value=test_recipe_config)

    opence._main(["build", build_feedstock.COMMAND])

def test_build_feedstock_nonexist_config_file(mocker):
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

    with pytest.raises(OpenCEError) as exc:
        opence._main(["build", build_feedstock.COMMAND, "--recipe-config-file", "my_config.yml"])
    assert "Unable to open provided config file: my_config.yml" in str(exc.value)

def test_recipe_config_file_for_inapplicable_configuration(mocker, capsys):
    """
    Tests the case when build is triggered for a configuration for which no recipes are applicable.
    """

    expect_recipe = os.path.join(os.getcwd(),'cuda_recipe_path') #Checks that the value from the input config file is used.
    mocker.patch(
        'conda_build.api.build',
        side_effect=(lambda x, **kwargs: helpers.validate_conda_build_args(x, expect_recipe=expect_recipe, **kwargs))
    )
    
    opence._main(["build", build_feedstock.COMMAND, "--recipe-config-file", os.path.join(test_dir, "my_config.yaml"), "--python_versions", "4.1"])
    captured = capsys.readouterr()
    assert "INFO: No recipe to build for given configuration." in captured.out

def test_build_feedstock_local_src_dir_args(mocker):
    """
    Tests that providing the local_src_dir argument sets the LOCAL_SRC_DIR environment variable correctly.
    """
    mocker.patch(
        'os.path.exists',
        return_value=True
    )

    build_feedstock._set_local_src_dir("my_src_dir", None, None)
    assert os.environ["LOCAL_SRC_DIR"] == "my_src_dir"

def test_build_feedstock_local_src_dir_args_fail(mocker):
    """
    Tests that providing the local_src_dir argument to a non-existant file fails properly.
    """
    mocker.patch(
        'os.path.exists',
        return_value=False
    )

    with pytest.raises(OpenCEError) as exc:
        build_feedstock._set_local_src_dir("my_src_dir", { 'local_src_dir' : "my_other_src_dir" }, None)
    assert "local_src_dir path \"my_src_dir\" specified doesn't exist" in str(exc.value)

def test_build_feedstock_local_src_dir_recipe(mocker):
    """
    Tests that providing the local_src_dir in a recipe sets the LOCAL_SRC_DIR environment variable correctly.
    """
    mocker.patch(
        'os.path.exists',
        return_value=True
    )

    build_feedstock._set_local_src_dir(None, { 'local_src_dir' : "my_other_src_dir" } , "/test/location/recipe.yaml")
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

    expect_config = { 'channel_urls' : ['/test/test_recipe/condabuild', 'test_channel', 'test_channel_2', 'test_channel_from_config']}
    expect_variants = {'python': '3.6', 'build_type': 'cpu', 'mpi_type': 'openmpi'}
    reject_recipe = os.path.join(os.getcwd(),'test_recipe_extra')
    mocker.patch(
        'conda_build.api.build',
        side_effect=(lambda x, **kwargs: helpers.validate_conda_build_args(x, expect_config=expect_config, expect_variants=expect_variants, reject_recipe=reject_recipe, **kwargs))
    )

    test_recipe_config = { 'recipes' : [{ 'name' : 'my_project', 'path' : 'recipe'},
                                        { 'name' : 'my_variant', 'path': 'variants'},
                                        { 'name' : 'test_recipe_extra', 'path' : 'extra'}],
                           'channels' : ['test_channel_from_config']}

    mocker.patch('open_ce.conda_utils.render_yaml', return_value=test_recipe_config)

    arg_input = ["build", build_feedstock.COMMAND,
                 "--channels", "test_channel",
                 "--channels", "test_channel_2",
                 "--recipes", "my_project,my_variant",
                 "--python_versions", "3.6",
                 "--build_types", "cpu",
                 "--mpi_types", "openmpi",
                 "--cuda_versions", "10.2"]
    opence._main(arg_input)

def test_build_feedstock_if_no_conda_build(mocker):
    '''
    Test that build_feedstock should fail if conda_build isn't present
    '''
    mocker.patch('pkg_resources.get_distribution', return_value=None)

    with pytest.raises(OpenCEError):
        assert opence._main(["build", build_feedstock.COMMAND]) == 1

