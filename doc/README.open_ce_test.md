# README for `open-ce test` command

* [`open-ce test env`](#open-ce-test-env-sub-command)
* [`open-ce test feedstock`](#open-ce-test-feedstock-sub-command)

## Open-CE Tests

Open-CE provides tools for running tests for packages built by the Open-CE tools. To add tests to a feedstock, create a file named `tests/open-ce-tests.yaml`. The test can include a list of tests that will be run within a newly generated conda environment that should include the packages being built by the feedstock.

### Open-CE Test File

An Open-CE Test file is a YAML file that describes the tests that will be run. The test files can also include jinja code. Below is a simple example of a test file:

```yaml
tests:
  - name: First Test
    command: |
      cd my_package
      pytest -v tests
{% if build_type == 'cuda' %}
  - name: CUDA Test
    command: |
      cd my_package
      pytest -v cuda_tests
{% endif %}
```

This example will:

1. Create a new conda environment that will be active throughout the running of the tests.
1. Run the bash instructions specified by `command` in "First Test" within a new bash shell that activates the conda environment from step 1.
1. If running within a CUDA environment, run the bash instructions specified by `command` in "CUDA Test" within a new bash shell that activates the conda environment from step 1.
1. Removes the conda environment created in step 1.

#### Open-CE Test File Environment Variables

The following environment variables can be referenced within the command section of an Open-CE test:

| Environment Variable | Description |
| -------------------- | ----------- |
| FEEDSTOCK_DIR        | Path of the feedstock directory containing the test |

### Test Labels

Labels can be added to tests using jinja. Labels can be activated using the `--test_labels` argument to the `open-ce test` tools. Below is an example of a test file that only runs the second test if the `long` label is activated.

```yaml
tests:
  - name: Short Test
    command: ./run_short_tests
{% if long %}
  - name: Long Test
    command: ./run_long_tests
{% endif %}
```

## Running Tests After a Build

Tests can be run immediately after a build has completed by passing the `--run_tests` argument to `open-ce build env`. Tests will be run for every package that was built (but not until every package has been built). Tests will be run for every combination of build variants that were specified by the build command. For example, if `python_versions` is set to `3.6,3.7`, tests will be run for the python 3.6 packages and python 3.7 packages. For more information on the `open-ce build env` command, see [doc/README.open_ce_build.md] (README.open_ce_build.md).

## `open-ce test env` sub command

The `open-ce test env` command can be used to run tests for every package listed within an Open-CE Environment [file](README.yaml.md). Tests will be run for every combination of build variants that are specified. For example, if `python_versions` is set to `3.6,3.7`, tests will be run for the python 3.6 packages and python 3.7 packages.

### Command usage for `open-ce test env`

```shell
==============================================================================
usage: open-ce test env [-h] [--conda_build_config CONDA_BUILD_CONFIG]
                        [--output_folder OUTPUT_FOLDER]
                        [--channels CHANNELS_LIST] [--packages PACKAGES]
                        [--repository_folder REPOSITORY_FOLDER]
                        [--python_versions PYTHON_VERSIONS]
                        [--build_types BUILD_TYPES] [--mpi_types MPI_TYPES]
                        [--cuda_versions CUDA_VERSIONS] [--container_build]
                        [--git_location GIT_LOCATION]
                        [--git_tag_for_env GIT_TAG_FOR_ENV]
                        [--test_labels TEST_LABELS]
                        env_config_file [env_config_file ...]

positional arguments:
  env_config_file       Path to the environment configuration YAML file. The configuration
                        file describes the package environment you wish to build.

                        A collection of files exist at https://github.com/open-ce/open-ce-environments.

                        This argument can be a URL, in which case imported_envs and the conda_build_config
                        will be automatically discovered in the same remote directory. E.g.:
                        >$ open-ce build env https://raw.githubusercontent.com/open-ce/open-ce-environments/main/envs/opence-env.yaml

                        For complete documentation on Open-CE environment files see:
                        https://github.com/open-ce/open-ce/blob/master/doc/README.yaml.md

optional arguments:
  -h, --help            show this help message and exit
  --conda_build_config CONDA_BUILD_CONFIG
                        Location of conda_build_config.yaml file. Can be a
                        valid URL. (default: None)
  --output_folder OUTPUT_FOLDER
                        Path where built conda packages will be saved.
                        (default: condabuild)
  --channels CHANNELS_LIST
                        Conda channels to be used. (default: [])
  --packages PACKAGES   Only build this list of comma delimited packages (plus
                        their dependencies). (default: None)
  --repository_folder REPOSITORY_FOLDER
                        Directory that contains the repositories. If the
                        repositories don't exist locally, they will be
                        downloaded from OpenCE's git repository. If no value
                        is provided, repositories will be downloaded to the
                        current working directory. (default: )
  --python_versions PYTHON_VERSIONS
                        Comma delimited list of python versions to build for ,
                        such as "3.6" or "3.7". (default: 3.7)
  --build_types BUILD_TYPES
                        Comma delimited list of build types, such as "cpu" or
                        "cuda". (default: cpu,cuda)
  --mpi_types MPI_TYPES
                        Comma delimited list of mpi types, such as "openmpi"
                        or "system". (default: openmpi)
  --cuda_versions CUDA_VERSIONS
                        CUDA version to build for , such as "10.2" or "11.0".
                        (default: 10.2)
  --container_build, --docker_build
                        Perform a build within a container. NOTE: When
                        the --container_build flag is used, all arguments with
                        paths should be relative to the directory containing
                        root level open-ce directory. Only files within the
                        root level open-ce directory and local_files will be
                        visible at build time. (default: False)
  --git_location GIT_LOCATION
                        The default location to clone git repositories from.
                        (default: https://github.com/open-ce)
  --git_tag_for_env GIT_TAG_FOR_ENV
                        Git tag to be checked out for all of the packages in
                        an environment. (default: None)
  --test_labels TEST_LABELS
                        Comma delimited list of labels indicating what tests
                        to run. (default: )
==============================================================================
```

## `open-ce test feedstock` sub command

The `open-ce test feedstock` command can be used to run tests for a specific feedstock. The `open-ce test feedstock` command should be run from within the feedstock directory that will be tested. A conda environment file must be passed in as an argument. A conda environment will be created before the tests are run based on the passed in conda environment file.

```shell
==============================================================================
usage: open-ce test feedstock [-h] [--conda_env_file CONDA_ENV_FILE]
                              [--test_working_dir TEST_WORKING_DIR]
                              [--test_labels TEST_LABELS]

optional arguments:
  -h, --help            show this help message and exit
  --conda_env_file CONDA_ENV_FILE
                        Location of conda environment file. (default: None)
  --test_working_dir TEST_WORKING_DIR
                        Directory where tests will be executed. (default: ./)
  --test_labels TEST_LABELS
                        Comma delimited list of labels indicating what tests
                        to run. (default: )
==============================================================================
```
