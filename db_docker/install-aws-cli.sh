#!/bin/sh
set -e

# Both pinned database images use Debian Bullseye.
sed -i 's|http://apt.postgresql.org/pub/repos/apt|https://apt-archive.postgresql.org/pub/repos/apt|g' /etc/apt/sources.list.d/pgdg.list
sed -i 's|http://deb.debian.org/debian-security|https://archive.debian.org/debian-security|g' /etc/apt/sources.list

apt-get update
apt-get install -y curl unzip
curl -fsSL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o awscliv2.zip
unzip -q awscliv2.zip
./aws/install
rm -rf aws awscliv2.zip
aws --version
