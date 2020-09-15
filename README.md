# open-ce

![Builder Unit Tests](https://github.com/open-ce/open-ce/workflows/Open-CE%20Builder%20Unit%20Tests/badge.svg)
[![Builder Unit Test Coverage](https://codecov.io/gh/open-ce/open-ce/branch/master/graph/badge.svg)](https://codecov.io/gh/open-ce/open-ce)

This is the Open-CE repo for feedstock collection, environment data, and build scripts

Welcome to the **open-ce** repository for Open-CE. This repository
represents the common controlling collection of configuration and
build scripts which are foundational to building the underlying
software component packages (feedstocks) which comprise the greater Open-CE
package ecosystem.  This is a general infrastructure repository; each of the
feedstock components has its own separate repository as well.

This repository provides all that you will need in order to build your own copy
of the Open-CE environment, including (for example) Tensorflow, Pytorch,
XGBoost, and other related packages and dependencies. These packages are built
to run in a conda environment.

Within this **open-ce** repository, you will find:

```text
conda_build_config.yaml:  This is a YAML config file which contains all package
    prerequisite information accumulated from across the Open-CE components
builder/
    This directory contains the parent build scripts, most notably
    `build_env.py` and `build_feedstock.py`.
    `build_env.py` is the script you will use to build Open-CE packages.
envs/
    Contains the YAML environment config files that identify the dependency
    feedstocks for each of the package environments within Open-CE, such as
    tensorflow and pytorch.
ci_common_scripts/
    Contains shell scripts for executing a build of Open-CE components within
    a docker container via `docker_common_run_build_pkg.sh`
doc/
    Documentation files
test/
    Test scripts and files
```

## GETTING STARTED

### Requirements
* `conda` >= 3.8.3 - The conda tool can either be installed through [Anaconda](https://www.anaconda.com/products/individual#Downloads) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).
* `conda-build` >= 3.20 - Once `conda` is installed, `conda-build` can be installed with the command: `conda install conda-build`

### CUDA Requirements
If building packages that use CUDA, a tar package of TensorRT 7.0 for CUDA 10.2 will need to be [downloaded](https://developer.nvidia.com/nvidia-tensorrt-7x-download) ahead of time. The downloaded file should be placed in a new local directory called `local_files`.

Currently CUDA 10.2 is supported by the recipes in Open-CE. The `cudatoolkit` and `cudatoolkit-dev` packages can be sourced from [IBM WML CE](https://public.dhe.ibm.com/ibmdl/export/pub/software/server/ibm-ai/conda/#/).

### Building a Collection of Packages
The `build_env.py` script can be used to build a collection of Open-CE packages. An environment file needs to be passed in as input. A selection of environment files are provided within the `envs` directory for different frameworks such as TensorFlow and PyTorch. The output from running `build_env.py` will be a local conda channel (by default called `condabuild`). For more details on `build_env.py`, please see `doc/README.build_env.md`.

The following commands will build all of the Open-CE packages for Python 3.6, including CUDA builds and cpu-only builds. The commands should be run from within the same directory that contains `local_files`.

```bash
# Clone Open-CE from GitHub
git clone https://github.com/open-ce/open-ce.git
# Build packages
./open-ce/builder/build_env.py open-ce/envs/opence-env.yaml
```

### Building a Single Feedstock
The `build_feedstock.py` script can be used to build a single feedstock (which could produce one or more conda packages). The output from running `build_feedstock.py` will be a local conda channel (by default called `condabuild`). For more details on `build_feedstock.py`, please see `doc/README.build_feedstock.md`.

The following commands will build all of the packages within a feedstock named `MY_FEEDSTOCK`.

```bash
# Clone Open-CE from GitHub
git clone https://github.com/open-ce/open-ce.git
# Clone MY_FEEDSTOCK from GitHub
git clone https://github.com/open-ce/MY_FEEDSTOCK-feedstock.git
# Build packages
./open-ce/builder/build_feedstock.py --working_directory MY_FEEDSTOCK-feedstock
```

### Installing Packages
After performing a build, a local conda channel will be created. By default, this will be within a folder called `condabuild` (it can be changed using the `--output_folder` argument). After the build, packages can be installed within a conda environment from this local channel. See conda's [documentation](https://docs.conda.io/projects/conda/en/latest/user-guide/index.html) for more information on conda environments.

The following command will install a package named `PACKAGE` from the local conda channel `condabuild` into the currently active conda environment.

```bash
conda install -c ./condabuild PACKAGE
```

### Contributions
We are working on the contribution guidelines, please check back soon. In the meantime feel free to open an issue for a bug report or feature request.
