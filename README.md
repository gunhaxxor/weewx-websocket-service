# weewx-websocket-service
A weewx service for pushing LOOP data to a websocket server

# Installation
You will need to install the required python packages yourself if they are not already on your system. I did it with pip. They are:
- websocket (`>pip install websocket-client`)
- threading
- json
- dotenv (`>pip install python-dotenv`)

Place the repository in **weewx/bin/user/**

Change **weewx.conf** by adding the bold part to the following line:

`report_services = `**`user.weewx-websocket-service.socketservice.SocketService`**`, weewx.engine.StdPrint, weewx.engine.StdReport`
