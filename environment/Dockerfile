# hash:sha256:cd149449132f220287b12ec7b3d77e926168bbb3816fe211fa6779618896905e
ARG REGISTRY_HOST
FROM $REGISTRY_HOST/codeocean/python:3.11.13

ARG DEBIAN_FRONTEND=noninteractive
ARG GIT_ASKPASS
COPY git-ask-pass /

RUN pip install -U --no-cache-dir \
    codeocean==0.14.0
