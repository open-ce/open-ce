
# README for Open-CE build YAML files


This README documents the YAML files used by the build scripts
[build_env.py](https://github.com/open-ce/open-ce/blob/master/doc/README.build_env.md)
and [build_feedstock.py](https://github.com/open-ce/open-ce/blob/master/doc/README.build_feedstock.md).
Please refer to the respective README files for each of these two scripts.

Most likely you will want to simply use the YAML files provided within the
open-ce repository as they are. These files have already been customized and
verified to work. However, if you want to debug or do your own customizations,
you can edit them or create your own YAML files for use by these scripts. If you
do this, you will likely want to start by copying one of the existing files and
making local edits as desired.

NOTE: This file only documents information about the YAML files as used within
the open-ce project. This file is nowhere near being a full reference of the
YAML configuration markup language. Only fields of interest to open-ce are noted
here. For more detail or education about YAML files in general, refer to the
public YAML specifications at https://yaml.org/ or in any number of independent
guides available elsewhere online.


# build_env environment YAML file

The `build_env.py` command uses what we call an environment YAML file.
In this context, an "environment" is a fully-built core package along with all
of its dependencies, each of which is found in a separate "feedstock" repository
within the broader open-ce project.
Default YAML files are provided for each of several environments in the open-ce
repository, within https://github.com/open-ce/open-ce/tree/master/envs
These files are named for their package environments, e.g.
[tensorflow-env.yaml](https://github.com/open-ce/open-ce/blob/master/envs/tensorflow-env.yaml)
or [pytorch-env.yaml](https://github.com/open-ce/open-ce/blob/master/envs/pytorch-env.yaml),
among others. You can review these files as examples.

Each environment file will contain a "packages" stanza which will list a number
of feedstock repositories that are needed to build as requisites. Each feedstock
dependency is listed on a separate line in the stanza. For example, in
[xgboost-env.yaml](https://github.com/open-ce/open-ce/blob/master/envs/xgboost-env.yaml):
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

Another stanza type that you might see in some environment YAML files is
`imported_envs`. An example found in
[horovod-env.yaml](https://github.com/open-ce/open-ce/blob/master/envs/horovod-env.yaml)
looks like:
```
imported_envs:
  - pytorch-env.yaml
  - tensorflow-env.yaml
```
This is straightforward; it simply imports the contents of the listed yaml
files. So if you are building the horovod environment, you will get a build of
both pytorch and tensorflow as well because of the specified imported
environments listed in this section.

These two stanza types (packages, imported_envs) are really the only
YAML elements that are used for the open-ce `build_env.py` builds. However, as
each feedstock in the list is built, other YAML file information is used from
the yaml files of each respective feedstock repository.


# build_feedstock YAML file (meta.yaml)

In most cases you will just use the `build_env.py` command to build an open-ce
environment. As an alternative, with the `build_feedstock.py` command, you could
selectively build any individual feedstock if you wished to do so.
In general, each feedstock repository within the open-ce project has its own
recipe `meta.yaml` file, which can be used exactly as found in the respective
feedstock repository tree. Optionally, you can edit your own local copy of the
`meta.yaml` file to make customizations, once you understand the most common
file sections as described here.

You will notice that the open-ce project at https://github.com/open-ce contains
many repositories that end with a `-feedstock` suffix. Each of these represents
one of the many feedstocks that comprise open-ce. While there are exceptions,
most feedstocks contain a `meta.yaml` within the `recipe` directory of the repo.
For purposes of illustration here, let's use the `pytorch-feedstock`
[meta.yaml](https://github.com/open-ce/pytorch-feedstock/blob/master/recipe/meta.yaml) to explain the various sections.  (Note that this is a living file that
will change over time, so the versions, patches, and other content will not
always be the same).

At the start of the `meta.yaml` file, we will typically set a version variable
to indicate the version of the upstream package in use. The version definition
is declared like this:
```
{% set version = "1.6.0" %}
```
This indicates we are building pytorch version `1.6.0` of course, so if you
are editing to build another version you would reflect that change here. The
default version provided by open-ce will normally change over time as well.

The `meta.yaml` file will always declare the package name and version, using
the `package` stanza name.  For example:
```
package:
  name: pytorch-base
  version: {{ version }}
```
Here you see the name and version specified as elements of `package`. Notice
the use of double braces for `{{ version }}`; this calls back to the variable
that we set at the top of the file, rather than hard-coding the version here.

The next required section is the `source`. Of course, open-ce does not itself
contain copies of the source for the various packages. Instead, as a feedstock,
it points to the primary source location for each package. The `source` stanza
will point to the git tree with the `git_url` keyword, and the version with the
`git_vers` keyword, again shown here with a pytorch example:
```
source:
  git_url: https://github.com/pytorch/pytorch.git
  git_rev: v{{ version }}
  patches:
    - example_fix_for_some_issue.patch
```
Note again that we are using the `{{ version}}` variable; the leading `v`
character is due to the pytorch repository using `v1.6.0` as the tagged branch
version (with a leading `v`). In the example, you will also see the use of the
`patches` keyword. This is used to indicate any needed standard diff-formatted
patch files that are to be applied to the source tree before building. These
patch(es) will reside in the same directory as the `meta.yaml` file, and there
may be multiple patches listed here, one per line in the same format seen above.
If no patches are necessary, this part can be omitted from the `source` stanza.
A source patch is the best way for you to add a small fix or make your own
minor customization to the source.

The next section of the `meta.yaml` file will generally be the `requirements`
stanza.  The `requirements` in turn has subsections, most typically `build`,
`host`, and `run`.  A partial example (edited here for brevity):
```
requirements:
  build:
    - {{ compiler('c') }}
    - {{ compiler('cxx') }}
    - libgcc-ng
    - {{ compiler('fortran') }}

  host:
    - make
    - cmake {{ cmake }}
    - python {{ python }}
    - numpy {{ numpy }}

  run:
    - python {{ python }}
    - numpy {{ numpy }}
    - cffi {{ cffi }}
```
These sections document build compiler tools (`build`) and host packages
(`host`) needed on the build system to to build the package for the given
feedstock, as well as the (`run`) packages required at run-time. Notice again
the use of the `{{  }}` bracket variable syntax. In this case, for variable
definitions, we are calling back to a core YAML file found in the primary
open-ce repository called
[conda_build_config.yaml](https://github.com/open-ce/open-ce/blob/master/conda_build_config.yaml). This file contains a number of dependency package versions
which are known to collectively work together across the open-ce environment.
The syntax of the `compiler` variables are unique because they are in turn
specifying different values depending on whether you are building for `ppc64le`
or `x86_64`. You can see this variation in definition in the common file:
```
c_compiler_version:
  - 7.2.*                      # [x86_64]
  - 7.3.*                      # [ppc64le]
```
When you see a line such as `- numpy {{ numpy }}` you are seeing first a
reference to the literal package name, `numpy`, followed by the `numpy` version
variable defined in the `conda_build_config.yaml` file. This is done by default
for open-ce to ensure common package functionality and dependencies across the
open-ce ecosystem, though you could experiment by editing your local `meta.yaml`
if you wanted to try building with a different version. The open-ce project
will only update the version of any dependency when it is proven to work across
the board for open-ce packages.

Next is the `build` section.  This can vary quite a bit among the different
feedstocks, so you may want to inspect several examples. Essentially, this
is a build information section for executing the build and it will always
have a `number` which is a build number incremented for each change made
within the same version of the package (for example, when a new patch or other
similar change is added wihout a version update). A basic example:
```
build:
  number: 1
  string: py{{ python | replace(".", "") }}_{{ PKG_BUILDNUM }}
```
The `string` is formatted to replace the python version number in the package
with an abbreviation, so if you have built with python 3.7 this string would
define itself as `py37` (the py characters and the python version). For more
information about this section, it may be better to look at existing open-ce
`meta.yaml` files for examples and cross-reference with the external build
documentation, such as Conda's own information:
[conda docs](https://docs.conda.io/projects/conda-build/en/latest/resources/define-metadata.html#build-section)

Finally, in our `meta.yaml` files you will see an `about` section. These fields
are fairly straightforward, although notice that the License refers to the
upstream license of the package itself (which may be different than the open-ce
project build files, which are ApacheV2.0 licensed).
```
about:
  home: http://pytorch.org/
  license: BSD 3-Clause
  license_family: BSD
  license_file: LICENSE
  summary: PyTorch is an optimized tensor library for deep learning using GPUs and CPUs.
  description: |
    PyTorch is an optimized tensor library for deep learning using GPUs and CPUs

extra:
  recipe-maintainers:
    - open-ce/open-ce-dev-team

```
This section should be generally self-explanatory, although also note that we
added an `extra` section in which we simply provide a reference to document the
`open-ce-dev-team` as the maintainers of the official project `meta.yaml` files.

If you are trying to build your own `meta.yaml` file or are making your own
edits, and if you have some questions that are not clear here, you may want to
reach out to others on the [open-ce Gitter](https://gitter.im/open-ce/community) community and ask.
