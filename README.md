# nmdc-edge

This repository contains the source code of the NMDC EDGE web application.

The NMDC EDGE web application is the web-based interface through which researchers can access the NMDC EDGE platform. 
The NMDC EDGE platform is a [Cromwell](https://cromwell.readthedocs.io/en/stable/)-based system researchers can use to
process omics data using standardized bioinformatics workflows.

You can learn more about the NMDC EDGE platform by reading the [NMDC EDGE tutorials](https://nmdc-edge.org/tutorial).

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

This repository includes a **limited** container-based development stack consisting of three containers:
- `webapp` - runs the web server (which serves both the web client and the HTTP API)
- `mongo` - runs a MongoDB server
- `cromwell` - runs a Cromwell server

You can use the development stack to run the NMDC EDGE web application locally. The main **limitation** is that changes
made to the web app client's file tree are not automatically reflected by the web app. That's because the web app serves
the client from the `webapp/client/build` directory, and updating the contents of that directory involves manually
running `$ npm run build` in the `webapp/client` directory. One workaround is to access the shell of the `webapp`
container and manually run that command after you make changes to the client's file tree. Other workarounds exist,
but they are not documented here.

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
- The server configuration file (i.e. `webapp/server/.env`) is populated.
  - You can initialize it based upon the corresponding example file:
    ```shell
    cp webapp/server/.env.example webapp/server/.env
    ```
    > Note: Many of the environment variables in the example server configuration file are not yet documented.
      Please file an [issue](https://github.com/microbiomedata/nmdc-edge/issues) when you encounter
      an environment variable you find confusing. That will help the maintainers prioritize
      documentation-related tasks.

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
graph BT
    host["Terminal<br>(You are here)"]
    
    %% Links:
    host -- "$ curl http://localhost:8000" --> server
    host -- "$ curl http://localhost:8001" --> cromwell_server
    host -- "$ docker compose exec webapp sh" --> webapp_shell
    webapp_shell -- "# mongo --host mongo:27017" --> db
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
```

## Deployment

Coming soon...