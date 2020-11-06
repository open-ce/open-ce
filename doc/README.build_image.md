
# README for build_image.py

This `build_image.py` script is used to create a runtime docker image with Open-CE
packages (generated from `build_env.py`) installed in it. This script takes two arguments
as an input - local conda channel and conda environment file which are the output of `build_env.py`
script.

For example,
```shell
    open-ce/open-ce/build_image.py --local_conda_channel=./condabuild
           --conda_env_file=open-ce-conda-env-py3.7-cuda-openmpi.yaml
```

`local_conda_channel` is the output folder that has all of the conda packages built within it. It has to
be present in the directory from where this `build_image.py` script is run.
`conda_env_file` is the conda environment file generated from `build_env.py`. 

A docker image created has a conda environment that has all the packages mentioned in the 
conda environment file, installed in it. The local conda channel being passed is also copied into the
image to enable users to create their custom environments.

Note that the image will not necessarily have all the Open-CE packages installed.
The packages to be installed strictly depends on the conda environment file which is used to build the image.
For more information on how conda environment files are generated and their content, please see 
[`doc/README.build_env.md`](doc/README.build_env.md).

So, the ideal sequence of getting Open-CE packages built and installed in a container should be
1. `build_env.py` 
2. `build_image.py`

## Command usage for `build_image.py`

```shell
==============================================================================
usage: build_image.py [-h] [--local_conda_channel LOCAL_CONDA_CHANNEL]
                      [--conda_env_file CONDA_ENV_FILE]

Run Open-CE tools within a container

optional arguments:
  -h, --help            show this help message and exit
  --local_conda_channel LOCAL_CONDA_CHANNEL
                        Path where built conda packages are present. (default:
                        condabuild)
  --conda_env_file CONDA_ENV_FILE
                        Location of conda environment file. (default: None)

==============================================================================
```
