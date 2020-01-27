
FROM python:3.7-alpine

LABEL Name=django-sspanel

COPY requirements.txt /tmp/requirements.txt

RUN set -e; \
    apk update \
    && apk add --virtual .build-deps libffi-dev build-base \
    # TODO workaround start
    && apk add mariadb-dev \
    # TODO workaround end
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && apk del .build-deps