#!/bin/bash
echo "Install NMDC EDGE webapp..."

#production installation will be with https and nginx proxy
read -p 'Is production installation? [y/n]'
if [[ $REPLY =~ ^[Yy] ]]; then
  env="production"
else
  env="development"
fi

#check server-env-prod
quit=0
if [ ! -f ./server-env-prod ]; then
  echo "ERROR: server-env-prod not found in current directiory"
  quit=1
fi
[[ $quit == 1 ]] && exit 1

pwd=$PWD
app_home="$(dirname "$pwd")"

read -p 'Web server domain name (default localhost)? ' web_server_domain
[[ ! $web_server_domain ]] && web_server_domain=localhost
read -p 'Webapp port (default 5000)? ' web_server_port
[[ ! $web_server_port ]] && web_server_port=5000

echo "Install $env NMDC EDGE webapp to $app_home"
if [[ $env == "production" ]]; then
  echo "URL: https://$web_server_domain"
else
  echo "URL: http://$web_server_domain:$web_server_port"
fi

read -p 'Continue to install NMDC EDGE webapp? [y/n]'
[[ ! $REPLY =~ ^[Yy]$ ]] && exit 1

# Prompt user for installation system
echo 'What OS are you using? ' 
options=("Mac" "Linux" "Quit")
select opt in "${options[@]}"
do
    case $opt in
        "Mac")
            break;
            ;;
        "Linux")
            break;
            ;;
        "Quit")
            exit 1;
            ;;
        *) echo "invalid option $REPLY";;
    esac
done

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

echo "Generate host.env"
echo "web_server_domain=$web_server_domain" > $app_home/host.env
echo "web_server_port=$web_server_port" >> $app_home/host.env

#setup .env and server_pm2.json
#Add this export for MacOS, otherwise will get 'tr: Illegal byte sequence' error
export LC_CTYPE=C
#Generate random 20 character string (upper and lowercase)
oauth_secret=`cat /dev/urandom|tr -dc '[:alpha:]'|fold -w ${1:-20}|head -n 1`
sendmail_key=`cat /dev/urandom|tr -dc '[:alpha:]'|fold -w ${1:-20}|head -n 1`
jwt_key=`cat /dev/urandom|tr -dc '[:alpha:]'|fold -w ${1:-20}|head -n 1`

cp $pwd/server-env-prod $app_home/webapp/server/.env
cp $pwd/server_pm2.tmpl $pwd/server_pm2.json
if [[ $opt == 'Mac' ]]; then
  sed -i "" "s/\<WEB_SERVER_DOMAIN\>/${web_server_domain}/g" $app_home/webapp/client/.env
  sed -i "" "s/\<WEB_SERVER_PORT\>/${web_server_port}/g" $app_home/webapp/client/.env
  sed -i "" "s/\<WEB_SERVER_DOMAIN\>/${web_server_domain}/g" $app_home/webapp/server/.env
  sed -i "" "s/\<WEB_SERVER_PORT\>/${web_server_port}/g" $app_home/webapp/server/.env
  sed -i "" "s/\<APP_HOME\>/${app_home//\//\\/}/g" $app_home/webapp/server/.env
  sed -i "" "s/\<IO_HOME\>/${io_home//\//\\/}/g" $app_home/webapp/server/.env
  sed -i "" "s/\<JWT_KEY\>/${jwt_key}/g" $app_home/webapp/server/.env
  sed -i "" "s/\<OAUTH_SECRET\>/${oauth_secret}/g" $app_home/webapp/server/.env
  sed -i "" "s/\<SENDMAIL_KEY\>/${sendmail_key}/g" $app_home/webapp/server/.env
  sed -i "" "s/\<APP_HOME\>/${app_home//\//\\/}/g" $pwd/server_pm2.json
else
  sed -i "s/<WEB_SERVER_DOMAIN>/${web_server_domain}/g" $app_home/webapp/client/.env
  sed -i "s/<WEB_SERVER_PORT>/${web_server_port}/g" $app_home/webapp/client/.env
  sed -i "s/<WEB_SERVER_DOMAIN>/${web_server_domain}/g" $app_home/webapp/server/.env
  sed -i "s/<WEB_SERVER_PORT>/${web_server_port}/g" $app_home/webapp/server/.env
  sed -i "s/<APP_HOME>/${app_home//\//\\/}/g" $app_home/webapp/server/.env
  sed -i "s/<IO_HOME>/${io_home//\//\\/}/g" $app_home/webapp/server/.env
  sed -i "s/<JWT_KEY>/${jwt_key}/g" $app_home/webapp/server/.env
  sed -i "s/<OAUTH_SECRET>/${oauth_secret}/g" $app_home/webapp/server/.env
  sed -i "s/<SENDMAIL_KEY>/${sendmail_key}/g" $app_home/webapp/server/.env
  sed -i "s/<APP_HOME>/${app_home//\//\\/}/g" $pwd/server_pm2.json
fi

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
echo "pm2 start server_pm2.json"
