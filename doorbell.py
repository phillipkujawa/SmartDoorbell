import os
import httplib, urllib
import RPi.GPIO as GPIO
import time, sys
import soco
import picamera
import threading
from threading import Thread
from datetime import date
from soco import SoCo
from soco.snapshot import Snapshot
from multiprocessing import Process
from urllib import quote
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import TCPServer
from subprocess import Popen, PIPE, STDOUT,call

redPin = 17
greenPin = 22
bluePin = 27
all_zones = soco.discover()
alert_sound = 'http://192.168.1.243:8080/doorbell.mp3'

class HttpServer(Thread):
    """A simple HTTP Server in its own thread"""

    def __init__(self, port):
        super(HttpServer, self).__init__()
        self.daemon = True
        handler = SimpleHTTPRequestHandler
        self.httpd = TCPServer(("", port), handler)

    def run(self):
        """Start the server"""
        print('Start HTTP server')
        self.httpd.serve_forever()

    def stop(self):
        """Stop the server"""
        print('Stop HTTP server')
        self.httpd.socket.close()

server = HttpServer(8080)
server.start()

# setting code for colors, can customize for your own colours
# output uses GPIO.LOW because my LED is an anode

def turnOn(pin):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)


def turnOff(pin):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)


def cyanOn():
    turnOn(greenPin)
    turnOn(bluePin)
    turnOff(redPin)


def whiteOn():
    turnOn(redPin)
    turnOn(greenPin)
    turnOn(bluePin)




# Below is the pushover code for push notifications
def PushOver(title, message, url):
    app_key = "a8jffoujd1cuj59pgfroy9kqsjdonr"
    user_key = "usfn4p8gvhmg6m95azdm1fzdkdaqea"
    # Connect with the Pushover API server
    conn = httplib.HTTPSConnection("api.pushover.net:443")
    
    # Send a POST request in urlencoded json
    conn.request("POST", "/1/messages.json",
                 urllib.urlencode({
                     "token": app_key,
                     "user": user_key,
                     "title": title,
                     "message": message,
                     "url": url,
                 }), {"Content-type": "application/x-www-form-urlencoded"})
    
    # Any error messages or other responses?
    conn.getresponse()


# Sonos code is here for snapshot activating speakers for doorbell
def play_alert(zones, alert_uri, alert_volume=35, alert_duration=0, fade_back=False):
    # Use soco.snapshot to capture current state of each zone to allow restore
    for zone in zones:
        zone.snap = Snapshot(zone)
        zone.snap.snapshot()
        print('snapshot of zone: {}'.format(zone.player_name))
    
    # prepare all zones for playing the alert
    for zone in zones:
        # Each Sonos group has one coordinator only these can play, pause, etc.
        if zone.is_coordinator:
            if not zone.is_playing_tv:  # can't pause TV - so don't try!
                # pause music for each coordinators if playing
                trans_state = zone.get_current_transport_info()
                if trans_state['current_transport_state'] == 'PLAYING':
                    zone.pause()
        
        # For every Sonos player set volume and mute for every zone
        zone.volume = alert_volume
        zone.mute = False
    
    # play the sound (uri) on each sonos coordinator
    print('will play: {} on all coordinators'.format(alert_uri))
    for zone in zones:
        if zone.is_coordinator:
            zone.play_uri(uri=alert_uri, title='Sonos Alert')
    
    # wait for alert_duration
    time.sleep(alert_duration)
    
    # restore each zone to previous state
    for zone in zones:
        print('restoring {}'.format(zone.player_name))
        zone.snap.restore(fade=fade_back)



# doorbell sound play through sonos
def play_doorbell():
    # alert uri to send to sonos - this uri must be available to Sonos
    play_alert(all_zones, alert_sound, alert_volume=30, alert_duration=2, fade_back=False)
d = threading.Thread(name='doorbell', target=play_doorbell)

# pushover notification
def notification_pushover():
    PushOver('Doorbell', 'Someone is  at the door!', 'https://fixnode.ca:8080')

# before using this function you must make sure that you already registered your sip account
# in file ~./linphonec
# this fnc is used to make linphone call using sip username

def LinphoneVoIP_Call(userid):
    # global p2, p3
    call(['killall', 'linphonec'])
    # global lines,callstatus
    notification_pushover()
    callstatus = ['@sip.linphone.org ringing',
                  '@sip.linphone.org connected',
                  '@sip.linphone.org ended ',
                  '@sip.linphone.org error']
    lines = []
    domain = '@sip.linphone.org'
    account = 'sip:' + userid + domain
    command = 'call ' + account
    p = Popen(['./linphonec'], cwd='/home/pi/linphone-desktop/OUTPUT/no-ui/bin/', stdin=PIPE,
              stdout=PIPE, stderr=STDOUT, bufsize=1)

    p.stdin.write(command)
    
    p.stdin.close()
    for line in iter(p.stdout.readline, b' '):  # newline=b'\n'
        lines.append(line)  # capture for later
        
        # CHECK IF RINGING
        if line.find(str(callstatus[0])) is not -1:
            print ('RINGING.....')
        
        # CHECK IF CALL CONNECTED
        if line.find(str(callstatus[1])) is not -1:
            print ('CALL Connected to ' + userid)
            
        # CHECK CALL ENDED
        if line.find(str(callstatus[3])) is not -1 or line.find(str(callstatus[2])) is not -1:
            print 'Call ended or not initiated'
            break
    
    p.stdout.close()
    p.terminate()
    p.wait()

def call_phone():
    LinphoneVoIP_Call('philkuj')

def take_video():
    counter = 0
    filename = "video{}.h264"
    while os.path.isfile(filename.format(counter)):
            counter += 1
    filename = filename.format(counter)
    camera.start_recording(filename)
    camera.wait_recording(15)
    camera.stop_recording()


def SysInit():
    # switch pins set using built in pull up resistor plus a hardware 10K resistor to ground
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    PushOver('Doorbell', 'Started', '')
    print 'Doorbell Server Started\r'

if __name__ == '__main__':
    try:
        SysInit()
        whiteOn()
        camera = picamera.PiCamera()
        camera.resolution = (1640, 1232)
        while True:
            input_state = GPIO.input(23)
            if input_state == False:
                print('Someone is at the door!\r')
                cyanOn()
                # sonos play sound for doorbell, calling sip phone and push notification
		play_doorbell()
                # make SIP call using linphone
		call_phone()
		take_video()
 		whiteOn()
            time.sleep(0.01)
    except KeyboardInterrupt:
        server.stop()
        GPIO.cleanup()
