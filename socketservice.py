import weewx
from weewx.engine import StdService
import websocket
import threading
import time
import json
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


import locale
# This will use the locale specified by the environment variable 'LANG'
# Other options are possible. See:
# http://docs.python.org/2/library/locale.html#locale.setlocale
locale.setlocale(locale.LC_ALL, '')

import syslog
#from weeutil.weeutil import timestamp_to_string, option_as_list

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
            # self.spacebrewStarted = True
            self.loopCounter = 0
            self.latestData = None
            self.ws = None
            self.started = False

            # # Dig the needed options out of the configuration dictionary.
            # # If a critical option is missing, an exception will be raised and
            # # the alarm will not be set.
            # self.expression    = config_dict['Alarm']['expression']
            # self.time_wait     = int(config_dict['Alarm'].get('time_wait', 3600))
            # self.smtp_host     = config_dict['Alarm']['smtp_host']
            # self.smtp_user     = config_dict['Alarm'].get('smtp_user')
            # self.smtp_password = config_dict['Alarm'].get('smtp_password')
            # self.SUBJECT       = config_dict['Alarm'].get('subject', "Alarm message from weeWX")
            # self.FROM          = config_dict['Alarm'].get('from', 'alarm@example.com')
            # self.TO            = option_as_list(config_dict['Alarm']['mailto'])
            # syslog.syslog(syslog.LOG_INFO, "alarm: Alarm set for expression: '%s'" % self.expression)
            
            # If we got this far, it's ok to start intercepting events:
            self.bind(weewx.STARTUP, self.startup)
            self.bind(weewx.NEW_ARCHIVE_RECORD, self.newArchiveRecord)    # NOTE 1
            self.bind(weewx.NEW_LOOP_PACKET, self.new_loop_packet)
        except KeyError, e:
            syslog.syslog(syslog.LOG_INFO, "Socket service not initialized.  Missing parameter: %s" % e)
    
    def create_socket_thread(self):
        def run(*args):
			self.run()
        
        try:
            self.thread = threading.Thread(target=run)
            self.thread.start()
            self.started = True
        except:
            # self.spacebrewStarted = False
            syslog.syslog(syslog.LOG_INFO, "socket service failed to setup socket connection")
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
        self.loopCounter += 1
        self.loopCounter %= 1023

        self.latestData = json.dumps(event.packet)

        # if not self.spacebrewStarted:
        #     try:
        #         brew.addPublisher("loop counter", "range")
        #         brew.start()
        #         self.spacebrewStarted = True
        #     except:
        #         self.spacebrewStarted = False
        #         syslog.syslog(syslog.LOG_INFO, "SpacebrewSocket (service) failed to setup socket connection")
        #         print "Couldn't connect spacebrew for some reason"
        #         return
        if self.ws is None:
            self.thread.join()
            self.create_socket_thread()
            return

        
        try:
            self.ws.send(self.latestData)
        except:
            pass

    def newArchiveRecord(self, event):
        """Gets called on a new archive record event."""
        print "archive!!!!!!"

    
    def on_message(self, ws, message):
        print(message)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        print("### closed ###")

    def on_open(self, ws):
        print('### opened ###')
