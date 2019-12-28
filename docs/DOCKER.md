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

Read more on the docker [Github project] (https://github.com/docker/docker)


Instructions
-----------------------
* Please complete ANYWAY’s [“getting the code” section] (https://github.com/hasadna/anyway#getting-the-code-and-adding-ci-to-your-forked-repository) before starting

**1.** [Get the code] (https://github.com/hasadna/anyway#getting-the-code-and-adding-ci-to-your-forked-repository)

**2.** [Install Docker] (https://docs.docker.com/install/)

**3.** Open "Docker terminal", go to the **anyway** directory and run:
    `docker-compose up -d db`
    
**4.** start anyway container: `docker-compose up -d`

**5.** while docker is running, run the following command to populate data (from 2014) `docker exec -i -t anyway_anyway_1 python main.py process cbs`

**6.** **You're all set!** ANYWAY is up and running - connect to http://127.0.0.1:8080 and change dates to 2014 in order to see accidents

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
