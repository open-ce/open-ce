
# README for build_env.py

For a general build to generate desired images for a specific package,
a build is achieved by executing the script `build_env.py`. This will extract
and build all of the individual required components within the various Open-CE
feedstock repository trees required for the requested package environment.
In other words, if you simply want to build a package such as tensorflow or
pytorch (or any other; see the `open-ce/envs` subdirectory), with dependencies
automatically handled, you can do so using a single `build_env.py` command.

For example:
In the simplest case, a build for tensorflow may look like this:

```shell
    ./open-ce/build_env.py envs/tensorflow-env.yaml
```

while a similar build for pytorch may look like this:

```shell
    ./open-ce/build_env.py envs/pytorch-env.yaml
```

Other environment files for other packages can also be found in the `envs`
directory; simply specify the file for whichever package environment you want.

> Note: that the `build_env.py` command executes the `build_feedstock.py` command
> as needed, behind the scenes.  This script builds each individual feedstock
> component dependency using the build recipe within its own repository.
> You do not need to execute `build_feedstock.py` directly yourself, although
> you may do so if you wish to perform an individual build of your own
> for any given Open-CE feedstock repository.

## Docker build

The `--docker_build` option will build an image and run the build command
inside of a container based on the new image.

As part of this process, it will copy a local_files directory that is in the
current working directory into the container, if the directory exists.

The paths to the `env_config_file`s and `--conda_build_config` must point to
files within the `open-ce` directory and be relative to the directory
containing the `open-ce` directory.

## Use System MPI

By default, building the entire
[Open-CE environment file](https://github.com/open-ce/open-ce/blob/master/envs/opence-env.yaml)
will include a build of [OpenMPI](https://github.com/open-ce/openmpi-feedstock)
which will be used for packages that need MPI, like
[Horovod](https://github.com/open-ce/horovod-feedstock). To use a system install of
MPI instead, `--mpi_types system` can be passed as an argument to `build_env.py`. Build success
will require that the MPI environment is correctly set up.

## Command usage for `build_env.py`

```shell
==============================================================================
usage: build_env.py [-h] [--conda_build_config CONDA_BUILD_CONFIG]
                    [--output_folder OUTPUT_FOLDER] [--channels CHANNELS_LIST]
                    [--repository_folder REPOSITORY_FOLDER]
                    [--python_versions PYTHON_VERSIONS]
                    [--build_types BUILD_TYPES] [--mpi_types MPI_TYPES]
                    [--git_location GIT_LOCATION]
                    [--git_tag_for_env GIT_TAG_FOR_ENV] [--docker_build]
                    env_config_file [env_config_file ...]

Build conda environment as part of Open-CE

positional arguments:
  env_config_file       Environment config file. This should be a YAML file
                        describing the package environment you wish to build.
                        A collection of files exist under the envs directory.

optional arguments:
  -h, --help            show this help message and exit
  --conda_build_config CONDA_BUILD_CONFIG
                        Location of conda_build_config.yaml file. (default:
                        /mnt/pai/home/bnelson/git/open-ce/open-
                        ce/../conda_build_config.yaml)
  --output_folder OUTPUT_FOLDER
                        Path where built conda packages will be saved.
                        (default: condabuild)
  --channels CHANNELS_LIST
                        Conda channels to be used. (default: [])
  --repository_folder REPOSITORY_FOLDER
                        Directory that contains the repositories. If the
                        repositories don't exist locally, they will be
                        downloaded from OpenCE's git repository. If no value
                        is provided, repositories will be downloaded to the
                        current working directory. (default: )
  --python_versions PYTHON_VERSIONS
                        Comma delimited list of python versions to build for ,
                        such as "3.6" or "3.7". (default: 3.6)
  --build_types BUILD_TYPES
                        Comma delimited list of build types, such as "cpu" or
                        "cuda". (default: cpu,cuda)
  --mpi_types MPI_TYPES
                        Comma delimited list of mpi types, such as "openmpi"
                        or "system". (default: openmpi)
  --git_location GIT_LOCATION
                        The default location to clone git repositories from.
                        (default: https://github.com/open-ce)
  --git_tag_for_env GIT_TAG_FOR_ENV
                        Git tag to be checked out for all of the packages in
                        an environment. (default: None)
  --docker_build        Perform a build within a docker container. NOTE: When
                        the --docker_build flag is used, all arguments with
                        paths should be relative to the directory containing
                        open-ce. Only files within the open-ce directory and
                        local_files will be visible at build time. (default:
                        False)
==============================================================================
```

## Conda environment files

`build_env.py` also generates conda environment files based on the configuration
 selected for a build. For e.g. if `build_env.py` is run for `tensorflow-env.yaml` and
 for python_versions `3.7`, build_type `cuda` and mpi_type being `openmpi`, then a
 conda environment file with name `open-ce-conda-env-py3.7-cuda-openmpi.yaml` gets
 generated. This environment file can be used to create a conda environment with
 the packages listed in `tensorflow-env.yaml` installed in it.

```shell
    ./open-ce/build_env.py --python_versions=3.7 --build_type=cuda --mpi_type=openmpi
    envs/tensorflow-env.yaml
```

 The above command will output `open-ce-conda-env-py3.7-cuda-openmpi.yaml` in the specified
 output folder (or by default `./condabuild` directory).

 The following command can be used to create a conda environment using the generated conda
 environment file -

```shell
    conda env create -f open-ce-conda-env-py3.7-cuda-openmpi.yaml
```

There could be one or more conda environment files generated for each variant based on inputs 
given to `build_env.py`. For example, if `build_env.py` is run without any `build_type` and python_versions 
`3.7` and mpi_type as `openmpi`, then two files will be generated namely -
`open-ce-conda-env-py3.7-cuda-openmpi.yaml`, `open-ce-conda-env-py3.7-cpu-openmpi.yaml`. 

`build_env.py` can generate these target conda environment files for a given Open-CE environment file 
and provided build configuration even without performing an actual build.
