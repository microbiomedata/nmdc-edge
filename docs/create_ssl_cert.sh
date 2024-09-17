#!/bin/sh

###############################################################################
# This shell script creates a self-signed SSL certificate.
# Reference: https://typeofnan.dev/a-one-line-command-to-generate-a-self-signed-ssl-certificate/
###############################################################################

echo "Creating self-signed SSL certificate..."
echo

openssl \
  req -nodes -new -x509 \
  -keyout /root/ssl.crt.key \
  -out /root/ssl.crt \
  -subj='/C=US'

echo "Done"
echo
