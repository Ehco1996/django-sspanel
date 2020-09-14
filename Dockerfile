FROM python:3.8-alpine as base

LABEL Name=django-sspanel

COPY requirements.txt /tmp/requirements.txt

RUN apk add --update --no-cache mariadb-connector-c-dev tzdata \
	&& apk add --no-cache --virtual .build-deps mariadb-dev gcc musl-dev libffi-dev make \
	# TODO workaround start
	&& pip install --no-cache-dir -r /tmp/requirements.txt \
	# TODO workaround end
	&& apk del .build-deps \
	&& cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
	&& echo "Asia/Shanghai" > /etc/timezone
