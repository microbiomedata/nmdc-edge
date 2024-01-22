## INSTALLATION PREREQUISITES

### Install Node16
https://nodejs.org/dist/latest-v16.x/

### Install pm2
`npm install pm2@latest -g`

### Install MongoDB Community Edition
https://docs.mongodb.com/manual/installation/#mongodb-community-edition-installation-tutorials

### Populate Configuration Files

1. Populate the "client build" configuration file (i.e. `webapp/client/.env`).
   - You can initialize it based upon the corresponding example file:
     ```shell
     cp webapp/client/.env.example webapp/client/.env
     ```

## INSTALLING webapp

### Procedure

1. Move/copy nmdc-edge folder to the installation directory

2. Inside nmdc-edge/installation folder, run the installation script 

    `./install.sh`

## STARTING webapp

### Procedure

1. Start MongoDB if it's not started yet

2. Inside nmdc-edge/installation folder, run the pm2 start command 

    `pm2 start server_pm2.json`
    
## STOP webapp
`pm2 stop all`
