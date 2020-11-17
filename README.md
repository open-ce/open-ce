<p align="center">
  <img src="https://avatars0.githubusercontent.com/u/68873540?s=400&u=a02dc4156e50cdffb23172aba7133e44381885d4&v=4" alt="Open-CE Logo" width="30%">
</p>

![Builder Unit Tests](https://github.com/open-ce/open-ce/workflows/Open-CE%20Builder%20Unit%20Tests/badge.svg)
[![Builder Unit Test Coverage](https://codecov.io/gh/open-ce/open-ce/branch/master/graph/badge.svg)](https://codecov.io/gh/open-ce/open-ce)
![Python version](https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8-blue.svg)
![GitHub Licence](https://img.shields.io/github/license/open-ce/open-ce.svg)

---

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
open-ce/
    This directory contains the build and validation tool `open-ce`.
    For more information run `./open-ce/open-ce -h`
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

* `conda` >= 3.8.3
  * The conda tool can either be installed through [Anaconda](https://www.anaconda.com/products/individual#Downloads) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).
* `conda-build` >= 3.20
  * Once `conda` is installed, `conda-build` can be installed with the command: `conda install conda-build`
* `python` >= 3.6
* `docker` >= 1.13
  * Docker is only required when using the `--docker_build` option (see below).

### CUDA Requirements

Currently CUDA 10.2 is supported by the recipes in Open-CE. Please see [`doc/README.cuda_support.md`](doc/README.cuda_support.md) for details on setting
up a proper build enviornment for CUDA support.

Open-CE expects the `CUDA_HOME` environment variable to be set to the location of the CUDA installation.

When building packages that use CUDA, a tar package of TensorRT 7.0 for CUDA 10.2 will need to be [downloaded](https://developer.nvidia.com/nvidia-tensorrt-7x-download) ahead of time. The downloaded file should be placed in a new local directory called `local_files`. The [cuda README](doc/README.cuda_support.md) has more information.

### Building a Collection of Packages

To build an entire integrated and functional conda channel using Open-CE, start by installing the needed tools in the [Requirements](#requirements) section above.
The `open-ce build env` command can then be used to build a collection of Open-CE packages. An Open-CE environment file needs to be passed in as input. A selection of environment files are provided within the `envs` directory for different frameworks such as TensorFlow and PyTorch. The output from running `open-ce build env` will be a local conda channel (by default called `condabuild`) and one or more conda environment file(s) in the output folder depending on the selected build configuration. For more details on `open-ce build env`, please see [`doc/README.open_ce_build.md`](doc/README.open_ce_build.md#open-ce-build-env-sub-command).

The following commands will use the `opence-env.yaml` Open-CE environment file to build all of the Open-CE packages for Python 3.6 (the default), including CUDA builds and cpu-only builds (also the default). The commands should be run from within the same directory that contains `local_files`.

```bash
# Clone Open-CE from GitHub
git clone https://github.com/open-ce/open-ce.git
# Build packages
./open-ce/open-ce/open-ce build env open-ce/envs/opence-env.yaml
```

The following commands will use opence-env.yaml Open-CE environment file from a specific Open-CE release to build all of the Open-CE packages for Python 3.6, 3.7 and 3.8, including only CUDA builds. The commands should be run from within the same directory that contains `local_files`.

```bash
# Clone a specific Open-CE release from GitHub
git clone https://github.com/open-ce/open-ce.git --branch open-ce-v1.0.0
# Build packages
./open-ce/open-ce/open-ce build env --python_versions 3.6,3.7,3.8 --build_types cuda open-ce/envs/opence-env.yaml
```

#### Building within a docker container

Passing the `--docker_build` argument to the `open-ce build env` command will create a docker image and perform the actual build inside of a container based on that image. This will provide a "clean" environment for the builds and make builds more system independent. It is recommended to build with this option as opposed to running on a bare metal machine. For more information on the `--docker_build` option, please see [`doc/README.open_ce_build.md`](doc/README.open_ce_build.md#open-ce-build-env-sub-command).

### Building a Single Feedstock

The `open-ce build feedstock` command can be used to build a single feedstock (which could produce one or more conda packages). The output from running `open-ce build feedstock` will be a local conda channel (by default called `condabuild`). For more details on `open-ce build feedstock`, please see [`doc/README.open_ce_build.md`](doc/README.open_ce_build.md#open-ce-build-feedstock-sub-command).

The following commands will build all of the packages within a feedstock named `MY_FEEDSTOCK`.

```bash
# Clone Open-CE from GitHub
git clone https://github.com/open-ce/open-ce.git
# Clone MY_FEEDSTOCK from GitHub
git clone https://github.com/open-ce/MY_FEEDSTOCK-feedstock.git
# Build packages
./open-ce/open-ce/open-ce build feedstock --working_directory MY_FEEDSTOCK-feedstock
```

### Installing Packages

After performing a build, a local conda channel will be created. By default, this will be within a folder called `condabuild` (it can be changed using the `--output_folder` argument). After the build, packages can be installed within a conda environment from this local channel. If the packages are built using `open-ce build env` script, then a conda environment file will also be generated which can be used to generate a conda environment with the built packages installed in it. See conda's [documentation](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) for more information on conda environments.

The following command will install a package named `PACKAGE` from the local conda channel `condabuild` into the currently active conda environment.

```bash
conda install -c ./condabuild PACKAGE
```

The following command can be used to create a conda environment using a conda environment file.

```bash
conda env create -f <conda_environment_file>
```

### Creating Docker Image with Open-CE Packages installed

After performing the build using `open-ce build env`, the `open-ce build image` command can be used to create a runtime docker image containing the newly created conda channel, as well as a conda environment with the newly build Open-CE packages. For more details on `open-ce build image`, please see [`doc/README.open_ce_build.md`](doc/README.open_ce_build.md#open-ce-build-image-sub-command).

### Contributions

For contribution information, please see the [CONTRIBUTING.md](CONTRIBUTING.md) page.
