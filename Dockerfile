FROM python:3.9

ADD requirements.txt /tmp/requirements.txt

RUN pip install -r /tmp/requirements.txt


ADD . /src

WORKDIR /src
