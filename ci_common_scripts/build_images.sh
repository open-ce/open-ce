#!/bin/bash
# *****************************************************************
#
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2020. All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
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


