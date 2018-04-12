
# Python support can be specified down to the minor or micro version
# (e.g. 3.6 or 3.6.3).
# OS Support also exists for jessie & stretch (slim and full).
# See https://hub.docker.com/r/library/python/ for all supported Python
# tags from Docker Hub.
FROM python:3.6

# If you prefer miniconda:
#FROM continuumio/miniconda3

LABEL Name=sspanel Version=0.0.1
EXPOSE 8080

RUN mkdir -p /src/django-sspanel
ADD . /src/django-sspanel
WORKDIR /src/django-sspanel

# Using pip:
RUN python3 -m pip install -r requirements.txt

