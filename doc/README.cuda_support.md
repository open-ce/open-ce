# Open-CE CUDA Support

The Open-CE build scripts and feedstocks support CUDA from NVIDIA. In order
for the build scripts to work, CUDA must be installed on the system on which
the builds are taking place. This can be accomplished in two ways (see below).

**In all cases, the `CUDA_HOME` environment variable must be set to the base
directory where CUDA has been installed.**

## Bare metal builds

If you are using Open-CE on a bare metal system. Install the appropriate version
of CUDA on the server that matches the version of Open-CE you are using. There
is a reference table below.

| Open-CE version | CUDA version |
|-----------------|--------------|
| 1.0 (marmotini) | 10.2         |
| 1.1 (unnamed) | 10.2 \| 11.0  |

It's important to install CUDA correctly. This procedure is dependent on the system
type and CUDA version. It's advised to follow NVIDIA's [official installation documentation](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html)
Note that NVLINK2-enabled POWER9 systems require a few [extra steps](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html#power9-setup)

## Container builds

It is recommended to run the Open-CE build scripts within a container. NVIDIA provides
official CUDA base containers [on](https://hub.docker.com/r/nvidia/cuda) [dockerhub](https://hub.docker.com/r/nvidia/cuda-ppc64le),
which are ideal for ensuring a properly installed CUDA environment.

Open-CE provides a working set of images that will work for running CUDA enabled builds.
These images use the official CUDA images referenced above as a base image. Dockerfiles for
these images are located in the [images directory](../images)
To build these images manually, use the command below.

```shell
docker build open-ce/images/build-cuda-x86_64
```

The Open-CE build image presets the `CUDA_HOME` environment variable to the appropriate location.

### Automatic docker builds

The [`open-ce build env`](README.open_ce_build.md#open-ce-build-env-sub-command) command supports the `--docker_build` command line argument.
This argument will automatically build the Open-CE CUDA-enabled build image and when combined
with the `--build_types=cuda` command line argument, it will build CUDA support into all of the
recipes included in the Open-CE environment file that are enabled to do so.

---

## Building with CUDA

### CUDA Build Type

Both the [`open-ce build env`](README.open_ce_build.md#open-ce-build-env.md) and [`open-ce build feedstock`](README.build_feedstock-sub-command) scripts
support the `--build_types=cuda` command line argument. This is required when CUDA support is desired in the build.
This argument sets a parameter in the build environment which can then be referenced in the
collected feedstocks and Open-CE environment files using a tag. For example,
a PyTorch Open-CE envionment file could use the tag as:

```shell
{% if build_type == 'cuda' %}
imported_envs:
  - tensorrt-env.yaml
{% endif %}

packages:
  - feedstock : pytorch
  - feedstock : numactl
{% if build_type == 'cuda' %}
  - feedstock : nccl
  - feedstock : magma
  - feedstock : cudnn
{% endif %}
  - feedstock : torchtext
  - feedstock : onnx
  - feedstock : av
  - feedstock : torchvision
```

The tag can also be used per line shown in this example for the xgboost [meta.yaml](https://github.com/open-ce/xgboost-feedstock/blob/master/recipe/meta.yaml)

```shell
    - cudatoolkit {{ cudatoolkit }}            #[build_type == 'cuda']
    - nccl {{ nccl }}                          #[build_type == 'cuda']
```

### Specifying CUDA Version

The `--cuda_versions` flag can be passed to `open-ce` to specify which version of CUDA to build conda packages for.

```shell
open-ce build env --build_types cuda --cuda_versions 11.0 envs/opence-env.yaml
```

---

## CUDA Runtime support

A system-level CUDA installation is not required at runtime. Once packages are built, CUDA is pulled
at the appropriate level from Anaconda's [Defaults channel](https://repo.anaconda.com/pkgs/).  Systems
with NVIDIA GPUs installed do still need the NVIDIA device driver installed. Drivers can be found on
NVIDIA's [Driver Downloads](https://www.nvidia.com/Download/index.aspx) website.

## NVIDIA cuDNN

The NVIDIA CUDA Deep Neural Network library (cuDNN) is a GPU-accelerated library of primitives for deep neural
networks. Both PyTorch and TensorFlow make use of cuDNN and it is require for those frameworks CUDA support.
Open-CE includes a build recipe for a cuDNN package and will automatically fetch the appropriate version
for which the package being built.

## NVIDIA TensorRT

NVIDIA TensorRT is an SDK for high-performance deep learning inference. It includes a deep learning inference
optimizer and runtime that delivers low latency and high-throughput for deep learning inference applications.
PyTorch, TensorFlow, and TensorFlow Serving include optional TensorRT support. Open-CE is unable to automatically
fetch TensorRT at build time. The appropriate version of TensorRT must be downloaded from NVIDIA's [TensorRT website](https://developer.nvidia.com/nvidia-tensorrt-download)
and saved in a directory called `local_files` adjacent to the `open-ce` repository. The version of TensorRT
must match the version of Open-CE.

| Open-CE version | TensorRT version | file type |
|-----------------|------------------|-----------|
| 1.0 (marmotini) | 7.0.0.11         |  tar.gz   |
| 1.1 (unnamed)   | 7.2.*            |  tar.gz   |

Note that the Open-CE recipe for TensorRT also includes some [open source samples and parsers](https://github.com/nvidia/tensorrt).
These are fetched automatically to match the version of TensorRT included in the version of Open-CE being used.

## NCCL

NCCL (pronounced "Nickel") is a stand-alone library of standard collective communication routines for NVIDIA GPUs,
implementing all-reduce, all-gather, reduce, broadcast, and reduce-scatter. Pytorch and TensorFlow
utilize NCCL when CUDA support is enabled. NCCL is now open source and fetched for build automatically.
