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

#create upload/log/projects/public directories, skip this step for reinstallation
io_home=$app_home/io
if [ ! -d  $io_home ]; then
  echo "Create directories"
  mkdir ${io_home}

  dirs=(
    "upload"
    "upload/files"
    "upload/tmp" 
    "log"
    "projects"
    "public"
    "db"
    "sra"
  )

  for dir in "${dirs[@]}"
  do
    mkdir ${io_home}/${dir}
  done

  test_data_home=$app_home/data/test_data
  if [ -d  $test_data_home ]; then
    ln -s ${test_data_home} ${io_home}/public/test_data
  fi
  opaver_web_app=$app_home/data/opaver_web
  if [ -d  $opaver_web_app ]; then
    ln -s ${opaver_web_app} ${io_home}/opaver_web
  fi
fi

echo "Generate imports.zip"
wdl_dirs=(
  "metaG"
  "metaP"
  "metaT"
  "organicMatter"
  "sra"
)

for wdl_dir in "${wdl_dirs[@]}"
do
  cd $app_home/data/workflow/WDL/${wdl_dir}
  zip -r imports.zip *.wdl
  if [ "$?" != "0" ]; then
    echo "Cannot create $app_home/data/workflow/WDL/${wdl_dir}/imports.zip!" 1>&2
    exit 1
  fi
done

echo "setup NMDC EDGE webapp ..."
#build client
echo "build client..."
cd $app_home/webapp/client
npm install --legacy-peer-deps
npm run build
#build server
echo "build server..."
cd $app_home/webapp/server
npm install

echo "NMDC EDGE webapp successfully installed!"
echo "To start the webapp:"
echo "pm2 start pm2.config.js"
