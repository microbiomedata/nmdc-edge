## INSTALLATION PREREQUISITES

### Install Node16
https://nodejs.org/dist/latest-v16.x/

### Install pm2
`npm install pm2@latest -g`

### Install MongoDB Community Edition
https://docs.mongodb.com/manual/installation/#mongodb-community-edition-installation-tutorials

## INSTALLING webapp

### Procedure

1. Move/copy nmdc-edge folder to the installation directory

2. Inside nmdc-edge/installation folder, run the installation script 

    `./install.sh`

    e.g.

    ```
    yan@edge-nmdc:~/nmdc-edge/installation$ ./install.sh 
    Install NMDC EDGE ...
    Web server domain name (default localhost)? edge-nmdc.org
    Web server port (default 5000)? 
    Install NMDC EDGE to /home/yan/nmdc-edge
    URL: http://edge-nmdc.org:5000
    Continue to install NMDC EDGE? [y/n]y
    What OS are you using? 
    1) Mac
    2) Linux
    3) Quit
    #? 2
    Generate imports.zip
    ...
    setup NMDC EDGE webapp ...
    Generate host.env
    build client...
    ...
    build server...
    ...
    NMDC EDGE successfully installed!
    To start the webapp:
    pm2 start server_pm2.json

    ```

3. Inside nmdc-edge/installation folder, import default admin user (username: admin@my.edge password: good#4Admin). You need start your MongoDB before importing admin user. 

    `mongoimport --db=nmdcedge --collection=users --file=admin_user.json`

## STARTING webapp

### Procedure

1. Start MongoDB if it's not started yet

2. Inside nmdc-edge/installation folder, run the pm2 start command 

    `pm2 start server_pm2.json`
    
## STOP webapp
`pm2 stop all`
