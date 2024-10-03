## INSTALLATION PREREQUISITES

### Install Node v20
https://nodejs.org/en/download/prebuilt-installer

### Install pm2
`npm install pm2@latest -g`

### Install MongoDB Community Edition
https://docs.mongodb.com/manual/installation/#mongodb-community-edition-installation-tutorials

### Create environment variables

The web client and web server each rely on environment variables for their configuration.
You can define those environment variables directly in your system environment, 
define them in `.env` files, or define them in both places.

Here's how you can define them in `.env` files:

- Populate the "client build" environment configuration file (i.e. `webapp/client/.env`).
  - You can initialize it based upon the corresponding example file:
    ```shell
    cp webapp/client/.env.example \
       webapp/client/.env
    ```
    > Those environment variables are used within `webapp/client/src/config.js`.
- Populate the server environment configuration file (i.e. `webapp/server/.env`).
  - You can initialize it based upon the corresponding example file:
    ```shell
    cp webapp/server/.env.example \
       webapp/server/.env
    ```
    > Those environment variables are used within `webapp/server/config.js`.

> If the same environment variable is defined in both your system environment and in an `.env` file, 
> the definition in your system environment will be used and the one in the `.env` file will be 
> [ignored](https://github.com/motdotla/dotenv/blob/master/README.md#what-happens-to-environment-variables-that-were-already-set).


## INSTALLING webapp

### Procedure

1. Move/copy nmdc-edge folder to the installation directory

2. Inside nmdc-edge/installation folder, run the installation script 

    `./install.sh`

## STARTING webapp

### Procedure

1. Start the MongoDB server.
2. Start the web app server via PM2:
   ```shell
   pm2 start pm2.config.js
   ```
    
## STOP webapp
`pm2 stop all`
