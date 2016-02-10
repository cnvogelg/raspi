# pifon2
## the next generation baby monitor for your Raspis

## 1. Introduction

### 1.1 Overview

pifon is a baby monitor application that uses two Raspis to detect audio
events in a baby's room and report them to the caring parents in another
room.

One Raspi in the baby's room is the pifon server (called pifon **fon**) that
continously records an audio stream and watches there for events, i.e.
intervals with high audio activity. If an audio event is detected then it is
reported to the other Raspi, the client (called pifon **mon**). The mon then
signals the audio event in its user interface and starts streaming the audio
stream from the baby's room until the audio level returns to silence again.

### 1.2 System Design

pifon uses available technlogies whenever possible. Therefore the
communication between fon and mon uses then chat protocol XMPP (aka Jabber).
So both fon and mon are implemented as chat bots that simply talk their
events to a chat room and listen out for events there. Nice side effect here
is that you can use a chat client to monitor the events and even inject your
own by simply chatting with the bots.

We use the [prosody][1] XMPP server in a local installation. The bots are
implemented in Python 2.7 and use the [sleekxmpp][2] library.

Audio streaming also relies on well established techniques: The fon server
runs an [Icecast2][3] audio streaming server that locally feeds in the recorded
microphone stream with the [darkice][4] server. On the mon/client side the
[Music Player Daemon][5] is used.

The mon uses a small [16x2 character LCD display from Adafruit][6] to display
all events and status information. Furthermore, the display hardware offers a
set of five buttons that allow you to control the behavior of the mon. If you
do not have a LCD then you can run the mon with a LCD simulator. It renders
the LCD display with PyGame library on any SDL supported display. Use this to
run mon on your desktop PC.

However, the system is very flexible, i.e. you can easily replace the way the
audio is played back or streamed or you can even write your own UI that uses
another way of displaying the audio events.

[1]: http://prosody.im
[2]: http://sleekxmpp.com
[3]: http://icecast.org
[4]: http://www.darkice.org
[5]: http://www.musicpd.org
[6]: https://learn.adafruit.com/adafruit-16x2-character-lcd-plus-keypad-for-raspberry-pi/overview

### 1.3 System Diagram

```
---------- fon ----------

                  +----> event detector -----> XMPP bot ------> prosody
Mic               |                                             chat room
*=== --> audio ---+
         record   |
                  +----> darkice ------------> Icecast2 <------ incoming
                         record/encode         stream           connect
                         stream                server           from mon

---------- mon ----------

prosody ---------> XMPP bot ----+---------> show events in UI/LCD
chat room                       |
                                v control player
connect <--------------------- MPD -------> play to speaker
to fon
Icecast2
```


## 2. Installation

### 2.1 Required Hardware

* Two Raspberry Pis
  - I use classic Model B, but newer ones like B+ or B2 should work, too
  - Model B is recommended since networking is required
* A Microphone
  - Either a USB Webcam with a microphone
  - Or a USB Soundcard with microphone input
* A LCD Display
  - I use the [Adafruit 16x2 Character LCD + Keypad for Raspberry Pi][1]
* A PC/Mac (optional)
  - use it to setup the system
  - run mon with LCD simulator

[1]: https://www.adafruit.com/products/1110

### 2.2 Required Software

* Raspbian Lite
  - Since **Jessie** Raspbian ships a Lite release that fits on a 2GB SD card.
    I prefer this one as it avoids the bloat of UI software found on the
    regular edition

  - Some extra pacakges are required on both Pis:

```
# apt-get install tmux git
```

  - I assume you have the base Raspbian system already installed and
    configured.

  - I typically add an own user on my Pis (called **chris**) and run the
    applications. I assume that this user is used in this installation but
    you may also use the default user **pi** for this.

### 2.3 Running on Mac OS X

* I use my Mac to test the components locally and run the **mon** with the
  LCD simulator there

* In order to do so, you have to install some extra components
  - I use [MacPorts][1] to manage my packets
* Install **Python 2.7**
```
# port install python27
# port select --set python2 python27
# port install py27-game
# port install py27-pip
```
* Install **tmux**
```
# port install tmux
```

[1]: https://www.macports.org

### 2.4 Runnnin on Ubuntu

* If you want to run the components on your PC with Ubuntu then install the
  following

```
# apt-get install python-pygame tmux python-pip
```


## 3. Setting up the XMPP Infrastructure

