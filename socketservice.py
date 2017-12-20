import weewx
from weewx.engine import StdService
import websocket
import threading
import json
import os
from dotenv import load_dotenv, find_dotenv

#inject variables from .env-file
load_dotenv(find_dotenv())


import locale
# This will use the locale specified by the environment variable 'LANG'
# Other options are possible. See:
# http://docs.python.org/2/library/locale.html#locale.setlocale
locale.setlocale(locale.LC_ALL, '')


# We need some environment variables to set the right properties of the websocket connection
# You can set them by using an .env-file. I'm making use of the dotenv package to inject them into the service

# clienttoken sets a tokenstring as a part of the initial connection request.
# server is websocket server. Either 'wss://blabla' for encrypted or 'ws://blabla' for unencrypted
# port is a port. Remember that some port ranges not are allowed in some environments (like chrome for example)
# These variables are used like this 'server:port?token=clientToken' when the service tries to create a websocket connection
clientToken = os.environ.get('WEATHERSTATIONTOKEN') 
server = os.environ.get('SERVER')
port = os.environ.get('PORT')

# Inherit from the base class StdService:
class SocketService(StdService):
    """Service that sets up a websocket and emits weather loop data to it"""
    
    def __init__(self, engine, config_dict):
        # Pass the initialization information on to my superclass:
        super(SocketService, self).__init__(engine, config_dict)
        
        
        try:
            self.latestData = None
            self.ws = None
            self.started = False

            self.bind(weewx.STARTUP, self.startup)
            self.bind(weewx.NEW_LOOP_PACKET, self.new_loop_packet)
        except:
            print "failed to initialize the websocket service"
    
    def create_socket_thread(self):
        def run(*args):
			self.run()
        
        try:
            self.thread = threading.Thread(target=run)
            self.thread.start()
            self.started = True
        except:
            print "Couldn't connect for some reason"

    def run(self):
		self.ws = websocket.WebSocketApp( server + ':' + str(port) + '?token=' + clientToken,
						on_message = lambda ws, msg: self.on_message(ws, msg),
						on_error = lambda ws, err: self.on_error(ws,err),
						on_close = lambda ws: self.on_close(ws) )
		self.ws.on_open = lambda ws: self.on_open(ws)
		self.ws.run_forever()
		self.ws = None

    def startup(self, event):
        # websocket.enableTrace(True)
        self.create_socket_thread()

    def shutDown(self):
        print('closing socket service')
		
        if self.ws is not None:
			self.ws.close()
		
        self.thread.join()
        self.started = False
    
    def new_loop_packet(self, event):
        """Gets called on a new loop packet event."""

        self.latestData = json.dumps(event.packet)

        if self.ws is None:
            self.thread.join()
            self.create_socket_thread()
            return

        
        try:
            self.ws.send(self.latestData)
        except:
            pass

    # def newArchiveRecord(self, event):
    #     """Gets called on a new archive record event."""
    #     print "archive!"

    
    def on_message(self, ws, message):
        print(message)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        print("### websocket closed ###")

    def on_open(self, ws):
        print('### websocket opened ###')
