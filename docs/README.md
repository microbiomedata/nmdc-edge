# Documentation

This directory contains documentation and files related to managing the NMDC EDGE web application.

## Files

- `./README.md` - (You are here)
- `./docker-compose.prod.yml` - A `docker-compose.yml` file designed to facilitate deploying the NMDC EDGE web application to a production environment.
- `./nginx-default.conf.template` - An Nginx configuration file in which variable names will be replaced with their values.
- `./create_ssl_cert.sh` - A shell script designed to generate a self-signed SSL certificate when the `nginx` container starts up.
- `./initialize_vm_on_jetstream2.sh` - A shell script designed to facilitate initializing the Docker host (i.e. the Jetstream2 VM that will run Docker).

## Appendix

Here's a command you can run in order to download the `docker-compose.prod.yml` file onto the VM:

```shell
curl -o ./docker-compose.yml https://raw.githubusercontent.com/microbiomedata/nmdc-edge/main/docs/docker-compose.prod.yml
```
> The downloaded file will be named: `docker-compose.yml`

Here's a command you can run in order to download the `nginx-default.conf.template` file onto the VM:

```shell
curl -o ./nginx-default.conf.template https://raw.githubusercontent.com/microbiomedata/nmdc-edge/main/docs/nginx-default.conf.template
```

Here's a sequence of commands you can run in order to download the `create_ssl_cert.sh` script onto the VM and make it executable:

```shell
curl  -o create_ssl_cert.sh https://raw.githubusercontent.com/microbiomedata/nmdc-edge/main/docs/create_ssl_cert.sh
chmod +x create_ssl_cert.sh
```

Here's a sequence of commands you can run in order to download the `initialize_vm_on_jetstream2.sh` script onto the VM and make it executable:

```shell
curl  -o initialize_vm.sh https://raw.githubusercontent.com/microbiomedata/nmdc-edge/main/docs/initialize_vm_on_jetstream2.sh
chmod +x initialize_vm.sh
```
