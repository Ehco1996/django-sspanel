
FROM python:3.6-alpine

LABEL Name=django-sspanel Version=0.0.3

COPY requirements.txt /tmp/requirements.txt

RUN apk update && apk add --no-cache gcc linux-headers \
    musl-dev python3-dev mariadb-dev jpeg-dev  && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    apk del gcc linux-headers \
    musl-dev python-dev jpeg-dev  && \
    rm -Rf ~/.cache

# # 如果是第一次运行需要手动exec进去执行如下命令
# # python3 manage.py collectstatic --no-input && \
# # python3 manage.py makemigrations && \
# # python3 manage.py migrate --run-syncdb && \
