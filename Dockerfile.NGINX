FROM ehco1996/django-sspanel:runtime as runtime

ENV DJANGO_ENV=ci

WORKDIR /mnt/src/django-sspanel/

COPY . /mnt/src/django-sspanel/

RUN python manage.py collectstatic --noinput

FROM k8s.gcr.io/nginx:1.7.9

WORKDIR /mnt/src/django-sspanel/

COPY --from=runtime /mnt/src/django-sspanel .

RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
	&& echo "Asia/Shanghai" > /etc/timezone
