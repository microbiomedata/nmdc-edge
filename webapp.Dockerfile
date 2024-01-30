# This is a Dockerfile you can use to build a container image that runs the NMDC EDGE Web App.
# Its design was influenced by the installation script at `installation/install.sh`.
#
# =====
# USAGE
# -----
#
# Here's how you can build a container image based upon this Dockerfile; and publish it to GitHub Container Registry.
#
# =========
# Procedure
# ---------
#
# 1. Build a container image (do one of the following, depending upon your situation):
#    - If the computer you're using to build the image, and the computer on which containers based upon the image will
#      run, have the same CPU architecture, then you can use this command to build the image:
#      ```
#      $ docker build -f webapp.Dockerfile -t nmdc-edge-web-app:some-tag .
#      ```
#    - If the computer you're using to build the image has the arm64 CPU architecture (e.g. a MacBook Pro M1),
#      and the computer on which containers based upon the image will run have the AMD64 CPU architecture
#      (e.g. Intel-based systems), you can use this command to build the image:
#      ```
#      $ docker buildx build --platform linux/amd64 -f webapp.Dockerfile -t nmdc-edge-web-app:some-tag .
#      ```
# 2. (Optional) Instantiate/run a container based upon the resulting container image:
#      ```
#      $ docker run --rm -p 8000:8000 nmdc-edge-web-app:some-tag
#      ```
# 3. Tag the container image for publishing to the GitHub Container Registry.
#    a. Get the ID of the container image.
#       ```
#       $ docker images
#       ```
#       - That will display the IDs of all container images. Identify the ID of the image you want to publish.
#    b. Tag the container image with the GHCR prefix (replace the placeholder with the image ID).
#       ```
#       $ docker tag __IMAGE_ID__ ghcr.io/microbiomedata/nmdc-edge-web-app:some-tag
#       ```
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
LABEL org.opencontainers.image.description="NMDC EDGE Web App (Node v18)"

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
CMD ["pm2-runtime", "start", "pm2.config.js"]