Before pifon can communicate with each components we first have to setup a
local XMPP server (here prosody), add users and setup the XMPP Python library
on all clients.

## 3.1 Prosody Setup

The XMPP server can either run on one of the two Raspis or can run also on
a third machine in your network. The latter approach is recommended if you
have already a LAN server running.

### Server Setup

* First install prosody with the corresponding package
```
# apt-get install prosody
```

* Configure prosody by creating **/etc/prosody/conf.d/pifon.cfg.lua**
```
VirtualHost "coin.local"

  enabled = true
  allow_registration = true
  disallow_s2s = true

Component "muc.coin.local" "muc"
```

* One important thing to **Note** here is the domain of the virtual host. I
  use the name of my server here that runs prosody (Its called **coin** and is
  locally reachable via **coin.local**). Be sure to use your hostname there
  and adjust the entries in the following installation guide. You may use an
  arbitrary name like **pifon.local** here, but you must ensure that all
  clients can resolve this name e.g. via DNS.

* Restart prosody
```
# /etc/init.d/prosody restart
```

* Watch the server log if everything went well
```
# tail -f /var/log/prosody/prosody.log
```

### Add Users

Each pifon component (mon and fon) is an XMPP bot that logs into the XMPP
server by using a username (here JID) and password. You have to add those
users now to your prosody setup and assign passwords. The passwords are
stored in the configuration files of pifon.

I suggest to add a user **fon** and **mon** for the corresponding components.
To keep things simple (and since we are local) I use the same entries as
password:

```
# prosodyctl adduser fon@coin.local
; use "fon" as a password
# prosodyctl adduser mon@coin.local
; use "mon" as password
```

Note: Always use the at-prefix with your XMPP domain name setup above (here
**@coin.local**)

Its very handy to also add a user for yourself that can be used inside your
chat program to sniff the events send on this room:

```
# prosodyctl adduser chris@coin.local
; give a handy password
```

### Test Setup

Best way to test your new XMPP server setup is to use a PC/Mac and a chat
client to connect the server.

On my Mac I use [Adium][1], on Ubuntu you may use [Pidgin][2].

In Adium use the following setps:

- add a new XMPP user account ``<user>@coin.local`` with own ``<password>``.
  Use the parameters set in the step above

- In the new account menu entry select **Show Services...**
- Open "coin.local" entry and double click on the "muc.coin.local" service
- There the chat rooms will be located. Later on the pifon bots will create
  a **pifon** chat room automatically. But for now we have to do it manually:
- In the dialog enter room name **pifon** and a user handle you want to use
  in this room. This could be your username but can also differ if you want.
- A chat window will open and you can start talking to yourself as no bot
  is currently running :) Keep the window open as we will use it in a minute
  to see our bot running.

[1]: https://adium.im
[2]: https://www.pidgin.im

## 3.2 Client Bot Setup

Now we setup the XMPP clients on both Raspis so that the pifon bot can be
run on both ends.

First we need to install the SleekXMPP library and then we run a simple test
bot to see if everything works.

### SleekXMPP Installation

SleepXMPP can be easily setup with PIP (be sure to run it as root):

```
# apt-get install python-pip
# pip install sleekxmpp
```

To test the library launch your Python 2.7 and try to import the lib:

```
> python
import sleekxmpp
exit()
```

If the import command returns without an error then the library was installed
successfully.

### Run the Test Bot

Now that the library is in place, we can test if a simple test bot shipped
with the pifon source code runs.

Enter the **tools** directory of the source tree and run the **test_xmppbot**
script there:

```
cd tools
./test_xmppbot
```

Please note that the test bot reads the configuration file called **sample.cfg**
in the same directory. There you have to adjust the user/password and domain
name if you use a different setup:

```
[xmppbot]
jid = client@coin.local
password = client
room = pifon@muc.coin.local
nick = sample
```

Replace **coin.local** with your prosody domain and replace **client** user
and passwort if you setup other users in your server.

The bot will start up and start logging its events on the console.

Now use your PC chat client you already setup and watch out for a new chat
member called **sample@host** with host being the hostname where you run
the test bot.

You can talk with the bot by chatting:

```
bot lsmod
```

The bot will reply with its modules:

```
sample@ridcully
chris|bot.event module test 1.0
chris|bot.event module echo 1.0
chris|bot.event end_module
```

Note that the bots will prefix a **user|** to every message that is addressed
to a single receiver (albeit all will read it - its a chat romm)

Use Ctrl-C to abort the running bot. The bot will then disappear from the
chat room.


