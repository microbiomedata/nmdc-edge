# This is a Dockerfile you can use to build a Docker image that runs the
# NMDC EDGE web app and a MongoDB server, all within a single Docker container.
# Its design was influenced by the installation script at `installation/install.sh`.
#
# Usage:
# 1. Build with:     $ docker build -t nmdc-edge-web-app:latest -f webapp.Dockerfile .
# 2. Then, run with: $ docker run --rm -p 8000:80 nmdc-edge-web-app

FROM node:18-alpine

# Declare arguments (and specify their default values) for use within this Dockerfile.
# Note: Their values can be overriden via `$ docker build --build-arg <varname>=<value>`.
# Reference: https://docs.docker.com/engine/reference/builder/#arg
ARG WEB_SERVER_PORT_ON_DOCKER_HOST=8000

# Install programs upon which the web app or its build process(es) depend.
#
# Note: `apk` (Alpine Package Keeper) is the Alpine Linux equivalent of `apt`.
#       Docs: https://wiki.alpinelinux.org/wiki/Alpine_Package_Keeper
#
# Note: We add repositories from an older Alpine version because MongoDB isn't
#       available in the repositories of current Alpine versions. References:
#       - https://www.mongodb.com/community/forums/t/why-is-there-no-mongodb-alpine-image/199185
#       - https://unix.stackexchange.com/a/569565
#
#       Also, we install `openrc` so we can run `rc-update`.
#
RUN echo 'http://dl-cdn.alpinelinux.org/alpine/v3.9/main'      >> /etc/apk/repositories
RUN echo 'http://dl-cdn.alpinelinux.org/alpine/v3.9/community' >> /etc/apk/repositories
RUN apk update && apk add \
  zip \
  openrc \
  mongodb \
  mongodb-tools

# Create a folder that the MongoDB server will look for.
RUN mkdir -p /data/db

# Configure the system to start the MongoDB server whenever the system boots.
# Reference: https://wiki.alpinelinux.org/wiki/OpenRC
RUN rc-update add mongodb default

# Update npm, itself, to the latest version.
RUN npm install -g npm@latest

# Install the latest version of PM2 (https://github.com/Unitech/pm2).
RUN npm install -g pm2@latest

# Set up both the web app client and the web app server.
#
# Note: I am intentionally omitting this Dockerfile from this COPY operation because I don't
#       want to trigger lots of cache misses while I'm still developing this Dockerfile.
#
# Note: By copying so much of the file tree this early in the Docker image build process,
#       we may be missing out on some Docker image layer caching opportunities.
#
RUN mkdir /app
COPY ./data          /app/data
COPY ./installation  /app/installation
COPY ./webapp        /app/webapp
COPY ./nmdc-edge.jpg /app/nmdc-edge.jpg
#
# Generate configuration files (like `installation/install.sh` does).
# Note: We use the `client-env-dev` file so the client uses HTTP (not HTTPS) to access the server.
#
WORKDIR /app
RUN cp installation/client-env-dev  webapp/client/.env
RUN cp installation/server-env-prod webapp/server/.env
RUN cp installation/server_pm2.tmpl server_pm2.json
RUN echo -e "web_server_domain=localhost\nweb_server_port=80"         > host.env
RUN sed -i -e 's/<WEB_SERVER_DOMAIN>/localhost/g'                       webapp/client/.env && \
    sed -i -e 's/<WEB_SERVER_PORT>/${WEB_SERVER_PORT_ON_DOCKER_HOST}/g' webapp/client/.env && \
    sed -i -e 's/<WEB_SERVER_DOMAIN>/localhost/g'                       webapp/server/.env && \
    sed -i -e 's/<WEB_SERVER_PORT>/80/g'                                webapp/server/.env && \
    sed -i -e 's/<APP_HOME>/\/app/g'                                    webapp/server/.env && \
    sed -i -e 's/<IO_HOME>/\/app\/io/g'                                 webapp/server/.env && \
    sed -i -e 's/<APP_HOME>/\/app/g'                                    server_pm2.json
#
# Generate empty folders (like `installation/install.sh` does).
# Note: `mkdir -p` automatically creates any necessary intermediate folders.
#
RUN mkdir -p io
RUN cd io && mkdir -p upload/files upload/tmp log projects public db sra
#
# Generate an `imports.zip` file for each group of WDL files (like `installation/install.sh` does).
#
RUN cd /app/data/workflow/WDL/metaG         && zip -r imports.zip *.wdl
RUN cd /app/data/workflow/WDL/metaP         && zip -r imports.zip *.wdl
RUN cd /app/data/workflow/WDL/metaT         && zip -r imports.zip *.wdl
RUN cd /app/data/workflow/WDL/organicMatter && zip -r imports.zip *.wdl
RUN cd /app/data/workflow/WDL/virusPlasmids && zip -r imports.zip *.wdl
RUN cd /app/data/workflow/WDL/sra           && zip -r imports.zip *.wdl
#
# Install the npm packages upon which the web app client depends.
#
# TODO: Once the project offers a `package-lock.json` file, run `npm ci` here instead
#       of `npm install` (see https://github.com/microbiomedata/nmdc-edge/issues/14).
#
# Note: We use the `--legacy-peer-deps` option (as shown in `installation/install.sh`)
#       to work around https://github.com/microbiomedata/nmdc-edge/issues/13.
#
RUN cd webapp/client && npm install --legacy-peer-deps
#
# Build the web app client (i.e. React app).
#
# Note: Prefix the command with `NODE_OPTIONS=--openssl-legacy-provider`
#       to work around https://github.com/microbiomedata/nmdc-edge/issues/15.
#
RUN cd webapp/client && NODE_OPTIONS=--openssl-legacy-provider npm run build
#
# Build the web app server (e.g. Express app).
#
RUN cd webapp/server && npm ci

# Run the MongoDB server in the background, and run PM2 in the foreground.
# PM2 will serve the web app server (i.e. Express app).
#
# Note: We use `pm2-runtime` (instead of `pm2` directly), as shown in the PM2
#       documentation about using PM2 inside containers.
#       Docs: https://pm2.keymetrics.io/docs/usage/docker-pm2-nodejs/
#
EXPOSE 80
CMD ["sh", "-c", "mongod --fork --syslog && pm2-runtime start server_pm2.json"]
