[![Open-CE Stars](https://img.shields.io/github/stars/open-ce?style=social)](https://github.com/open-ce/open-ce/stargazers)

<p align="center">
  <img src="https://avatars0.githubusercontent.com/u/68873540?s=400&u=a02dc4156e50cdffb23172aba7133e44381885d4&v=4" alt="Open-CE Logo" width="30%">
</p>

[![Python Support](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue.svg)](#requirements)
[![Cuda Support](https://img.shields.io/badge/cuda-11.2%20%7C%2011.4-blue)](#)
[![Architecture Support](https://img.shields.io/badge/architecture-x86%20%7C%20ppc64le%20%7C%20s390x-blue)](#)
[![GitHub Licence](https://img.shields.io/github/license/open-ce/open-ce.svg)](LICENSE)
---

This is the Open-CE project for feedstock collection, environment data, and build scripts

Welcome to the **open-ce** project. The project contains everything that is needed to build conda packages for
a collection of machine learning and deep learning frameworks. All packages created for a specific version of
Open-CE have been designed to be installed within a single conda environment. For more information on `conda`,
please look at conda's official [documentation](https://docs.conda.io/).

This repository contains a collection of Open-CE files that can be used to create a conda channel. The conda channel
will contain packages for every feedstock listed within the Open-CE files. Different variants of Python and CUDA can
be specified at build time. Open-CE currently supports the following:

| | Supported Versions |
| --- | --- |
| Architecture | Power, x86, s390x |
| Python | 3.8, 3.9, 3.10 |
| CUDA | 11.2, 11.4 |


The `open-ce` tool can also be used to build all or some of the packages provided by Open-CE. For more information on the `open-ce` tool,
please see the open-ce-builder [repository](https://github.com/open-ce/open-ce-builder).

## GETTING STARTED

### Requirements

* `conda`
  * The conda tool can either be installed through [Anaconda](https://www.anaconda.com/products/individual#Downloads) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

### Community Builds

Oregon State University hosts pre-built versions of the Open-CE conda channels [here](https://osuosl.org/services/powerdev/opence/). These
channels provide packages for both Power and x86 architectures. The latest version of Open-CE can be pulled down using the channel:
https://ftp.osuosl.org/pub/open-ce/current/.

MIT hosts pre-built versions of Open-CE for the IBM Power architecture. Multiple versions of Open-CE are hosted within this single channel: https://opence.mit.edu/.

### Installing Packages

Open-CE packages can be installed from one of the community [builds](#community-builds). To install packages from one of the community channels, pass the channel's URL to the `conda` tool using the `-c` option.

The following command will install the tensorflow package from the most recent version of Open-CE hosted in within the OSU channel:

```bash
conda install -c https://ftp.osuosl.org/pub/open-ce/current/ tensorflow
```

For more information on installing conda packages, please see the official conda [documentation](https://docs.conda.io/).

For more information on installing conda packages created from using the `open-ce` tools locally, please see the open-ce-builder [repository](https://github.com/open-ce/open-ce-builder).

## Contributions

For contribution information, please see the [CONTRIBUTING.md](CONTRIBUTING.md) page.

## Slack Community

Join us on [Slack!](http://open-ce.slack.com/) Use [this link](https://join.slack.com/t/open-ce/shared_invite/zt-o27t9db6-oUklancQvdGO8FIwftDwgw) or ping the [@open-ce/open-ce-dev-team](https://github.com/orgs/open-ce/teams/open-ce-dev-team) for an invite.

