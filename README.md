# SmartDoorbell
Doorbell software built for a Raspberry Pi. Integrates using SIP (Linphone), Sonos speakers using SoCo (https://github.com/SoCo/SoCo) and Picamera 1.13 (https://github.com/waveform80/picamera). 

Prerequisites:
  - Enable IPv6
    - echo ipv6 >> /etc/modules
  - Check if IPv6 is enabled
    - sudo nano /etc/modules
  - Reboot
    - sudo reboot
  - Install dependencies
    - sudo apt-get install cmake automake autoconf libtool intltool yasm libasound2-dev libpulse-dev libv4l-dev nasm git libglew-dev
    - git clone git://git.linphone.org/linphone-desktop.git --recursive
  - Compile dependencies
    - cd linphone-desktop
    - ./prepare.py no-ui -DENABLE_OPENH264=ON -DENABLE_WEBRTC_AEC=OFF -DENABLE_UNIT_TESTS=OFF -DENABLE_MKV=OFF -DENABLE_FFMPEG=ON -DENABLE_CXX_WRAPPER=OFF -DENABLE_NON_FREE_CODECS=ON -DENABLE_VCARD=OFF -DENABLE_BV16=OFF -DENABLE_V4L=OFF
    - make -j4
    - mkdir /home/pi/.local/share/linphone/
 - Check directory to confirm if everything is installed correctly
    - cd linphone-desktop/OUTPUT/no-ui/bin
    - For PSTN calls please use a SIP Provider with Linphone (Recommended: Telnyx - https://telnyx.com/)
    
 - Account Registration
    - cd linphone-desktop/OUTPUT/no-ui/bin 
    - ./linphonec
    - enter proxy sip address: sip:sip.linphone.org;transport=tls
    - enter your identity for this proxy: sip:SIPUSERNAME@sip.linphone.org
    - do you want to register on this proxy (yes/no): yes
    - specify register expiration time in seconds (default is 600): (PRESS ENTER LEAVE DEFAULT VALUE)
    - accept the above proxy configuration (yes/no) ?: yes
    - password for SIPUSERNAME on sip.linphone.org: PASSWORD1234
    - proxy list
    
****** Proxy 0 - this is the default one - ******
sip address: <sip:sip.linphone.org;transport=tls>
route: 
identity: sip:SIPUSERNAME@sip.linphone.org
register: yes
expires: 600
registered: yes

If you see the above example and it registers successfully then you've completed the prerequisite steps successfully.
