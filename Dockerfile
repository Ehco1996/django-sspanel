FROM python:3.8-alpine as base

LABEL Name=django-sspanel

ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

WORKDIR /tmp
COPY pyproject.toml poetry.lock /tmp/


RUN apk add --update --no-cache mariadb-connector-c-dev tzdata \
	&& apk add --no-cache --virtual .build-deps mariadb-dev gcc musl-dev libffi-dev make \
	# TODO workaround start
	&& pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install  --no-dev --no-interaction --no-ansi \
	# TODO workaround end
	&& apk del .build-deps \
	&& cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
	&& echo "Asia/Shanghai" > /etc/timezone
