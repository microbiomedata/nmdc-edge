###############################################################################
# This is a Dockerfile you can use to build a container image that runs the   #
# NMDC EDGE Web App. Its design was influenced by the installation script     #
# at `installation/install.sh`.                                               #
###############################################################################

FROM node:16-alpine

# Add metadata to the Docker image.
# Reference: https://docs.docker.com/engine/reference/builder/#label
LABEL org.opencontainers.image.description="NMDC EDGE Web App (Node v16)"
LABEL org.opencontainers.image.source="https://github.com/microbiomedata/nmdc-edge"

# Create an environment variable that contains the web app version identifier.
#
# Note: Its value will come from the `--build-arg NMDC_EDGE_WEB_APP_VERSION={value}`
#       CLI option, if any, included in the `$ docker build` command.
#       Reference: https://docs.docker.com/reference/dockerfile/#arg
#
ARG NMDC_EDGE_WEB_APP_VERSION
ENV NMDC_EDGE_WEB_APP_VERSION="$NMDC_EDGE_WEB_APP_VERSION"

# Allow the developer to (optionally) customize the ID and name of the user by which PM2 will
# be launched; and the ID and name of the group to which that user will belong.
ARG USER_ID=60005
ARG GROUP_ID=60005
ARG USER_NAME=webuser
ARG GROUP_NAME=webuser

# Install programs upon which the web app or its build process(es) depend.
#
# Note: `apk` (Alpine Package Keeper) is the Alpine Linux equivalent of `apt`.
#       Docs: https://wiki.alpinelinux.org/wiki/Alpine_Package_Keeper
#
RUN apk update && apk add \
  zip

# Install the latest version of PM2 globally (https://github.com/Unitech/pm2).
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
WORKDIR /app
COPY ./data          /app/data
COPY ./installation  /app/installation
COPY ./webapp        /app/webapp
COPY ./nmdc-edge.jpg /app/nmdc-edge.jpg
COPY ./pm2.config.js /app/pm2.config.js
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
# Note: The `--legacy-peer-deps` option is here because some of the npm packages upon which the web app depends,
#       have conflicting dependencies with one another. The `--legacy-peer-deps` option causes npm to be more
#       lenient about stuff like that. Reference: https://stackoverflow.com/a/66620869
#
RUN cd webapp/client && npm ci --legacy-peer-deps
#
# Build the web app client (i.e. React app).
#
RUN cd webapp/client && npm run build
#
# Build the web app server (e.g. Express app).
#
RUN cd webapp/server && npm ci

# Create a group having the specified GID (Group ID) and group name, and create
# a user (in that group) having the specified UID (User ID) and user name.
# Reference: https://gist.github.com/utkuozdemir/3380c32dfee472d35b9c3e39bc72ff01
RUN addgroup -g $GROUP_ID $GROUP_NAME && \
    adduser --shell /sbin/nologin --disabled-password \
            --ingroup $GROUP_NAME --uid $USER_ID $USER_NAME

# Switch to that user before running the subsequent commands.
# Reference: https://docs.docker.com/reference/dockerfile/#user
USER $USER_NAME

# Run PM2 in the foreground. PM2 will serve the NMDC EDGE web app.
#
# Note: We use `pm2-runtime` (instead of `pm2` directly), as shown in the PM2
#       documentation about using PM2 inside containers.
#       Docs: https://pm2.keymetrics.io/docs/usage/docker-pm2-nodejs/
#
CMD ["pm2-runtime", "start", "pm2.config.js"]
