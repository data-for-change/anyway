ANYWAY’s docker environment
===========================

Docker is an open source project to pack, ship and run any application as a lightweight container.

The idea is to deploy a container (light weight environment) that has all our app dependencies installed and ready to go.
As a developer you can do one of both:

* Use the container do write your code (using vim/nano or any other GNU text editing tool - not recommended)
* Use a git repo cloned to your local machine and use the container as a remote server running the app

The container loads itself with the command given in the instructions, it has the DB on it, deployed and ready to work (at /anyway/local.db)
With every local code change, the container would restart itself and the changes would be immediately available in your web browser.
The current image is based on an Ubuntu linux with java.

Read more on the docker [Github project](https://github.com/docker/docker)


Instructions
-----------------------
* Please complete ANYWAY’s [“getting the code” section](https://github.com/hasadna/anyway#getting-the-code) before starting

**1.** [Get the code](https://github.com/hasadna/anyway#getting-the-code)

**2.** [Install Docker](https://docs.docker.com/install/)

**Continue with your OS, See below**

**For Mac:**

**3.** Build anyway container: `docker-compose build`

**4.** Start the container, go to the **anyway** directory and run:
    `docker-compose up -d`

**5.** Download the [db dump](https://drive.google.com/drive/folders/1OesX8Y2MGgIcj0B3f5cdS-BIzt4govXA?usp=sharing) (You need to request access) and save it in the **anyway** directory.
Restore the db (in anyway directory): `cat <truncated dump file path> | docker-compose exec -T db psql -U anyway`
Now your containers are up and with data loaded.

**6.** **You're all set!** ANYWAY is up and running - connect to http://127.0.0.1:8080
Note - you won't see the map since the key works in production.

**7.** To stop the containers run: `docker-compose down`

**For Ubuntu:**

**3.** Build anyway container: `sudo docker-compose build`

**4.** Start the container, go to the **anyway** directory and run:
    `sudo docker-compose up -d`

**5.** Download the [db dump](https://drive.google.com/drive/folders/1OesX8Y2MGgIcj0B3f5cdS-BIzt4govXA?usp=sharing) (You need to request access) and save it in the **anyway** directory.
Restore the db (in anyway directory): `cat <truncated dump file path> | sudo docker-compose exec -T db psql -U anyway`
Now your containers are up and with data loaded.

**6.** **You're all set!** ANYWAY is up and running - connect to http://127.0.0.1:8080
Note - you won't see the map since the key works in production.

**7.** To stop the containers run: `sudo docker-compose down`


Environment Configuration for WIndows 
-----------------------
**1.** Install Oracle Virtual Box for Window - Download 'Windows hosts' installer from: https://www.virtualbox.org/wiki/Downloads

**2.** Create new VM for Ubuntu OS - see next tutorial – 'How to Use VirtualBox' - https://www.youtube.com/watch?v=sB_5fqiysi4&t=315s

**3.** After VM creation, if you're dealing the next warning:

"System Acceleration Settings: The hardware virtualization is enabled in the Acceleration section of the system although it is not supported from the host system. It should be disabled in order to start the visual system."

you need to enable virtualization in the BIOS Screen – Base on your computer, go to BIOS Screen to enable virtualization, see for example: 
'How to enable Virtualization (VT-x) in Bios' - https://www.youtube.com/watch?v=MOuTxfzCvMY

**4.** In the VM Settings storage - Download Ubuntu 18.04 LTS iso for Desktop: https://releases.ubuntu.com/18.04.4/

**5.** Power-On the VM and the Ubuntu installation should start

**6.** You have Ubuntu VM on your Windows!

**7.** Get the code, install docker and run Anyway Container for Ubuntu

More
-----------------------
To install requirements again, redeploy DB or any requirement involving the dependencies installation,
simply rebuild the image;
then go to its local path and `docker build --no-cache -t hasdna/anyway .`

## Docker commands

Set your VM with the current running shell session:

    eval "$(docker-machine env default)"


List your local docker images:

    docker images

List your running containers:

    docker ps

List all containers ever:

    docker ps -a

Stop a running container (id is listed in `docker ps`):

    docker top <container-id>

Deleting an image(from `docker images`):

    docker rmi <image-id>

Rebuild the image:

    docker-compose build


Additional Notes
-----------------------
If you want to work with your own code and the docker or if your 8080 port is already taken by other dockers\servers you need to create an override for the docker-compose.
For example:

```version: '2'
services:
 anyway:
   volumes:
     - ./anyway:/anyway/anyway
```

This loads the ./anyway dir (relative to the docker-compose file) as /anyway/anyway in the docker overriding the inner volume and allowing you to run your own code inside the docker.

Questions and ideas
-----------------
Talk to Atalya on HASADNA's Slack (atalya)
