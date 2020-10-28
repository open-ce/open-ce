#FROM nvidia/cuda-ppc64le:10.2-runtime-ubi7
FROM registry.access.redhat.com/ubi7/ubi:7.6

ENV CONDA_HOME=${CONDA_HOME:-/opt/conda}
ENV PATH=$CONDA_HOME/bin:$PATH

ENV CICD_GROUP=cicd
ARG GROUP_ID=1500
ARG USER_ID=1084

ARG OPENCE_USER
ARG LOCAL_CONDA_CHANNEL
ARG CONDA_ENV_FILE
ARG TARGET_DIR

# Remove preinclude system compilers
#RUN rpm -e --nodeps --verbose gcc gcc-c++

# Install basic requirements.
RUN export ARCH="$(uname -m)" && \
    yum repolist && yum install -y \
    sudo openssh && \
    # Create CICD Group
    groupadd --non-unique --gid ${GROUP_ID} ${CICD_GROUP} && \
    # Adduser Builder
    adduser -b /home/ --non-unique --create-home --gid ${GROUP_ID} --groups wheel \
    --uid ${USER_ID} ${OPENCE_USER} && \
    echo "${OPENCE_USER}    ALL=NOPASSWD: ALL" > /etc/sudoers.d/user-${OPENCE_USER} && \
    curl -o /tmp/anaconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-${ARCH}.sh && \
    chmod +x /tmp/anaconda.sh && \
    /bin/bash /tmp/anaconda.sh -f -b -p /opt/conda && \
    rm -f /tmp/anaconda.sh && \
    $CONDA_HOME/bin/conda install -y conda-build && \
    chown -R ${OPENCE_USER}:${CICD_GROUP} ${CONDA_HOME}

USER ${OPENCE_USER}
RUN export PATH="${PATH}" && \
    echo "PATH="${PATH}"" >> ${HOME}/.profile && \
    $CONDA_HOME/bin/conda config --system --add envs_dirs $CONDA_HOME/envs && \
    $CONDA_HOME/bin/conda config --system --add pkgs_dirs $CONDA_HOME/pkgs && \
    $CONDA_HOME/bin/conda config --system --set always_yes true && \
    $CONDA_HOME/bin/conda config --system --set auto_update_conda false && \
    $CONDA_HOME/bin/conda config --system --set notify_outdated_conda false && \
    mkdir -p $CONDA_HOME/conda-bld && \
    mkdir -p $HOME/.cache && \
    $CONDA_HOME/bin/conda --version && \
    sudo rm -f /run/nologin && \
    yes | ssh-keygen -f $HOME/.ssh/id_rsa -q -t rsa -N '' && cp $HOME/.ssh/id_rsa.pub $HOME/.ssh/authorized_keys && \
    echo ". $CONDA_HOME/etc/profile.d/conda.sh" >> ${HOME}/.bashrc && \
    echo "conda activate base" >> ${HOME}/.bashrc

RUN mkdir -p ${TARGET_DIR}

COPY ${LOCAL_CONDA_CHANNEL} ${TARGET_DIR}

RUN sudo chown -R ${OPENCE_USER}:${CICD_GROUP} ${TARGET_DIR}

RUN $CONDA_HOME/bin/conda env create -f ${TARGET_DIR}/${CONDA_ENV_FILE}

