import weewx
from weewx.engine import StdService
from pySpacebrew.spacebrew import Spacebrew

import locale
# This will use the locale specified by the environment variable 'LANG'
# Other options are possible. See:
# http://docs.python.org/2/library/locale.html#locale.setlocale
locale.setlocale(locale.LC_ALL, '')

import syslog
#from weeutil.weeutil import timestamp_to_string, option_as_list

# get app name and server from query string
name = "weather station socket service"
server = "weather-sound.herokuapp.com"
port = 443

# configure the spacebrew client
brew = Spacebrew(name=name, server=server, port=port)
brew.addPublisher("loop counter", "range")
# brew.addSubscriber("remote state", "boolean")

# Inherit from the base class StdService:
class SpacebrewSocket(StdService):
    """Service that sends email if an arbitrary expression evaluates true"""
    
    def __init__(self, engine, config_dict):
        # Pass the initialization information on to my superclass:
        super(SpacebrewSocket, self).__init__(engine, config_dict)
        
        
        try:
            self.spacebrewStarted = True
            self.loopCounter = 0

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
            syslog.syslog(syslog.LOG_INFO, "SpacebrewSocket (service) not initialized.  Missing parameter: %s" % e)
    
    def startup(self, event):
        # start-up spacebrew
        try:
            brew.start()
            self.spacebrewStarted = True
        except:
            self.spacebrewStarted = False
            syslog.syslog(syslog.LOG_INFO, "SpacebrewSocket (service) failed to setup socket connection")
            print "Couldn't connect spacebrew for some reason"

    def shutDown(self):
	    brew.stop()
    
    def new_loop_packet(self, event):
        """Gets called on a new loop packet event."""
        self.loopCounter += 1
        self.loopCounter %= 1023

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
        
        try:
            brew.publish('loop counter', self.loopCounter)
        except:
            self.spacebrewStarted = False;

    def newArchiveRecord(self, event):
        """Gets called on a new archive record event."""
        print "archive!!!!!!"
        
        # # To avoid a flood of nearly identical emails, this will do
        # # the check only if we have never sent an email, or if we haven't
        # # sent one in the last self.time_wait seconds:
        # if not self.last_msg_ts or abs(time.time() - self.last_msg_ts) >= self.time_wait :
        #     # Get the new archive record:
        #     record = event.record
            
        #     # Be prepared to catch an exception in the case that the expression contains 
        #     # a variable that is not in the record:
        #     try:                                                              # NOTE 2
        #         # Evaluate the expression in the context of the event archive record.
        #         # Sound the alarm if it evaluates true:
        #         if eval(self.expression, None, record):                       # NOTE 3
        #             # Sound the alarm!
        #             # Launch in a separate thread so it doesn't block the main LOOP thread:
        #             t  = threading.Thread(target = MyAlarm.soundTheAlarm, args=(self, record))
        #             t.start()
        #             # Record when the message went out:
        #             self.last_msg_ts = time.time()
        #     except NameError, e:
        #         # The record was missing a named variable. Write a debug message, then keep going
        #         syslog.syslog(syslog.LOG_DEBUG, "alarm: %s" % e)

    # def soundTheAlarm(self, rec):
    #     """This function is called when the given expression evaluates True."""
        
    #     # Get the time and convert to a string:
    #     t_str = timestamp_to_string(rec['dateTime'])

    #     # Log it
    #     syslog.syslog(syslog.LOG_INFO, "alarm: Alarm expression \"%s\" evaluated True at %s" % (self.expression, t_str))

    #     # Form the message text:
    #     msg_text = "Alarm expression \"%s\" evaluated True at %s\nRecord:\n%s" % (self.expression, t_str, str(rec))
    #     # Convert to MIME:
    #     msg = MIMEText(msg_text)
        
    #     # Fill in MIME headers:
    #     msg['Subject'] = self.SUBJECT
    #     msg['From']    = self.FROM
    #     msg['To']      = ','.join(self.TO)
        
    #     # Create an instance of class SMTP for the given SMTP host:
    #     s = smtplib.SMTP(self.smtp_host)
    #     try:
    #         # Some servers (eg, gmail) require encrypted transport.
    #         # Be prepared to catch an exception if the server
    #         # doesn't support it.
    #         s.ehlo()
    #         s.starttls()
    #         s.ehlo()
    #         syslog.syslog(syslog.LOG_DEBUG, "alarm: using encrypted transport")
    #     except smtplib.SMTPException:
    #         syslog.syslog(syslog.LOG_DEBUG, "alarm: using unencrypted transport")

    #     try:
    #         # If a username has been given, assume that login is required for this host:
    #         if self.smtp_user:
    #             s.login(self.smtp_user, self.smtp_password)
    #             syslog.syslog(syslog.LOG_DEBUG, "alarm: logged in with user name %s" % (self.smtp_user,))
            
    #         # Send the email:
    #         s.sendmail(msg['From'], self.TO,  msg.as_string())
    #         # Log out of the server:
    #         s.quit()
    #     except Exception, e:
    #         syslog.syslog(syslog.LOG_ERR, "alarm: SMTP mailer refused message with error %s" % (e,))
    #         raise
        
    #     # Log sending the email:
    #     syslog.syslog(syslog.LOG_INFO, "alarm: email sent to: %s" % self.TO)