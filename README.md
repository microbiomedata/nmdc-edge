# nmdc-edge

This repository contains the source code of the NMDC EDGE web application.

The NMDC EDGE web application is the web-based interface through which researchers can access the NMDC EDGE platform. 
The NMDC EDGE platform is a [Cromwell](https://cromwell.readthedocs.io/en/stable/)-based system researchers can use to
process omics data using standardized bioinformatics workflows.

You can learn more about the NMDC EDGE platform by reading the [NMDC EDGE tutorials](https://nmdc-edge.org/tutorial).

## Table of contents

* [Architecture](#architecture)
* [Development](#development)
  * [Development stack](#development-stack)
    * [Setup](#setup)
      * [Prerequisites](#prerequisites)
      * [Procedure](#procedure)
    * [Usage](#usage)
* [Deployment](#deployment)
  * [Building and publishing the container image](#building-and-publishing-the-container-image)
    * [Building](#building)
    * [Publishing](#publishing)
      * [References](#references)
  * [Instantiating the container image](#instantiating-the-container-image)

## Architecture

Here's a diagram depicting the architecture of the NMDC EDGE platform,
including how the NMDC EDGE web application fits into it.

```mermaid
graph LR
    %% Nodes:
    user["Web Browser"]
    cromwell["Workflow Management System<br>(Cromwell)"]
    workers[["Workers"]]
    
    subgraph "NMDC EDGE Web Application"
      %% Nodes:
      client["Web Client<br>(React.js)"]
      server["Web Server<br>(Express.js)"]
      db[("Database<br>(MongoDB)")]
    end
    
    %% Relationships:
    user --> client
    client --> server
    server --> db
    server --> cromwell
    cromwell --> workers
```

Here's a list of the main technologies upon which the NMDC EDGE web application is built:

- [React.js](https://react.dev/) (web client)
- [Node.js](https://nodejs.org/en) + [Express.js](https://expressjs.com/) (web server)
- [MongoDB](https://www.mongodb.com/) (database)

## Development

### Development stack

This repository includes a container-based development stack consisting of three containers:
- `webapp` - runs the NMDC EDGE web application
- `mongo` - runs a MongoDB server
- `cromwell` - runs a Cromwell server

You can use the development stack to run the NMDC EDGE web application locally.

#### Setup

##### Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop/) is installed on your computer.
    - For example, version 24:
      ```shell
      $ docker --version
      Docker version 24.0.6, build ed223bc
      ```
- The "client build" configuration file (i.e. `webapp/client/.env`) is populated.
  - You can initialize it based upon the corresponding example file:
    ```shell
    cp webapp/client/.env.example webapp/client/.env
    ```
    > Those environment variables are used within `webapp/client/src/config.js`.
- The server configuration file (i.e. `webapp/server/.env`) is populated.
  - You can initialize it based upon the corresponding example file:
    ```shell
    cp webapp/server/.env.example webapp/server/.env
    ```
    > Those environment variables are used within `webapp/server/config.js`.

##### Procedure

You can spin up the development stack by running the following command in the root directory of the repository:

```shell
docker compose up
```

> Alternatively, if you've made any changes to the `Dockerfile` since the last time you ran that command,
> run it with the `--build` option so those changes take effect.
> 
> ```shell
> docker compose up --build
> ```
> 
> Note: Building a new container image can take several minutes; whereas starting up an existing container image
> usually takes only a few seconds.

#### Usage

Once the development stack is up and running, you can access various pieces of it from your computer as shown here:

```mermaid
---
title: Accessing parts of the development stack
---
graph LR
    %% Links:
    host -- "$ cd ./io" --> io
    host -- "$ curl http://localhost:8000" --> server
    host -- "$ curl http://localhost:8001" --> cromwell_server
    host -- "$ docker compose exec webapp sh" --> webapp_shell
    webapp_shell -- "# mongo --host mongo:27017" --> db
    webapp_shell -- "# cd /app/io" --> io
    host -- "$ mongo --host localhost:27017" --> db
    webapp_shell -- "# wget -q -O- http://cromwell:8000" --> cromwell_server
    
    subgraph WebAppContainer["webapp container"]
        server["Web server"]
        webapp_shell["Bourne shell (sh)"]
    end
    
    subgraph MongoContainer["mongo container"]
        db["MongoDB server"]
    end
    
    subgraph CromwellContainer["cromwell container"]
        cromwell_server["Cromwell server"]
    end
    
    subgraph Host["Host"]
        host["Terminal<br>(You are here)"]
        io[("IO directory")]
    end        
```

## Deployment

### Building and publishing the container image

Here's how you can build and deploy new versions of the `webapp` container image.

#### Building

You can build a new version of the `webapp` container image by issuing one of the following commands:

- If the architecture of the computer you're using to build the image, and the architecture of the computer on which 
  containers based upon the image will run, are the **same** (e.g. both are arm64, or both are AMD64); then you can use
  this command to build the image (replace `{some_tag}` with a unique identifier for this version, such as `v1.2.3`):
  ```shell
  docker build -f webapp-node20.Dockerfile \
               -t nmdc-edge-web-app:{some_tag} .
  ```
  <details>
    <summary>Example</summary>

    ```console
    $ docker build -f webapp-node20.Dockerfile -t nmdc-edge-web-app:v1.2.3 .
    ```
  </details>

- If the architecture of the computer you're using to build the image is **arm64** (e.g. an M1 Mac), and the
  architecture of the computer on which containers based upon the image will run is **AMD64**; then you can use _this_
  command to build the image (replace `{some_tag}` with a unique identifier for this version, such as `v1.2.3`):
  ```shell
  docker buildx build --platform linux/amd64 \
                      -f webapp-node20.Dockerfile \
                      -t nmdc-edge-web-app:some-tag .
  ```
  <details>
    <summary>Example</summary>

    ```console
    $ docker buildx build --platform linux/amd64 -f webapp-node20.Dockerfile -t nmdc-edge-web-app:v1.2.3 .
    ```
  </details>

#### Publishing

Here's how you can publish the newly-built container image to 
[GitHub Container Registry (GHCR)](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

1. Get the ID of the newly-built container image.
   ```shell
   docker images
   ```
   <details>
     <summary>Example</summary>

     ```console
     $ docker images
     REPOSITORY         TAG     IMAGE ID      CREATED       SIZE
     ...
     nmdc-edge-web-app  v1.2.3  365743f24303  1 minute ago  1.35GB
     ...
     ```
   </details>
2. Give the container image a tag that begins with `ghcr.io/microbiomedata/nmdc-edge-web-app` 
   (replace `{image_id}` with the ID of the container image, and replace `{some_tag}` with the tag
   you want the container image to have when published).
   ```shell
   docker tag {image_id} ghcr.io/microbiomedata/nmdc-edge-web-app:{some_tag}
   ```
   <details>
     <summary>Example</summary>

     ```console
     $ docker tag 365743f24303 ghcr.io/microbiomedata/nmdc-edge-web-app:v1.2.3
     ```
   </details>
3. Upload the container image to GitHub Container Registry (GHCR) (replace `{some_tag}` with the same tag
   you used in the previous step):
   ```shell
   docker push ghcr.io/microbiomedata/nmdc-edge-web-app:{some_tag}
   ```
   <details>
     <summary>Example</summary>

     ```console
     $ docker push ghcr.io/microbiomedata/nmdc-edge-web-app:v1.2.3
     The push refers to repository [ghcr.io/microbiomedata/nmdc-edge-web-app]
     1990b48a8037: Pushing [====================>          ]  35.07MB/64.54MB
     c60069b08109: Pushing [====>                          ]   37.4MB/271.3MB
     986a439534f8: Pushing [===>                           ]  47.53MB/440.2MB
     7f3870580da8: Pushed
     ff224f440bfc: Pushed
     ...
     d4fc045c9e3a: Waiting   
     ```
   </details>
4. Verify the container image is listed on 
   [GHCR](https://github.com/orgs/microbiomedata/packages/container/package/nmdc-edge-web-app).

##### References

- https://github.com/orgs/microbiomedata/packages/container/package/nmdc-edge-web-app
- https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry

### Instantiating the container image

_Coming soon..._