## 4. Audio Setup

In this section we will setup and configure audio processing on both clients.

The **fon** Raspi will use its microphone to capture audio and we install an
audio streaming server there.

The **mon** Raspi will setup its audio playback and the MPD for music play
back.

### 4.1 Mic Setup on fon Raspi

#### Microphone Setup in ALSA

* Attach your USB Soundcard/Webcam and setup your microphone

* Run ALSAs ``arecord`` to find the ALSA device of your mic

```
> arecord -l
**** Liste der Hardware-Geräte (CAPTURE) ****
Karte 1: U0x46d0x819 [USB Device 0x46d:0x819], Gerät 0: USB Audio [USB Audio]
  Sub-Geräte: 0/1
  Sub-Gerät #0: subdevice #0
```

  - Ok: card 1, device 0 (hw1,0 in ALSA speak) is our mic

* First use the ALSA mixer to tune your recording level (I put mine to 100%):

```
> alsamixer -c 1 -V capture
```

* Now create a new ALSA device called **mixin** that allows multiple clients
  to share the single mic source. We need this so that both the audio detector
  and the audio streamer can use the mic.

  - As root create a file called ``/etc/asound.conf``:
```
pcm.mixin {
       type dsnoop
       ipc_key 12345
       ipc_key_add_uid yes
       slave {
               pcm "hw:1,0"
       }
}
```
  - Note: you need to adjust **hw:1,0** if your mic is another ALSA device!

  - arecord should list the new device now:
```
> arecord -L | grep mixin
mixin
```

* As a quick test of your setup you can run arecord and look at the VU meter
  if you talk into your mic:

```
> arecord -D mixin -V mono -f S16_LE /dev/null
```

#### Setup pifon's VUmeter

pifon uses a small skript called **vumeter** that records audio from the
newly created **mixin** device and derives a single loudness value every
few microseconds. This vumeter is used in the bot to decide when an audio
alarm has to be triggered.

* First we need to install [SoX][1] as we use it for recording and audio
  processing.

```
# apt-get install sox
```

* A small helper program shipped with pifon called **rms** needs to be
  compiled:

```
> cd pifon/fon/tools
> make
```
  - This assumes that your Raspi installation is able to compile some C code.
    But this is usually the case (even on the Lite release)

* Now you are ready to test the **vumeter** script:

```
> cd pifon/fon/tools
> ./vumeter
```

  - Now every few milliseconds a line with a loudness value is written.
    If you make more noise then this value will increase.

* Ok, audio is now setup for pifon use!


### 4.2 Setup Stream Server on fon Raspi

For a working audio streaming server that records local mic audio we need
two ingredients: First the darkice tool that records the live audio from the
mic and creates a compressed audio stream and then a streaming server that
provides these streams to external players.

#### Darkice Installation

* Install darkice package
```
# apt-get install darkice
```

* Find the default sample rate of your device
```
# arecord --dump-hw-params -D mixin 2>&1 | grep RATE
RATE: 480000
```

* Configure DarkIce and create ``/etc/darkice.cfg``:
```
[general]
duration        = 0        # duration of encoding, in seconds. 0 means forever
bufferSecs      = 1        # size of internal slip buffer, in seconds
reconnect       = yes      # reconnect to the server(s) if disconnected

[input]
device          = mixin     # use my ALSA device
sampleRate      = 48000     # use sample rate determined above
bitsPerSample   = 16        # bits per sample. try 16
channel         = 1         # channels. 1 = mono, 2 = stereo

[icecast2-0]
bitrateMode     = vbr
format          = mp3
quality         = 0.6
server          = localhost
port            = 8000
password        = hackme
mountPoint      = pifon
name            = baby@pifon
description     = The live stream from baby's room
url             = http://pifon.local:80/
genre           = baby
public          = no
highpass        = 500
```
  - adjust ``format = vorbis`` if using the OGG darkice
  - adjust ``url`` to match your pi's host name. This URL is only for
    advertising your audio stream and not required for normal operation.

* You can test drive darkice manually with:
```
> sudo darkice
```
  - It will start without errors and wait for stream requests

#### Icecast2 Installation

* Install Icecast2 package
```
# apt-get install icecast2
Config? -> Yes
Hostname? -> your hostname
Set passwords
```

* You can tune icecast by omitting the audio burst at the begin of a stream
  to speed up connection time:

  - edit ``/etc/icecast2/icecast.xml`` set burst on connect to 0 and comment
    out burst size:
