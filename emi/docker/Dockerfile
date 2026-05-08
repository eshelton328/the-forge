# openEMS + gerber2ems — electromagnetic (FDTD) simulation from Gerbers.
# Intended for EMI-adjacent / SI regression smoke in CI; not chamber certification.
# Upstream references:
#   https://github.com/antmicro/gerber2ems/blob/main/Dockerfile
#   https://github.com/thliebig/openEMS-Project/
FROM debian:trixie

SHELL ["/bin/bash", "-lc"]

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential cmake git \
    libhdf5-dev libvtk9-dev libboost-all-dev libcgal-dev libtinyxml-dev \
    qtbase5-dev libvtk9-qt-dev \
    python3 python3-venv cython3 python3-pip \
    gerbv \
 && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash docker \
 && echo "docker:docker" | chpasswd

USER docker
WORKDIR /home/docker

ENV HOME=/home/docker \
    PATH="/home/docker/.local/bin:/home/docker/opt/openEMS/venv/bin:${PATH}"

# Pinned openEMS commit recommended by gerber2ems documentation.
ARG OPENEMS_COMMIT=a30587728affa4f8451e13819981899bd8ab6b64
RUN git clone https://github.com/thliebig/openEMS-Project.git openEMS-Project \
 && cd openEMS-Project \
 && git checkout "${OPENEMS_COMMIT}" \
 && git submodule update --init --recursive \
 && ./update_openEMS.sh /home/docker/opt/openEMS --python

# Pinned gerber2ems revision (keep in sync with scripts/ci/run-emi-fixture.sh default).
ARG GERBER2EMS_SHA=9eaf3033f8adb0b468045f7177523162b388b020
RUN git clone https://github.com/antmicro/gerber2ems.git gerber2ems \
 && cd gerber2ems \
 && git checkout "${GERBER2EMS_SHA}" \
 && source /home/docker/opt/openEMS/venv/bin/activate \
 && pip install --no-cache-dir . \
 && mkdir -p /home/docker/.local/bin \
 && ln -sf /home/docker/opt/openEMS/venv/bin/gerber2ems /home/docker/.local/bin/ \
 && ln -sf /home/docker/opt/openEMS/venv/bin/ems2paraview /home/docker/.local/bin/ \
 && ln -sf /home/docker/opt/openEMS/venv/bin/ems2png /home/docker/.local/bin/

ENTRYPOINT ["gerber2ems"]
