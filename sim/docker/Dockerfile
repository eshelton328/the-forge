# Unified KiCad CLI + ngspice + Python sim toolchain.
# The FROM digest MUST match KICAD_IMAGE in:
#   - .github/workflows/{pr-checks,spice-checks,update-readmes}.yml
#   - Makefile (KICAD_IMAGE)
FROM kicad/kicad:10.0@sha256:feb600e931ca7ad8ae684566131edbea32218cb90ab54bb2ea0944cee257eea6

# Debian package pin for ngspice (verify with: docker run --rm --user root <KICAD_IMAGE> apt-cache policy ngspice)
ARG NGSPICE_DEB_VERSION=44.2+ds-1

USER root

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
       ngspice=${NGSPICE_DEB_VERSION} \
       python3-venv \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Build context is the repository root (see sim/docker/README.md).
COPY requirements.txt /tmp/the-forge-requirements.txt
RUN python3 -m venv /opt/the-forge-sim \
  && /opt/the-forge-sim/bin/pip install --disable-pip-version-check --no-cache-dir -r /tmp/the-forge-requirements.txt \
  && rm /tmp/the-forge-requirements.txt \
  && chmod -R a+rX /opt/the-forge-sim

ENV PATH="/opt/the-forge-sim/bin:${PATH}"

# Match upstream image default for bare `docker run` without `--user` (CI passes `--user "$(id -u):$(id -g)"`).
USER kicad
