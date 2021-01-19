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


build_base_layer(){
    build_layer=${BASE_LAYER}-${OPENCE_RELEASE}-${DISTRO_VERSION}-${UBI_ARCH}
    echo "* Building Base Image as ${REPO_NAME}:${build_layer}"
    
    ${DOCKER_BIN} build  $NO_CACHE \
            -f ${ROOT_FOLDER}/Dockerfile \
            -t ${REPO_NAME}:${build_layer} . ; echo $? > status_base &
}

if [ $# -ne 3 ]; then
    echo "Please pass in Linux Distro, Version,image name, repo name as parameters.  (example: ubi 7.7 )"
    exit 1
fi

DISTRO_VERSION=$1$2
DISTRO_DIR=$1/$2
UBI_ARCH=$3


#Get access to current directory of this scripts
CUR_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source ${CUR_DIR}/imageconfig
build_base_layer ${UBI_ARCH}


