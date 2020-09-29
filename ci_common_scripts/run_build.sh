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
set -ex

pwd
ls -lrt
cd ${EXTERNAL_GIT_ROOT}/${PACKAGE_NAME}
python ${EXTERNAL_GIT_ROOT}/open-ce/open-ce/build_feedstock.py --output_folder=${OUTPUT_FOLDER}

echo "Verifying built packages"
ls -ltrR ${OUTPUT_FOLDER}
