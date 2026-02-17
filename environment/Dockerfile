# hash:sha256:ff7957216084d9e74a9e84c85b51acc05a81cb015b2df39d6350f58309d1f580
ARG REGISTRY_HOST
FROM $REGISTRY_HOST/codeocean/mambaforge3:22.11.1-4-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG GIT_ASKPASS
COPY git-ask-pass /

RUN pip install -U --no-cache-dir \
    codeocean==0.14.0
