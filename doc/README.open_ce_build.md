# README for `open-ce build` command

* [`open-ce build env`](#open-ce-build-env-sub-command)
* [`open-ce build feedstock`](#open-ce-build-feedstock-sub-command)
* [`open-ce build image`](#open-ce-build-image-sub-command)

## Installing these tools

Installation information can be found in the main [README](https://github.com/open-ce/open-ce#installing-the-open-ce-build-tools). The examples in this document assume installation via pip.

## `open-ce build env` sub command

For a general build to generate desired images for a specific package,
a build is achieved by executing the script `open-ce build env`. This will extract
and build all of the individual required components within the various Open-CE
feedstock repository trees required for the requested package environment.
In other words, if you simply want to build a package such as tensorflow or
pytorch (or any other; see the `open-ce-environments/envs` subdirectory), with dependencies
automatically handled, you can do so using a single `open-ce build env` command.

For example:
In the simplest case, a build for tensorflow may look like this:

```shell
    open-ce build env open-ce-environments/envs/tensorflow-env.yaml
```

while a similar build for pytorch may look like this:

```shell
    open-ce build env open-ce-environments/envs/pytorch-env.yaml
```

Other environment files for other packages can also be found in the `envs`
directory; simply specify the file for whichever package environment you want.

> Note: that the `open-ce build env` command executes the `open-ce build feedstock` command
> as needed, behind the scenes.  This script builds each individual feedstock
> component dependency using the build recipe within its own repository.
> You do not need to execute `open-ce build feedstock` directly yourself, although
> you may do so if you wish to perform an individual build of your own
> for any given Open-CE feedstock repository.

### Container build

The `--container_build` option will build an image and run the build command
inside of a container based on the new image. The `--container_tool` option can
be passed to specify container tool to be used. 

Along with `--container_build` option, `--container_build_args` can be passed
to set container build options like environment variables or other settings
like cpusets.

```shell
    open-ce build env --container_build --container_tool podman --container_build_args="--build-arg ENV1=test1 --cpuset-cpus 0,1" open-ce-environments/envs/pytorch-env.yaml
```

As part of this process of container build, it will copy a local_files directory that is in the
current working directory into the container, if the directory exists.

The paths to the `env_config_file`s and `--conda_build_config` must point to
files within the `open-ce-environments` directory and be relative to the directory
containing the root level `open-ce` directory.

### Use System MPI

By default, building the entire
[Open-CE environment file](https://github.com/open-ce/open-ce-environments/blob/main/envs/opence-env.yaml)
will include a build of [OpenMPI](https://github.com/open-ce/openmpi-feedstock)
which will be used for packages that need MPI, like
[Horovod](https://github.com/open-ce/horovod-feedstock). To use a system install of
MPI instead, `--mpi_types system` can be passed as an argument to `open-ce build env`. Build success
will require that the MPI environment is correctly set up.

### Command usage for `open-ce build env`

```shell
==============================================================================
usage: open-ce build env [-h] [--conda_build_config CONDA_BUILD_CONFIG]
                         [--output_folder OUTPUT_FOLDER]
                         [--channels CHANNELS_LIST] [--packages PACKAGES]
                         [--repository_folder REPOSITORY_FOLDER]
                         [--python_versions PYTHON_VERSIONS]
                         [--build_types BUILD_TYPES] [--mpi_types MPI_TYPES]
                         [--cuda_versions CUDA_VERSIONS]
                         [--skip_build_packages] [--run_tests]
                         [--container_build] [--git_location GIT_LOCATION]
                         [--git_tag_for_env GIT_TAG_FOR_ENV]
                         [--test_labels TEST_LABELS]
                         [--container_build_args CONTAINER_BUILD_ARGS]
                         [--container_tool CONTAINER_TOOL]
                         env_config_file [env_config_file ...]

positional arguments:
  env_config_file       Path to the environment configuration YAML file. The configuration
                        file describes the package environment you wish to build.
 
                        A collection of files exist at https://github.com/open-ce/open-ce-environments.

                        This argument can be a URL, in which case imported_envs and the conda_build_config
                        will be automatically discovered in the same remote directory. E.g.:
                        >$ open-ce build env https://raw.githubusercontent.com/open-ce/open-ce-environments/main/envs/opence-env.yaml

                        If the provided file doesn't exist locally, a URL will be generated to pull down from
                        https://raw.githubusercontent.com/open-ce/open-ce-environments/main/envs. If the --git_tag_for_env argument
                        is provided, it will pull down from the provided tag instead of main. E.g:
                        >$ open-ce build env opence-env

                        For complete documentation on Open-CE environment files see:
                        https://github.com/open-ce/open-ce/blob/main/doc/README.yaml.md

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
  --skip_build_packages
                        Do not perform builds of packages. (default: False)
  --run_tests           Run Open-CE tests for each potential conda environment
                        (default: False)
  --container_build, --docker_build
                        Perform a build within a container. NOTE: When the
                        --container_build flag is used, all arguments with
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
  --container_build_args CONTAINER_BUILD_ARGS
                        Container build arguments like environment variables
                        to be set in the container or cpus or gpus to be used
                        such as "--build-arg ENV1=test1 --cpuset-cpus 0,1".
                        (default: )
  --container_tool CONTAINER_TOOL
                        Container tool to be used. Default is taken from the
                        system, podman has preference over docker. (default: )
==============================================================================
```

### Conda environment files

`open-ce build env` also generates conda environment files based on the configuration
 selected for a build. For e.g. if `open-ce build env` is run for `tensorflow-env.yaml` and
 for python_versions `3.7`, build_type `cuda` and mpi_type being `openmpi`, then a
 conda environment file with name `open-ce-conda-env-py3.7-cuda-openmpi.yaml` gets
 generated. This environment file can be used to create a conda environment with
 the packages listed in `tensorflow-env.yaml` installed in it.

```shell
    open-ce build env --python_versions=3.7 --build_type=cuda --mpi_type=openmpi
    open-ce-environments/envs/tensorflow-env.yaml
```

 The above command will output `open-ce-conda-env-py3.7-cuda-openmpi.yaml` in the specified
 output folder (or by default `./condabuild` directory).

 The following command can be used to create a conda environment using the generated conda
 environment file -

```shell
    conda env create -f open-ce-conda-env-py3.7-cuda-openmpi.yaml
```

There could be one or more conda environment files generated for each variant based on inputs
given to `open-ce build env`. For example, if `open-ce build env` is run without any `build_type` and python_versions
`3.7` and mpi_type as `openmpi`, then two files will be generated namely -
`open-ce-conda-env-py3.7-cuda-openmpi.yaml`, `open-ce-conda-env-py3.7-cpu-openmpi.yaml`.

`open-ce build env` can generate these target conda environment files for a given Open-CE environment file
and provided build configuration even without performing an actual build.

## `open-ce build feedstock` sub command

The `open-ce build feedstock` script can be used to build an image of a specific
individual feedstock repository from the Open-CE project.  In most cases, you
will want to build a package and all of its dependencies, which can be more
easily accomplished by using the `open-ce build env` command (Refer to the README
for that command).
However, in some cases you may want to just build a selected individual package
from its own feedstock repo.  In that case, you can run `open-ce build feedstock`
directly.

Note that a local clone of the desired feedstock repository will need to be present
in addition to the Open-CE `open-ce` repository (in which this script is found).  
By contrast, if you were to use `open-ce build env`, the script will clone any necessary 
dependency repositories for you.

In addition, note that the `open-ce build feedstock` command should be run from
within the base directory checked out code of the feedstock.

Command usage for the `open-ce build feedstock` command:

```shell
==============================================================================
usage: open-ce build feedstock [-h] [--conda_build_config CONDA_BUILD_CONFIG]
                               [--output_folder OUTPUT_FOLDER]
                               [--channels CHANNELS_LIST]
                               [--python_versions PYTHON_VERSIONS]
                               [--build_types BUILD_TYPES]
                               [--mpi_types MPI_TYPES]
                               [--cuda_versions CUDA_VERSIONS]
                               [--recipe-config-file RECIPE_CONFIG_FILE]
                               [--recipes RECIPE_LIST]
                               [--working_directory WORKING_DIRECTORY]
                               [--local_src_dir LOCAL_SRC_DIR]

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
                        CUDA version to build for ,
                        such as "10.2" or "11.0". (default: 10.2)
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

                        If no path is given, the default value is build-config.yaml.
                        If build-config.yaml does not exist, and no value is provided,
                        it will be assumed there is a single recipe with the
                        path of "recipe". (default: None)
  --recipes RECIPE_LIST
                        Comma separated list of recipe names to build.
                        (default: None)
  --working_directory WORKING_DIRECTORY
                        Directory to run the script in. (default: None)
  --local_src_dir LOCAL_SRC_DIR
                        Path where package source is downloaded in the form of
                        RPM/Debians/Tar. (default: None)
==============================================================================
```

For example,

```shell
    git clone http://github.com/open-ce/spacy-feedstock
    cd spacy-feedstock
    open-ce build feedstock --output_folder=/home/builder/condabuild
```

## `open-ce build image` sub command

This `open-ce build image` script is used to create a runtime container image with Open-CE
packages (generated from `open-ce build env`) installed in it. This script takes two main arguments
as an input - local conda channel and conda environment file which are the output of `open-ce build env`
script.

The `--container_tool` option can be passed to specify container tool to be used. Additionally 
`--container_build_args` can be passed to set container build options like environment variables
 or other settings like cpusets.

For example,

```shell
    open-ce build image --local_conda_channel=./condabuild
           --conda_env_file=open-ce-conda-env-py3.7-cuda-openmpi.yaml
           --container_tool podman --container_build_args="--build-arg ENV1=test1 --cpuset-cpus 0,1"
```

`local_conda_channel` is the output folder that has all of the conda packages built within it. It has to
be present in the directory from where this `open-ce build image` script is run.
`conda_env_file` is the conda environment file generated from `open-ce build env`.

A container image created has a conda environment that has all the packages mentioned in the
conda environment file, installed in it. The local conda channel being passed is also copied into the
image to enable users to create their custom environments.

Note that the image will not necessarily have all the Open-CE packages installed.
The packages to be installed strictly depends on the conda environment file which is used to build the image.
For more information on how conda environment files are generated and their content, please see
[`doc/README.open_ce_build.md`](README.open_ce_build.md#open-ce-build-$1-sub-command).

So, the ideal sequence of getting Open-CE packages built and installed in a container should be

1. Build packages and target conda environment files using `open-ce build env`
2. Create container image using `open-ce build image`

### Command usage for `open-ce build image`

```shell
==============================================================================
usage: open-ce build image [-h] [--local_conda_channel LOCAL_CONDA_CHANNEL]
                      [--conda_env_files CONDA_ENV_FILES]
                      [--container_build_args CONTAINER_BUILD_ARGS]
                      [--container_tool CONTAINER_TOOL]

Run Open-CE tools within a container

optional arguments:
  -h, --help            show this help message and exit
  --local_conda_channel LOCAL_CONDA_CHANNEL
                        Path where built conda packages are present. (default:
                        condabuild)
  --conda_env_files CONDA_ENV_FILES
                        Comma delimited list of paths to conda environment
                        files. (default: None)
  --container_build_args CONTAINER_BUILD_ARGS
                        Container build arguments like environment variables to
                        be set in the container or cpus or gpus to be used
                        such as "--build-arg ENV1=test1 --cpuset-cpus 0,1".
                        (default: )
  --container_tool CONTAINER_TOOL
                        Container tool to be used. Default is taken from the
                        system, podman has preference over docker. (default: )

==============================================================================
```

### Further details of the OpenCE runtime image

The Dockerfile for this runtime image is located in [`images/opence-runtime/Dockerfile`](https://github.com/open-ce/open-ce/blob/main/images/opence-runtime/Dockerfile).
This file can also be built and run manually and supports GPUs if the system is set up with
`nvidia-container-runtime`. When building the Dockerfile directly, it does require a few arguents,
check the Dockerfile for details.