```
<burst-on-connect>0</burst-on-connect>
<!-- <burst-size>65535</burst-size> -->
```
  - restart service
```
service icecast2 start
```

#### Test Stream Server with PC

* First run darkice manually on your fon Raspi:
```
> sudo darkice
```
* Icecast2 should be already running on fon Raspi.

* With a web browser on your PC access the Icecast page: ``http://fozzie.local:8000``.
  - Note: ``fozzie``is the hostname of the fon Raspi
  - You should see a web page announcing our darkice **pifon** mount point
  - If you click on the **M3U** icon your media-enabled browser should start
    streaming the audio from the fon Pi.

* Now use a streaming capable media player on your PC to connect to the stream.
  - It uses directly the stream URL: ``http://fozzie.local:8000/pifon``
  - I use [VLC][1] and pick "Open/Network..." to set the URL

[1]: http://www.videolan.org


### 4.3 Audio Playback Setup on mon Raspi

#### Speaker Setup

* Install and attach your speakers to the Raspi's analog audio

* If you use the analog output on your Raspi then make sure to enable it:
```
> amixer cset numid=3 1
```

* Use the alsamixer to setup output levels (I use 85)
```
> alsamixer
```

* To test play a sound:
```
> aplay /usr/share/sounds/alsa/Noise.wav
```

* Install some nice sounds for chiming in pifon
```
# apt-get install sound-icons
```

#### Music Player Daemon Setup

* Install package
```
# apt-get install mpd mpc
```

* Copy the sound-icons to mpd's music dir and update its index
```
# cp /usr/share/sounds/sound-icons/* /var/lib/mpd/music/
> mpc update
> mpc ls
```

* Test simple playback by playing a sound icon
```
> mpc clear
> mpc add prompt.wav
> mpc play
```

* Test streaming from fon's audio server
  - Use the URL we created in the server setup on fon part (see above)
```
> mpc clear
> mpc add http://fozzie.local:8000/pifon
> mpc play
... listen a bit
> mpc stop
```


## 5. Monitor User Interface Setup

### 5.1 Adafruit 16x2 character LCD display

#### I2C Setup

* Activate I2C with **raspi-config**
```
# raspi-config
Advanced Options -> I2C
  Yes + Yes
```
  - Reboot to activate

* Install i2c tools
```
# apt-get install i2c-tools
```

* Scan the I2C bus for the LCD
```
# i2cdetect 0
```
  - This will report the LCD at address **0x20**
  - Note: On new Raspis (B+ and B2) use bus 1 instead of 0!

* You should find a device for your bus:
```
> ls -la /dev/i2c*
crw-rw---- 1 root i2c 89, 0 Feb  9 11:00 /dev/i2c-0
```

* Make sure your user is member of group **i2c**:
```
# usermod -a -G i2c chris
```

* Now re-test bus scan as user
```
> i2cdetect 0
```

#### Python Setup

* Install Python I2C library
```
# apt-get install python-smbus
```

* Install the Adafruit library for the display
```
> sudo apt-get install python-dev
> cd ~
> git clone https://github.com/adafruit/Adafruit_Python_CharLCD.git
> cd Adafruit_Python_CharLCD
> sudo python setup.py install
```

* Run a quick test with the shipped examples:
```
> cd Adafruit_Python_CharLCD/example
> python char_lcd_plate.py
```

* Run a test with the pifon code base:
```
> cd raspi/pifon/mon/ui/lcd
> python lcd.py
```
  - Press buttons to see their values
  - Press Up and Down simultaneously to quit demo


## 6. Installing the pifon Bots

### 6.1 Autostart Bots

#### fon

* as root edit ``/etc/rc.local`` and add before ``exit 0``:
```
su -l chris -c '/home/chris/raspi/pifon/fon/rc.pifon_fon start'
```
  - no change **chris** to your user name

* test:
  * reboot and test
  * you can always attach to your running processes with
```
> tmux list-sessions
> tmux attach -t audio
leave the tmux session with Ctrl+B and d
```
  * you can exit the audio server by pressing Ctrl+C while being attached
  * manually start/stop the fon with:
```
> $HOME/raspi/pifon/fon/rc.pifon_fon start
> $HOME/raspi/pifon/fon/rc.pifon_fon stop
```

#### mon

* same as for **fon** but use script in **mon** folder
```
su -l chris -c '/home/chris/raspi/pifon/mon/rc.pifon_mon start'
```

EOF
