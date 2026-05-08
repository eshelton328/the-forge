# openEMS + gerber2ems — electromagnetic (FDTD) simulation from Gerbers.
# Intended for EMI-adjacent / SI regression smoke in CI; not chamber certification.
# Upstream references:
#   https://github.com/antmicro/gerber2ems/blob/main/Dockerfile
#   https://github.com/thliebig/openEMS-Project/
# oci image index (multi-arch debian:trixie as of Docker Hub digest below)
FROM debian:trixie@sha256:35b8ff74ead4880f22090b617372daff0ccae742eb5674455d542bef71ef1999

SHELL ["/bin/bash", "-lc"]

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential cmake git \
    libhdf5-dev libvtk9-dev libboost-all-dev libcgal-dev libtinyxml-dev \
    qtbase5-dev libvtk9-qt-dev \
    python3 python3-venv cython3 python3-pip \
    gerbv \
 && rm -rf /var/lib/apt/lists/*

COPY emi-pinned-versions.env /tmp/emi-pinned-versions.env

RUN useradd -m -s /bin/bash docker

USER docker
WORKDIR /home/docker

ENV HOME=/home/docker \
    PATH="/home/docker/.local/bin:/home/docker/opt/openEMS/venv/bin:${PATH}"

RUN set -a \
 && source /tmp/emi-pinned-versions.env \
 && set +a \
 && test -n "${OPENEMS_COMMIT}" \
 && test -n "${GERBER2EMS_SHA}" \
 && git clone https://github.com/thliebig/openEMS-Project.git openEMS-Project \
 && cd openEMS-Project \
 && git checkout "${OPENEMS_COMMIT}" \
 && git submodule update --init --recursive \
 && ./update_openEMS.sh /home/docker/opt/openEMS --python \
 && cd .. \
 && git clone https://github.com/antmicro/gerber2ems.git gerber2ems \
 && cd gerber2ems \
 && git checkout "${GERBER2EMS_SHA}" \
 && source /home/docker/opt/openEMS/venv/bin/activate \
 && pip install --no-cache-dir . \
 && mkdir -p /home/docker/.local/bin \
 && ln -sf /home/docker/opt/openEMS/venv/bin/gerber2ems /home/docker/.local/bin/ \
 && ln -sf /home/docker/opt/openEMS/venv/bin/ems2paraview /home/docker/.local/bin/ \
 && ln -sf /home/docker/opt/openEMS/venv/bin/ems2png /home/docker/.local/bin/

USER root

RUN chmod 755 /home/docker \
 && chmod -R a+rX /home/docker

USER docker

ENTRYPOINT ["gerber2ems"]
