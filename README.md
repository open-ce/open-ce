# open-ce

![Builder Unit Tests](https://github.com/open-ce/open-ce/workflows/builder-unit-test/badge.svg)
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

To get started with the basic commands to build the Open-CE environment (e.g.
to build all of `tensorflow` or `pytorch` or another package), see the
`README.build_env.md` file in the doc directory.  The `build_env.py` command
is the fundamental script to perform the build(s).
