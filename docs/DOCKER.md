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
* **For Windows users please first install ubuntu VM**. See [UBUNTU_VM_ON_WINDOWS](UBUNTU_VM_ON_WINDOWS.md)

* Please complete ANYWAY’s [“getting the code” section](https://github.com/hasadna/anyway#getting-the-code) before starting

**1.** [Get the code](https://github.com/hasadna/anyway#getting-the-code)

**2.** [Install Docker](https://docs.docker.com/install/) and [Install Docker Compose](https://docs.docker.com/compose/install/)

**3.** Get the `.env` file with the required secret values and place in the project **root directory** - can be downloaded [from here](https://drive.google.com/file/d/1WA_B3Qo5xgf2Zt_tVNjnSK2VONqQ1ZYD/view?usp=sharing). Note that this file **needs to be saved as `.env`** - with the `.` at the beginning of the name of the file.
**Continue with your OS, See below**

**For Mac:**

**4.** If this is your first time installing ANYWAY Docker environment - move on to stage 5.
Otherwise, to build an existing environment with the most updated DB, remove DB volume by running `docker volume rm anyway_db_data`.
Note - this will delete all of your local DB data!

**5.** Anyway images stored on github package, to be able to pull the images you need to login to github using docker login.
if you already logged in with docker to github source jump to the next step.

#### **docker login**
First, to login to github go to [this link](https://github.com/settings/tokens) of your github account and generate token with `read:packages` permission.

Second, copy the token that you just generate and run docker login command like this when `USERNAME` is your github username, and paste the token when prompt will ask the password.
```bash
$ docker login docker.pkg.github.com -u USERNAME 
```

**6.** Go to the project's root directory and run:
    `sudo docker-compose up -d`
This will start the containers. It will take a few minutes until it's done.

**7.** **You're all set!** ANYWAY is up and running with the DB data - connect to http://127.0.0.1:8080
Note - you won't see the map since the key works in production.
If you need to see the map contact atalya via slack to get a developer key.  
The developer key need to replace the production key in the file /anyway/blob/dev/templates/index.html where you can find: "https://maps.googleapis.com/maps/api/js?key=AIzaSyDUIWsBLkvIUwzLHMHos9qFebyJ63hEG2M&libraries=places,visualization&language=iw" (google maps url)
So if the developer key is "12345" the new url need to be is: "https://maps.googleapis.com/maps/api/js?key=12345&libraries=places,visualization&language=iw"

**8.** To stop the containers run: `docker-compose down`

**9.** To restore fresh DB data, delete all existing volumes: `docker-compose down -v` then restart from step 7 

**For Ubuntu:**

**4.** If this is your first time installing ANYWAY Docker environment - move on to stage 5.
Otherwise, to build an existing environment with the most updated DB, remove DB volume by running `sudo docker volume rm anyway_db_data`.
Note - this will delete all of your local DB data!

**5.** Anyway images stored on github package, to be able to pull the images you need to login to github using docker login.
if you already logged in with docker to github source jump to the next step.

#### **docker login**
First, to login to github go to [this link](https://github.com/settings/tokens) of your github account and generate token with `read:packages` permission.

Second, copy the token that you just generate and run docker login command like this when `USERNAME` is your github username, and paste the token when prompt will ask the password.
```bash
$ docker login docker.pkg.github.com -u USERNAME 
```

**6.** Go to the project's root directory and run:
    `sudo docker-compose up -d`
This will start the containers. It will take a few minutes until it's done.

**7.** **You're all set!** ANYWAY is up and running with the DB data - connect to http://127.0.0.1:8080
Note - you won't see the map since the key works in production.
If you need to see the map for development email us [anyway@anyway.co.il](mailto:anyway@anyway.co.il) to get a developer key.  
The developer key need to replace the production key in the file /anyway/blob/dev/templates/index.html where you can find: "https://maps.googleapis.com/maps/api/js?key=AIzaSyDUIWsBLkvIUwzLHMHos9qFebyJ63hEG2M&libraries=places,visualization&language=iw" (google maps url)
So if the developer key is "12345" the new url need to be is: "https://maps.googleapis.com/maps/api/js?key=12345&libraries=places,visualization&language=iw"

**7.** To stop the containers run: `sudo docker-compose down`

**8.** To restore fresh DB data, delete all existing volumes: `docker-compose down -v` then restart from step 7

## Additional Docker commands
Use `sudo` before each docker commands if you are using ubuntu.

To install requirements again, update DB schema OR redeploy any of the requirement involving the dependencies installation,
simply rebuild the image - Run in anyway directory:

    docker-compose build

Run docker-compose in detached mode - containers are running in background:

    docker-compose up -d

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

For example - to open the bash terminal of the db container:

    docker exec -it db bash

For example - to open the bash terminal of the anyway container:

    docker exec -it anyway bash

Inside the bash terminal of anyway container - run the following to use postgres command line:

    psql $DATABASE_URL

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


Testing production environment locally
--------------------------------------

This process allows to emulate a full production environment locally for testing. This is an advanced operation and not needed for normal development.

Create a .env file for production (set relevant values):

```
# app env vars
DATABASE_URL=postgresql://anyway:12345678@db/anyway
GOOGLE_MAPS_KEY=
TWITTER_CONSUMER_KEY=
TWITTER_CONSUMER_SECRET=
TWITTER_ACCESS_KEY=
TWITTER_ACCESS_SECRET=
FACEBOOK_KEY=
FACEBOOK_SECRET=
GOOGLE_LOGIN_CLIENT_ID=
GOOGLE_LOGIN_CLIENT_SECRET=
MAILUSER=
MAILPASS=
GOOGLE_APPLICATION_CREDENTIALS=/secrets/GOOGLE_APPLICATION_CREDENTIALS_KEY.json
GOOGLE_APPLICATION_CREDENTIALS_HOST_PATH=/host/path/to/google_application_credentials.json
APP_SECRET_KEY=

# db env vars
POSTGRES_USER=postgres
POSTGRES_PASSWORD=123456
POSTGRES_DB=postgres
#   aws access/secret with permissions to read from full db dumps bucket
DBRESTORE_AWS_ACCESS_KEY_ID=
DBRESTORE_AWS_SECRET_ACCESS_KEY=
DBRESTORE_AWS_BUCKET=anyway-full-db-dumps
DBRESTORE_FILE_NAME=2020-06-09_anyway.pgdump
#   should match the password set in app env vars
DBRESTORE_SET_ANYWAY_PASSWORD=12345678

# db-backup env vars
DBDUMP_S3_FILE_PREFIX=testing_
#   aws access/secret with permissions to write to both full and partial db dumps buckets
DBDUMP_AWS_ACCESS_KEY_ID=
DBDUMP_AWS_SECRET_ACCESS_KEY=
#   db connection details to the postgres user
DBDUMP_USER=postgres
DBDUMP_PASSWORD=123456
DBDUMP_HOST=db
```

Create a shell alias to run docker-compose for production

```
alias docker-compose-prod="docker-compose -f docker-compose.yml -f docker-compose-production.override.yml"
```

Restore the DB

```
docker-compose-prod down -v
docker-compose-prod up --build db
```

Start the app

```
docker-compose-prod up --build nginx anyway
```

Access the app at http://localhost:8000

Run the backup job

```
docker-compose-prod build db-backup
docker-compose-prod run db-backup
```
