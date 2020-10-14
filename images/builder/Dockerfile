FROM registry.access.redhat.com/ubi7/ubi

ENV CONDA_HOME=${CONDA_HOME:-/opt/conda}
ENV PATH=$CONDA_HOME/bin:$PATH

ENV CICD_GROUP=cicd
ARG GROUP_ID=1500
ENV BUILD_USER=builder
ARG BUILD_ID=1084
ENV IBM_POWERAI_LICENSE_ACCEPT=yes

RUN export ARCH="$(uname -m)" && \
    yum repolist && yum install -y \
    sudo \
    bzip2 \
    git \
    patch && \
    # Create CICD Group
    groupadd --gid ${GROUP_ID} ${CICD_GROUP} && \
    # Adduser Builder
    useradd -b /home --create-home --gid ${GROUP_ID} --groups wheel \
    --uid ${BUILD_ID} --comment "User for Building" ${BUILD_USER} && \
    echo "${BUILD_USER}    ALL=NOPASSWD: ALL" > /etc/sudoers.d/user-${BUILD_USER} && \
    curl -o /tmp/anaconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-${ARCH}.sh && \
    chmod +x /tmp/anaconda.sh && \
    /bin/bash /tmp/anaconda.sh -f -b -p /opt/conda && \
    rm -f /tmp/anaconda.sh && \
    $CONDA_HOME/bin/conda install -y conda-build && \
    chown -R ${BUILD_USER}:${CICD_GROUP} ${CONDA_HOME}

USER ${BUILD_USER}
RUN export PATH="${PATH}" && \
    echo "PATH="${PATH}"" >> ${HOME}/.profile && \
    $CONDA_HOME/bin/conda config --system --add envs_dirs $CONDA_HOME/envs && \
    $CONDA_HOME/bin/conda config --system --add pkgs_dirs $CONDA_HOME/pkgs && \
    $CONDA_HOME/bin/conda config --system --set always_yes true && \
    $CONDA_HOME/bin/conda config --system --set auto_update_conda false && \
    $CONDA_HOME/bin/conda config --system --set notify_outdated_conda false && \
    $CONDA_HOME/bin/conda --version && \
    sudo rm -f /run/nologin && \
    yes | ssh-keygen -f $HOME/.ssh/id_rsa -q -t rsa -N '' && cp $HOME/.ssh/id_rsa.pub $HOME/.ssh/authorized_keys && \
    echo ". $CONDA_HOME/etc/profile.d/conda.sh" >> ${HOME}/.bashrc && \
    echo "conda activate base" >> ${HOME}/.bashrc
    

    
    
