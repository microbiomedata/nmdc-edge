#!/bin/bash

###############################################################################
#
# ━━━━━━━
# Summary
# ━━━━━━━
#
# This shell script initializes a virtual machine (VM) hosted on the Jetstream2
# platform so that the VM can run the NMDC EDGE web app.
#
# ━━━━━━━━━━━━━
# Preconditions
# ━━━━━━━━━━━━━
#
# - The VM (which Jetstream2 refers to as an "instance") has these characteristics:
#   - Flavor: `m3.medium` (i.e. 8 CPUs, 30 GB RAM, 60 GB root disk)
#   - Operating system: `Ubuntu 22.04`
#   - It has a ≥10 GB (persistent) Volume mounted at some path
#     (see `MONGO_DATA_DIR_PATH` in "Configuration" section below)
# - The VM belongs to the same security group as the NFS server. At the time
#   of this writing, that group is named: `cluster-alma8-secgroup`
# - You can SSH into the VM as the user: `exouser`
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Configuration (via environment variables)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# - MONGO_DATA_DIR_PATH: Absolute path to the Volume on which Mongo will store data
# - NMDC_EDGE_WEB_APP_USER_NAME: Name of user the web app will run as
# - NMDC_EDGE_WEB_APP_UID: UID of that user
# - NMDC_EDGE_WEB_APP_GROUP_NAME: Name of group to which that user will belong
# - NMDC_EDGE_WEB_APP_GID: GID of that group
# - NFS_SERVER_IP_ADDRESS: IP address of the NFS server
# - LOCAL_NFS_VOLUME_MOUNT_PATH: Local path at which you want to mount the NFS volume
#
# ━━━━━
# Usage
# ━━━━━
#
# 1. Get this script onto the VM (copy/paste its contents into Vim, then save):
#    $ vi ~/initialize_vm_on_jetstream2.sh
# 2. Make the script executable by running:
#    $ chmod +x ~/initialize_vm_on_jetstream2.sh
# 3. Define any necessary environment variables (see above).
# 4. Run the script and follow the on-screen instructions:
#    $ ~/initialize_vm_on_jetstream2.sh
#
###############################################################################

# Read environment variables into local variables.
mongo_data_dir_path="${MONGO_DATA_DIR_PATH:-/media/volume/nmdc-edge-web-app-mongo-data-20240715}"
nmdc_edge_web_app_user_name="${NMDC_EDGE_WEB_APP_USER_NAME:-webuser}"
nmdc_edge_web_app_uid="${NMDC_EDGE_WEB_APP_UID:-60005}"
nmdc_edge_web_app_group_name="${NMDC_EDGE_WEB_APP_GROUP_NAME:-webuser}"
nmdc_edge_web_app_gid="${NMDC_EDGE_WEB_APP_GID:-60005}"
nfs_server_ip_address="${NFS_SERVER_IP_ADDRESS:-10.0.61.212}"
local_nfs_volume_mount_path="${LOCAL_NFS_VOLUME_MOUNT_PATH:-/mnt/}"

# Install dependencies.
echo "Installing dependencies."
echo
echo "Note: If presented with a pink GUI about restarting the services,"
echo "      'networkd-dispatcher.service' and 'unattended-upgrades.service',"
echo "      select both services and press 'OK' to restart them."
echo
read -p "Press Enter to start installing dependencies..."
echo
sudo apt update
sudo apt install -y nfs-common
curl -o ~/docker-compose.yml https://raw.githubusercontent.com/microbiomedata/nmdc-edge/main/docs/docker-compose.prod.yml

# Check dependencies.
echo "Checking dependencies."
dpkg   --version
dpkg   -l nfs-common
sudo   --version
ufw    --version
curl   --version
docker --version
docker compose version
which stat
which id
which mount
which useradd
which groupadd
stat "${mongo_data_dir_path}"

# Configure and enable the firewall.
#
# Note: The `--force` flag avoids the interactive "(y/n)" prompt.
#
echo "Configuring and enabling firewall."
sudo ufw status verbose
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable
sudo ufw status verbose

# Create the application-specific group and user.
echo "Creating application-specific group and user."
sudo groupadd --gid "${nmdc_edge_web_app_gid}" \
              "${nmdc_edge_web_app_group_name}"
sudo useradd  --no-user-group \
              --gid "${nmdc_edge_web_app_gid}" \
              --uid "${nmdc_edge_web_app_uid}" \
              "${nmdc_edge_web_app_user_name}"
id "${nmdc_edge_web_app_user_name}"

# Mount the NFS volume used by Cromwell.
echo "Mounting NFS volume."
sudo mount -t nfs4 \
           -o proto=tcp,nosuid,nolock,noatime,actimeo=3,nfsvers=4.2,seclabel,x-systemd.automount,x-systemd.mount-timeout=30,_netdev \
           "${nfs_server_ip_address}:/project" \
           "${local_nfs_volume_mount_path}"
stat "${local_nfs_volume_mount_path}"

# Suggest some follow-on actions to the user.
echo
echo "Done."
echo
echo "To start the web app:"
echo "1. $ cd ~                        # Go to your home directory"
echo "2. $ vi .env                     # Create environment variables"
echo "3. $ docker compose up --detach  # Spin up the Docker Compose stack"
echo
