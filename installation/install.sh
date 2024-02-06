#!/bin/bash
echo "Install NMDC EDGE webapp..."

pwd=$PWD
app_home="$(dirname "$pwd")"

read -p 'Web server domain name (default localhost)? ' web_server_domain
[[ ! $web_server_domain ]] && web_server_domain=localhost
read -p 'Webapp port (default 5000)? ' web_server_port
[[ ! $web_server_port ]] && web_server_port=5000

read -p 'Continue to install NMDC EDGE webapp? [y/n]'
[[ ! $REPLY =~ ^[Yy]$ ]] && exit 1

# TODO: Consolidate the recurrences of the `mkdir` and `zip` (etc.) commands into a loop.

#create upload/log/projects/public directories, skip this step for reinstallation
io_home=$app_home/io
if [ ! -d  $io_home ]; then
  mkdir ${io_home}
  mkdir ${io_home}/upload
  mkdir ${io_home}/upload/files
  mkdir ${io_home}/upload/tmp
  mkdir ${io_home}/log
  mkdir ${io_home}/projects
  mkdir ${io_home}/public
  mkdir ${io_home}/db
  mkdir ${io_home}/sra
  #ln -s ${app_home}/data/test_data ${io_home}/public/test_data
fi

echo "Generate imports.zip"
cd $app_home/data/workflow/WDL/metaG
zip -r imports.zip *.wdl
if [ "$?" != "0" ]; then
  echo "Cannot create $app_home/data/workflow/WDL/metaG/imports.zip!" 1>&2
  exit 1
fi
cd $app_home/data/workflow/WDL/metaP
zip -r imports.zip *.wdl
if [ "$?" != "0" ]; then
  echo "Cannot create $app_home/data/workflow/WDL/metaP/imports.zip!" 1>&2
  exit 1
fi
cd $app_home/data/workflow/WDL/metaT
zip -r imports.zip *.wdl
if [ "$?" != "0" ]; then
  echo "Cannot create $app_home/data/workflow/WDL/metaT/imports.zip!" 1>&2
  exit 1
fi
cd $app_home/data/workflow/WDL/organicMatter
zip -r imports.zip *.wdl
if [ "$?" != "0" ]; then
  echo "Cannot create $app_home/data/workflow/WDL/organicMatter/imports.zip!" 1>&2
  exit 1
fi
cd $app_home/data/workflow/WDL/virusPlasmids
zip -r imports.zip *.wdl
if [ "$?" != "0" ]; then
  echo "Cannot create $app_home/data/workflow/WDL/virusPlasmids/imports.zip!" 1>&2
  exit 1
fi
cd $app_home/data/workflow/WDL/sra
zip -r imports.zip *.wdl
if [ "$?" != "0" ]; then
  echo "Cannot create $app_home/data/workflow/WDL/sra/imports.zip!" 1>&2
  exit 1
fi

echo "setup NMDC EDGE webapp ..."

# TODO: Where, if anywhere, is the `host.env` file used?
echo "Generate host.env"
echo "web_server_domain=$web_server_domain" > $app_home/host.env
echo "web_server_port=$web_server_port" >> $app_home/host.env

#build client
echo "build client..."
cd $app_home/webapp/client
npm install
npm run build
#build server
echo "build server..."
cd $app_home/webapp/server
npm install

echo "NMDC EDGE webapp successfully installed!"
echo "To start the webapp:"
echo "pm2 start pm2.config.js"
