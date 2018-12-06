
FROM python:3.6-slim

LABEL Name=django-sspanel Version=0.0.2

COPY . /src/django-sspanel

WORKDIR /src/django-sspanel

RUN apt-get update && \
    apt-get install  -y --no-install-recommends \
        build-essential \
        python3-dev \
        default-libmysqlclient-dev && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

# 如果是第一次运行需要手动exec进去执行如下命令
# python3 manage.py collectstatic --no-input && \
# python3 manage.py makemigrations && \
# python3 manage.py migrate --run-syncdb && \

# server
CMD uwsgi uwsgi.ini