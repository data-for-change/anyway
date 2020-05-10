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
* For Windows users please first install ubuntu VM. See [UBUNTU_VM_ON_WINDOWS](docs/UBUNTU_VM_ON_WINDOWS.md)

* Please complete ANYWAY’s [“getting the code” section](https://github.com/hasadna/anyway#getting-the-code) before starting

**1.** [Get the code](https://github.com/hasadna/anyway#getting-the-code)

**2.** [Install Docker](https://docs.docker.com/install/)

**3.** Copy the GDRIVE_FILE_ID from [this file](https://drive.google.com/file/d/1IRnSsRwwHFtmGTNlSOfChg-H6R8JKMpl/view?usp=sharing) (You need to request access)
**Continue with your OS, See below**

**For Mac:**

**4.** Build anyway container (in anyway main directory): `docker-compose -f docker-compose.yml build --build-arg CURR_ENV=DEV --build-arg GDRIVE_FILE_ID=<GDRIVE_FILE_ID value>`

**5.** Start the container, go to the **anyway** directory and run:
    `docker-compose up -d`

**6.** **You're all set!** ANYWAY is up and running with the DB data - connect to http://127.0.0.1:8080
Note - you won't see the map since the key works in production.
If you need to see the map contact atalya via slack to get a developer key.

**7.** To stop the containers run: `docker-compose down`

**8.** To rebuild the docker containers with the most updated db, run `docker volume rm anyway_db_data` and go back to stage 4.

**For Ubuntu:**

**4.** Build anyway container (in anyway main directory): `sudo docker-compose -f docker-compose.yml build --build-arg CURR_ENV=DEV --build-arg GDRIVE_FILE_ID=<GDRIVE_FILE_ID value>`

**5.** Start the container, go to the **anyway** directory and run:
    `sudo docker-compose up -d`

**6.** **You're all set!** ANYWAY is up and running with the DB data - connect to http://127.0.0.1:8080
Note - you won't see the map since the key works in production.
If you need to see the map for development email us [anyway@anyway.co.il](mailto:anyway@anyway.co.il) to get a developer key.

**7.** To stop the containers run: `sudo docker-compose down`

**8.** To rebuild the docker containers with the most updated db, run `sudo docker volume rm anyway_db_data` and go back to stage 4.

## Additional Docker commands
Use `sudo` before each docker commands if you are using ubuntu.

To install requirements again, update DB schema OR redeploy any of the requirement involving the dependencies installation,
simply rebuild the image;
Run in anyway `docker-compose build`

List your local docker images:

    docker images

List your running containers:

    docker ps

List all containers ever:

    docker ps -a

Stop a running container (id is listed in `docker ps`):

    docker top <container-id>

Rebuild the image:

    docker-compose build

Open container bash terminal to execute commands (while container is running):

    docker exec -it <container-name> bash

For example - to open the bash terminal of the anyway container:

    docker exec -it anyway bash

For example - to open the bash terminal of the db container:

    docker exec -it db bash

**Be careful with the following command** Deleting an image(from `docker images`):

    docker rmi <image-id OR image repository>

**Be careful with the following command** Remove the DB volume (this will delete all db data)

    docker volume rm anyway_db_data

**Be careful with the following command** Delete all docker unused images and all volumes

    docker system prune --all --volumes

Set your VM with the current running shell session:

    eval "$(docker-machine env default)"


Additional Notes
-----------------------
If you want to work with your own code and the docker OR if your 8080 port is already taken by other dockers\servers you need to create an override for the docker-compose.
For example:

```version: '3'
services:
 anyway:
   volumes:
     - ./anyway:/anyway/anyway
```

This loads the ./anyway dir (relative to the docker-compose file) as /anyway/anyway in the docker overriding the inner volume and allowing you to run your own code inside the docker.

Questions and ideas
-----------------
Talk to Atalya on HASADNA's Slack (atalya) or email us [anyway@anyway.co.il](mailto:anyway@anyway.co.il).
