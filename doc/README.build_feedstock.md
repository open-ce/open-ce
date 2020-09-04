
# README for build_feedstock.py

The `build_feedstock.py` script can be used to build an image of a specific
individual feedstock repository from the Open-CE project.  In most cases, you
will want to build a package and all of its dependencies, which can be more
easily accomplished by using the `build_env.py` command (Refer to the README
for that command).
However, in some cases you may want to just build a selected individual package
from its own feedstock repo.  In that case, you can run `build_feedstock.py`
directly.

Note that you will need to have a local clone of the feedstock repository that
you wish to build, as well as the Open-CE `open-ce` repository (in which this
script is found).  By contrast, if you were to use `build_env.py`, the script
will clone any necessary dependency repositories for you.

Command usage for the `build_feedstock.py` command:

```shell
==============================================================================
usage: build_feedstock.py [-h] [--recipe-config-file RECIPE_CONFIG_FILE]
                        [--output_folder OUTPUT_FOLDER]
                        [--recipes RECIPE_LIST]
                        [--conda_build_config CONDA_BUILD_CONFIG]
                        [--python_versions PYTHON_VERSIONS_LIST]
                        [--build_types BUILD_TYPES_LIST]
                        [--working_directory WORKING_DIRECTORY]
                        [--channels CHANNELS_LIST]

Build conda packages as part of Open-CE

optional arguments:
  -h, --help            show this help message and exit
  --recipe-config-file RECIPE_CONFIG_FILE
                        Path to the recipe configuration YAML file. The configuration
                        file lists paths to recipes to be built within a feedstock.

                        Below is an example stating that there are two recipes to build,
                        one named my_project and one named my_variant.

                        recipes:
                          - name : my_project
                            path : recipe

                          - name : my_variant
                            path: variants

                        If no path is given, the default value is `build-config.yaml`.
                        If `build-config.yaml` does not exist, and no value is provided,
                        it will be assumed there is a single recipe with the
                        path of "recipe".
  --output_folder OUTPUT_FOLDER
                        Path where built conda packages will be saved.
  --recipes RECIPE_LIST
                        Comma separated list of recipe names to build.
  --conda_build_config CONDA_BUILD_CONFIG
                        Location of `conda_build_config.yaml` file.
  --python_versions PYTHON_VERSIONS_LIST
                        Comma delimited list of python versions to build for, such as "3.6" or "3.7".
  --build_types BUILD_TYPES_LIST
                        Comma delimited list of build types, such as "cpu" or "gpu".
  --working_directory WORKING_DIRECTORY
                        Directory to run the script in.
  --channels CHANNELS_LIST
                        Conda channel to be used.
==============================================================================
```
