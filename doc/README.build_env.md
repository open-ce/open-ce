
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
    ./builder/build_env.py envs/tensorflow-env.yaml
```

while a similar build for pytorch may look like this:

```shell
    ./builder/build_env.py envs/pytorch-env.yaml
```

Other environment files for other packages can also be found in the `envs`
directory; simply specify the file for whichever package environment you want.

Note that the `build_env.py` command executes the `build_feedstock.py` command
as needed, behind the scenes.  This script builds each individual feedstock
component dependency using the build recipe within its own repository.
You do not need to execute `build_feedstock.py` directly yourself, although
you may do so if you wish to perform an individual build of your own
for any given Open-CE feedstock repository.

## Docker build
The `--docker_build` option will build an image and run the build command
inside of a container based on the new image.

As part of this process, it will copy a local_files directory that is in the
current working directory into the container, if the directory exists.

The paths to the `env_config_file`s and `--conda_build_config` must point to
files within the `open-ce` directory and be relative to the directory
containing the `open-ce` directory.

##Command usage for `build_env.py`

```shell
==============================================================================
usage: build_env.py [-h] [--repository_folder REPOSITORY_FOLDER]
                    [--output_folder OUTPUT_FOLDER]
                    [--conda_build_config CONDA_BUILD_CONFIG]
                    [--python_versions PYTHON_VERSIONS]
                    [--build_types BUILD_TYPES] [--git_location GIT_LOCATION]
                    [--git_tag_for_env GIT_TAG_FOR_ENV]
                    [--channels CHANNELS_LIST]
                    [--docker_build]
                    env_config_file [env_config_file ...]

Build conda environment as part of Open-CE

positional arguments:
  env_config_file       Environment config file. This should be a YAML file
                        describing the package environment you wish to build.
                        A collection of files exist under the envs directory.

optional arguments:
  -h, --help            show this help message and exit
  --repository_folder REPOSITORY_FOLDER
                        Directory that contains the repositories. If the
                        repositories don't exist locally, they will be
                        downloaded from OpenCE's git repository. If no value
                        is provided, repositories will be downloaded to the
                        current working directory. (default: )
  --output_folder OUTPUT_FOLDER
                        Path where built conda packages will be saved.
                        (default: condabuild)
  --conda_build_config CONDA_BUILD_CONFIG
                        Location of conda_build_config.yaml file. (default:
                        ./builder/../conda_build_config.yaml)
  --python_versions PYTHON_VERSIONS
                        Comma delimited list of python versions to build for,
                        such as "3.6" or "3.7". (default: None)
  --build_types BUILD_TYPES
                        Comma delimited list of build types, such as "cpu" or
                        "cuda". (default: cpu,cuda)
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
                        local_files will be visible at build time.
                        (default: False)
  --channels CHANNELS_LIST
                        Extra conda channel to be used. (default: [])
==============================================================================
```
