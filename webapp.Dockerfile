# This is a Dockerfile you can use to build a container image that runs the NMDC EDGE Web App.
# Its design was influenced by the installation script at `installation/install.sh`.
#
# =====
# USAGE
# -----
#
# Here's how you can build a container image based upon this Dockerfile; and publish it to GitHub Container Registry.
#
# =============
# Prerequisites
# -------------
#
# - Determine the ORCiD Client ID you want the resulting container image to use. You can get it by logging into
#   the ORCiD website and visiting the "Developer tools" page there. You will use it in the procedure below.
#
# =========
# Procedure
# ---------
#
# 1. Build a container image (do one of the following, depending upon situation):
#    - Build an image on your Mac for local development:
#      ```
#      $ docker build -f webapp.Dockerfile \
#          --build-arg ORCID_CLIENT_ID='__REPLACE_ME__' \
#          --build-arg API_HOST='localhost' \
#          --build-arg API_PORT='8000' \
#          -t nmdc-edge-web-app:dev .
#      ```
#    - Build an image that will run on a GCP VM (amd64 architecture):
#      ```
#      $ docker buildx build --platform linux/amd64 -f webapp.Dockerfile \
#          --build-arg ORCID_CLIENT_ID='__REPLACE_ME__' \
#          --build-arg API_HOST='edge-dev.microbiomedata.org' \
#          --build-arg API_PORT='80' \
#          -t nmdc-edge-web-app:some-tag .
#      ```
# 2. (Optional) Run a container based upon that container image:
#      ```
#      $ docker run --rm -p 8000:8000 nmdc-edge-web-app:dev
#      ```
# 3. Tag the container image for publishing to the GitHub Container Registry.
#    a. Get the ID of the container image.
#       ```
#       $ docker images
#       ```
#       - That will display the IDs of all container images. Identify the ID of the image you want to publish.
#    b. Tag the container image with the GHCR prefix.
#       ```
#       $ docker tag __IMAGE_ID__ ghcr.io/microbiomedata/nmdc-edge-web-app:some-tag
#       ```
#       - Replace `__IMAGE_ID__` above with the image ID.
# 4. Publish the tagged container image to GitHub Container Registry (where it will be publicly accessible).
#    ```
#    $ docker push ghcr.io/microbiomedata/nmdc-edge-web-app:some-tag
#    ```
#    - That will upload the image (layer by layer) to GitHub Container Registry. It will then be listed at
#      https://github.com/orgs/microbiomedata/packages/container/package/nmdc-edge-web-app
#
# ==========
# References
# ----------
#
# - Building a container image and pushing it to GitHub Container Registry (GHCR):
#   https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry
#
# ----------------------------------------------------------------------------------------------------------------------

FROM node:18-alpine

# Add metadata to the Docker image.
# Reference: https://docs.docker.com/engine/reference/builder/#label
LABEL org.opencontainers.image.description="NMDC EDGE Web App"

# Declare arguments (and specify their default values) for use within this Dockerfile.
# Note: Their values can be overriden via `$ docker build --build-arg <varname>=<value>`.
# Reference: https://docs.docker.com/engine/reference/builder/#arg
ARG API_HOST=edge-dev.microbiomedata.org
ARG API_PORT=80
ARG ORCID_CLIENT_ID

# Install programs upon which the web app or its build process(es) depend.
#
# Note: `apk` (Alpine Package Keeper) is the Alpine Linux equivalent of `apt`.
#       Docs: https://wiki.alpinelinux.org/wiki/Alpine_Package_Keeper
#
RUN apk update && apk add \
  zip

# Update npm, itself, to the latest version.
RUN npm install -g npm@latest

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
COPY ./data          /app/data
COPY ./installation  /app/installation
COPY ./webapp        /app/webapp
COPY ./nmdc-edge.jpg /app/nmdc-edge.jpg
#
# Generate secrets (each one is a 20-character hexadecimal string).
#
RUN node -e 'console.log(require("crypto").randomBytes(20).toString("hex"))' > /app/jwt.secret.txt
RUN node -e 'console.log(require("crypto").randomBytes(20).toString("hex"))' > /app/oauth.secret.txt
RUN node -e 'console.log(require("crypto").randomBytes(20).toString("hex"))' > /app/sendmail.secret.txt
#
# Generate configuration files (like `installation/install.sh` does).
# Note: We use the `client-env-dev` file so the client uses HTTP (not HTTPS) to access the server.
#
WORKDIR /app
RUN cp installation/client-env-dev  webapp/client/.env
RUN cp installation/server-env-prod webapp/server/.env
RUN cp installation/server_pm2.tmpl server_pm2.json
RUN echo -e "web_server_domain=${API_HOST}\nweb_server_port=${API_PORT}" > host.env
RUN sed -i -e "s/<WEB_SERVER_DOMAIN>/${API_HOST}/g"                     webapp/client/.env && \
    sed -i -e "s/<WEB_SERVER_PORT>/${API_PORT}/g"                       webapp/client/.env && \
    sed -i -e "s/<WEB_SERVER_DOMAIN>/${API_HOST}/g"                     webapp/server/.env && \
    sed -i -e "s/<WEB_SERVER_PORT>/${API_PORT}/g"                       webapp/server/.env && \
    sed -i -e 's/<APP_HOME>/\/app/g'                                    webapp/server/.env && \
    sed -i -e 's/<IO_HOME>/\/app\/io/g'                                 webapp/server/.env && \
    sed -i -e "s/<JWT_KEY>/`cat /app/jwt.secret.txt`/g"                 webapp/server/.env && \
    sed -i -e "s/<OAUTH_SECRET>/`cat /app/oauth.secret.txt`/g"          webapp/server/.env && \
    sed -i -e "s/<SENDMAIL_KEY>/`cat /app/sendmail.secret.txt`/g"       webapp/server/.env && \
    sed -i -e 's/<APP_HOME>/\/app/g'                                    server_pm2.json
#
# Further edit configuration files (beyond what `installation/install.sh` does).
# Note: I substitute `ORCID_CLIENT_ID` here so developers don't have to edit `installation/client-env-dev`.
#
RUN sed -i -e "s/<your orcid client id>/${ORCID_CLIENT_ID}/g"           webapp/client/.env
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
RUN cd webapp/client && npm ci
#
# Build the web app client (i.e. React app).
#
# Note: Prefix the `npm run build` command with `NODE_OPTIONS=--openssl-legacy-provider`
#       in order to work around https://github.com/microbiomedata/nmdc-edge/issues/15.
#
RUN cd webapp/client && NODE_OPTIONS=--openssl-legacy-provider npm run build
#
# Build the web app server (e.g. Express app).
#
RUN cd webapp/server && npm ci

# Run PM2 in the foreground. PM2 will serve the NMDC EDGE web app.
#
# Note: We use `pm2-runtime` (instead of `pm2` directly), as shown in the PM2
#       documentation about using PM2 inside containers.
#       Docs: https://pm2.keymetrics.io/docs/usage/docker-pm2-nodejs/
#
EXPOSE ${API_PORT}
CMD ["pm2-runtime", "start", "server_pm2.json"]
