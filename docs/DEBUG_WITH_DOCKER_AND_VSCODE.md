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
