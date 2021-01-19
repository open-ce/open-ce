#!/bin/bash
# *****************************************************************
# (C) Copyright IBM Corp. 2020, 2021. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# *****************************************************************
set -e

echo "DEBUG: in docker_common_run_build_pkg.sh, user is:"
echo `whoami`




#Determine if we're building POWER or x86 images, and do the Ubi swizzle
ARCH=`uname -m`
if [ ${ARCH} = "ppc64le" ] ; then
    UBI_ARCH=ppc64le
else
    UBI_ARCH=x86_64
fi

#Get access to current directory of this scripts
CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ${CUR_DIR}/imageconfig
build_layer=${BASE_LAYER}-${OPENCE_RELEASE}-${DISTRO_VERSION}-${UBI_ARCH}

# checking for docker image on the host
if [[ "$(docker images -q $REPO_NAME:$build_layer 2> /dev/null)" == "" ]]; then
        ./open-ce/ci_common_scripts/build_images.sh ubi ${DISTRO_VERSION} $UBI_ARCH
	
fi


echo "checking for docker"
docker images

# Some env vars used in the docker container to be run later.
git_root=$(pwd)
VOL_OPTS="rw,z"
VOL_EXTRA_OPTS=":z"

EXTERNAL_GIT_ROOT="/var/local/opence"
OUTPUT_FOLDER="/home/builder/condabuild"
CONTAINER_NAME="conda_travis_build_$PACKAGE_NAME"

# Ensure existence of ccache directory to potentially speed up builds
CCACHE_DIR=/tmp/${PACKAGE_NAME}-ccache
mkdir -p $CCACHE_DIR

# Run command inside docker.
docker run --pid=host \
  -e CCACHE_DIR=$CCACHE_DIR \
  -e PACKAGE_NAME=$PACKAGE_NAME \
  -e EXTERNAL_GIT_ROOT=${EXTERNAL_GIT_ROOT} \
  -e GIT_PERS_TOKEN_PSW=${GITHUB_TOKEN}\
  -e GIT_PERS_TOKEN_USR=${GITHUB_USER}\
  -e OUTPUT_FOLDER=${OUTPUT_FOLDER} \
  -v "$git_root:${EXTERNAL_GIT_ROOT}:$VOL_OPTS" \
  -v $CCACHE_DIR:$CCACHE_DIR$VOL_EXTRA_OPTS \
  --name=$CONTAINER_NAME \
  ${REPO_NAME}:${build_layer} \
  bash -i "${EXTERNAL_GIT_ROOT}/$DOCKER_RUN_SCRIPT" 
 
if [ "$FAILED" != "" ]
then
  exit 1
fi 

# remove the container, possibly killing it first
docker rm -f $CONTAINER_NAME || true



