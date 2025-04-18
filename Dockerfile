FROM python:3.11

RUN \
    pip install poetry && \
    poetry config virtualenvs.create false

ADD pyproject.toml poetry.lock README.md /src/
WORKDIR /src
RUN \
    poetry install --only=main --no-root

RUN pip install semver

ADD . /src

