
# README for Open-CE Environment Files


This README documents the Open-CE Environment YAML files used by the build scripts
[build_env.py](README.build_env.md)
and [build_feedstock.py](README.build_feedstock.md).
Please refer to the respective README files for each of these two scripts.

Most likely you will want to simply use the Open-CE environment files provided within the
open-ce repository as they are. These files have already been customized and
verified to work. However, if you want to debug or do your own customizations,
you can edit them or create your own environment files for use by these scripts. If you
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

There are a number of keywords that can be used in the environment files, each one
serving a different purpose. All are used to define key-value pairs as used in a
YAML file format. The keywords recognized for Open-CE environments include the
following:
```
packages:      # The environment package name
  - feedstock: # Defines each feedstock comprising the environment
  - channels:  # Defines a channel location for obtaining dependencies
  - git_tag:   # Defines a specific git tag to use for this package
  - recipes:   # Sets name and path of recipe location(s)
imported_envs: # Used to import content of one env file into another
channels:      # Defines a channel location for obtaining dependencies
git_tag_for_env: # Specify a git tag to use across all packages in environment
```

Most of these are optional. At a minimum, the environment files will define one
or more feedstocks under the `packages` stanza. Other keyword elements are used
only infrequently, typically to override defaults.

In the most common basic case, each environment file has a `packages` stanza
which lists a number of feedstock repositories that are needed to build as
requisites. Each feedstock dependency is listed on a separate line in the stanza.
For example, in [xgboost-env.yaml](../envs/xgboost-env.yaml):
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

The other keywords that optionally can be used as part of the `packages` stanza
include `git_tag`, `channels`, and `recipes`. By default, the git tag will be
the current (i.e. main or master) branch of the specified source tree, such that
you don't need to include this keyword unless you want to explicitly override it
to fetch a different version. To do this, you will simply specify the version
value or the hexadecimal git tag value that you want to obtain during the build.
An example might look something like this:
```
packages:
  - feedstock: dummy_example
  - git_tag: v1.0.0
```
This might be useful if there is a new default version, but you want to
specifically build an older tagged version.

For `channels`, if you need to add a package dependency that is not found within
open-ce but which is available at some other external delivery channel, you can
specify the URL to the desired channel as seen below (replacing the URL with
whatever is appropriate for your build):
```
packages:
  channels:
    - https://anaconda.org/anaconda
```

While this example shows usage specific to one `packages` stanza, the `channels`
keyword can also be defined on its own for use throughout the environment file
(see below).

Finally, a package might define more than one recipe, particularly if it will
build into more than one variant. One example of this is tensorflow, which
can build both a default GPU and CPU version, handled by using multiple
recipes. While you could specify this as part of the `packages` stanza, you
can find the more typical usage within Open-CE in which the respective
package feedstock has its own `config/build-config.yaml` file that defines
the individual recipes. For example, the
[tensorflow-feedstock](https://github.com/open-ce/tensorflow-feedstock)
`config/build_config.yaml` file defines recipes in this way:
```
recipes:
  - name : tensorflow-select
    path : select_recipe

  - name : tensorflow-base
    path : recipe

  - name : tensorflow-meta
    path : meta_recipe
```
If you look in the
[tensorflow-feedstock](https://github.com/open-ce/tensorflow-feedstock) tree,
you will see that each of these `path` specifiers has a directory name that is
present in the feedstock repo, and within each path is a `meta.yaml` file which
represents the recipe for each separate package.


Another stanza type that you might see in some environment files is
`imported_envs`. An example found in
[horovod-env.yaml](../envs/horovod-env.yaml)
looks like:
```
imported_envs:
  - pytorch-env.yaml
  - tensorflow-env.yaml
```
This is straightforward; it effectively creates a nested environment file by simply
importing the contents of the listed environment files. So if you are building the
horovod environment, you will get a build of both pytorch and tensorflow as well
because of the specified imported environments listed in this section.


As mentioned earlier, the `channels` specifier can also be used as a universal keyword
within an environment file; in fact, this is probably the more common usage.
This means that the any external dependencies will be searched in the specified
URL channel, for any of the packages in the build. You would only need to do this if
a package dependency is not found as part of open-ce but which is available
at some other external delivery channel. You can specify the URL to the desired
channel as seen below, placing this at the top of the file (again, replacing this
sample URL with the one you want to use):
```
channels:
  - https://public.dhe.ibm.com/ibmdl/export/pub/software/server/ibm-ai/conda/
```

The keyword `git_tag_for_env` can also be used to set a universal key-value definition
for an environment file. This is much like the `git_tag` described above for an
individual package stanza, but in this case it would be in effect for the whole
environment (although it can be overridden by an individual package `git_tag`).
You would likely not typically use this, unless you are doing custom builds based
off of a tagged version of open-ce which is not the current default one. For
example, if you wanted to stay doing custom build variants based on the very first
open-ce release tag, you could achieve this by defining:
```
git_tag_for_env:
  - open-ce-v1.0.0
```


The stanza types above are the only elements that are used by the open-ce environment
[build_env.py](README.build_env.md) builds. However, as each feedstock in the list is
built, other file information is used from the individual configuration files of each
respective feedstock repository, normally found as a recipe in the `config/meta.yaml`
within each feedstock.

