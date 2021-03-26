CONFIGURING VSCODE 
==================

In order to debug our flask app using VSCODE python debugger, follow the following steps:

1. Install [VSCODE](https://code.visualstudio.com)
2. In VSCODE Install the following extensions: Microsoft Python Extension](https://github.com/Microsoft/vscode-python), [Docker Extension](https://github.com/microsoft/vscode-docker), [Microsoft Remote Development](https://github.com/Microsoft/vscode-remote-release)
[A guide for installing VSCODE extensions](https://code.visualstudio.com/learn/get-started/extensions)
3. Modify docker-compose.yml: add the following to the ports section in anyway service: `- "5678:5678"` This will add the port mapping exposing it to the debugger.
4. Modify Dockerfile: remove the following command: `CMD FLASK_APP=anyway flask run --host 0.0.0.0` and add the following commands instead:
```
RUN pip install debugpy
CMD FLASK_APP=anyway python -m debugpy --listen 0.0.0.0:5678 -m flask run --host 0.0.0.0 -p 5000
```
5. Add the following configuration to .vscode/launch.json:
```
    "configurations": [
        {       
            "name": "ANYWAY Docker: Python - Flask",
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
    ]
```
6. Run `docker-compose build`
7. Run `docker-compose up`
8. Go to the `RUN` section in VSCODE and choose `ANYWAY Docker: Python - Flask`
9. Happy Debugging!
