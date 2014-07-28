# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "precise64"
  config.vm.box_url = "http://files.vagrantup.com/precise64.box"

  config.vm.network :forwarded_port, guest: 5000, host: 5000

  config.vm.network "private_network", ip: "192.168.100.100"
  config.vm.synced_folder ".", "/vagrant", type: "nfs"

  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--memory", "1024"]
  end

  config.vm.provision :shell do |shell|
    shell.inline = <<-EOS
      set -e

      if [ ! -f /var/lock/provision ]; then
        export DEBIAN_FRONTEND=noninteractive
        debconf-set-selections <<< 'mysql-server mysql-server/root_password password'
        debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password'

        apt-get update -y -q

        apt-get install -y -q python python-pip python-dev mysql-server libmysqlclient-dev python-software-properties

        apt-add-repository -y ppa:chris-lea/node.js
        apt-get update -y -q
        apt-get install -y -q nodejs

        wget -qO- https://toolbelt.heroku.com/install-ubuntu.sh | sh

        pip install virtualenv
        cd /vagrant
        rm -rf ~/venv
        virtualenv ~/venv
        source ~/venv/bin/activate
        pip install -r requirements.txt

        mysql -u root <<< 'CREATE DATABASE `anyway` CHARSET=utf8' || :
        export CLEARDB_DATABASE_URL="mysql://localhost/anyway?charset=utf8"
        python models.py # create the DB schema
        python process.py # load the CSV into the DB

        touch /var/lock/provision # mark provisioning as completed
      fi
    EOS
  end

  config.vm.provision :shell do |shell|
    shell.inline = <<-EOS
      [ -f /var/lock/provision ] || exit 1

      cd /vagrant
      source ~/venv/bin/activate
      export CLEARDB_DATABASE_URL="mysql://localhost/anyway?charset=utf8"
      killall gunicorn 2>/dev/null
      foreman start
    EOS
  end
end
