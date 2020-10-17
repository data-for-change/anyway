# Instructions
1. Watch the following video: https://www.youtube.com/watch?v=b78Tg-YmJZI and do as it says
2. Add this line in the dockerfile: ENV FLASK_DEBUG=0
3. Change the line:
```CMD python -m ptvsd --host 0.0.0.0 --port 5678 --wait --multiprocess -m flask run -h 0.0.0 -p 5000```
to ```CMD python -m ptvsd --host 0.0.0.0 --port 5678 --wait --multiprocess -m flask run -h 0.0.0.0 -p 5000```
4. Comment the lines ```ENTRYPOINT ["/anyway/docker-entrypoint.sh"]``` and ```CMD FLASK_APP=anyway flask run --host 0.0.0.0 ```

5. in launch.json add the following code:

  ```
  {
  
    "version": "0.2.0",
    "configurations": [
        {       
            "name": "Python Attach",
            "type": "python",
            "request": "attach",
            
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}/",
                    "remoteRoot": "/anyway"
                }
            ],
            "port": 5678,
            "host": "127.0.0.1"
        }
  ```
 
 #### Note: everytime you change something in dockerfile you have to rebuild the docker using the command:
 `sudo docker-compose build`
 
6. in docker-compose.yaml there is this code:
```
ersion: '3'

services:
  anyway:
    build: .
    image: docker.pkg.github.com/hasadna/anyway/anyway:latest
    container_name: anyway
    ports:
      - "8080:5000"
    environment:
      - DATABASE_URL=postgresql://anyway:anyway@db/anyway
      - FLASK_ENV=development
    volumes:
      - .:/anyway
    restart: always
    depends_on:
      - db

  db:
    build: db_docker
    image: docker.pkg.github.com/hasadna/anyway/db:latest
    container_name: db
    environment:
      - DBRESTORE_AWS_ACCESS_KEY_ID
      - DBRESTORE_AWS_SECRET_ACCESS_KEY
    volumes:
      - db_data:/var/lib/postgresql/data
    ports:
      - "9876:5432"
    restart: always

volumes:
  db_data:
```
comment this line:`image: docker.pkg.github.com/hasadna/anyway/anyway:latest` in anyway container
