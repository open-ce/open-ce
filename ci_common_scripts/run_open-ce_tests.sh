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

# Install required dependencies
conda install -y conda-build pytest pytest-cov pytest-mock

# Need to move the open-ce repo to a directory with write permissions
if [ -n "${EXTERNAL_GIT_ROOT+x}" ]; then
    cp -r ${EXTERNAL_GIT_ROOT}/open-ce ~
    cd ~/open-ce
fi

# Run the tests
pytest tests/
