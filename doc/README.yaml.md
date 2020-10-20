
# README for Open-CE Environment Files


This README documents the YAML files used by the build scripts
[build_env.py](README.build_env.md)
and [build_feedstock.py](README.build_feedstock.md).
Please refer to the respective README files for each of these two scripts.

Most likely you will want to simply use the Open-CE environment files provided within the
open-ce repository as they are. These files have already been customized and
verified to work. However, if you want to debug or do your own customizations,
you can edit them or create your own YAML files for use by these scripts. If you
do this, you will likely want to start by copying one of the existing files and
making local edits as desired.


# Open-CE Environment File

The `build_env.py` command uses what we call an Open-CE environment file.
In this context, an "environment" is a fully-built core package along with all
of its dependencies, each of which is found in a separate "feedstock" repository
within the broader open-ce project.
Default environment files are provided for each of several environments in the open-ce
repository, within [https://github.com/open-ce/open-ce/envs](../envs)
These files are named for their package environments, e.g.
[tensorflow-env.yaml](../envs/tensorflow-env.yaml)
or [pytorch-env.yaml](../envs/pytorch-env.yaml),
among others. You can review these files as examples.

Each environment file will contain a "packages" stanza which will list a number
of feedstock repositories that are needed to build as requisites. Each feedstock
dependency is listed on a separate line in the stanza. For example, in
[xgboost-env.yaml](../envs/xgboost-env.yaml):
```
packages:
  - feedstock : nccl              #[build_type == 'cuda']
  - feedstock : xgboost
```
Here you see two feedstocks listed; these correspond to the open-ce repository
tree for [nccl-feedstock](https://github.com/open-ce/nccl-feedstock) and
[xgboost-feedstock](https://github.com/open-ce/xgboost-feedstock) respectively.
Here, notice the `cuda` designation on the nccl feedstock line. This will only
be built if the `build_type` is set to `cuda` when executing the `build_env.py`
script, so it is considered an optional dependency that you may want to include
if your runtime environment has CUDA available.

Another stanza type that you might see in some environment files is
`imported_envs`. An example found in
[horovod-env.yaml](../envs/horovod-env.yaml)
looks like:
```
imported_envs:
  - pytorch-env.yaml
  - tensorflow-env.yaml
```
This is straightforward; it simply imports the contents of the listed environment
files. So if you are building the horovod environment, you will get a build of
both pytorch and tensorflow as well because of the specified imported
environments listed in this section.

Another optional feature that you might use in some customization scenarios is the
`channels` specifier.  If you are creating an environment file and you have a need
to add a package dependency that is not found within open-ce but which is available
at some other external delivery channel, you can specify the URL to the desired
channel as seen below, placing this at the top of the file (and replacing this
sample URL with the one you want to use):
```
channels:
  - https://public.dhe.ibm.com/ibmdl/export/pub/software/server/ibm-ai/conda/
```

These stanza types are normally the only elements that are used by the open-ce
`build_env.py` builds. However, as each feedstock in the list is built, other
file information is used from the configuration files of each respective feedstock
repository.


