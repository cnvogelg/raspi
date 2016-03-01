# pifon
## the next generation baby monitor for Raspberry Pis

### Features

* **Version 2.0**: 28.02.2016
  - multi fon support. observe one, two or more rooms with one mon
  - fully customizable audio streaming
  - use audio ssh stream for low-latency playback
  - redesigned LCD UI with graphical audio level display
  - completely rewritten XMPP bot framework with modules


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

pifon uses available technologies whenever possible. Therefore the
communication between fon and mon uses the chat protocol XMPP (aka Jabber).
So both fon and mon are implemented as chat bots that simply talk their
events to a chat room and listen out for events there. Nice side effect here
is that you can use a chat client to monitor the events and even inject your
own ones by simply chatting with the bots.

We use the [prosody][1] XMPP server in a local installation. The bots are
implemented in Python 2.7 and use the [sleekxmpp][2] library.

Audio streaming is done by recording an audio stream with [SoX][3] and stream
it via an SSH link to the mon where it is play back with SoX again.

The mon uses a small [16x2 character LCD display from Adafruit][4] to display
all events and status information. Furthermore, the display hardware offers a
set of five buttons that allow you to control the behavior of the mon. If you
do not have a LCD then you can run the mon with a LCD simulator. It renders
the LCD display with PyGame library on any SDL supported display. Use this to
run mon e.g. on your desktop PC/Mac.

However, the system is very flexible, i.e. you can easily replace the way the
audio is played back or streamed or you can even write your own UI that uses
another way of displaying the audio events.

[1]: http://prosody.im
[2]: http://sleekxmpp.com
[3]: http://sox.sourceforge.net
[4]: https://learn.adafruit.com/adafruit-16x2-character-lcd-plus-keypad-for-raspberry-pi/overview

### 1.3 System Diagram

```
---------- fon ----------

                  +----> event detector -----> XMPP bot ------> prosody
Mic               |                                             chat room
*=== --> audio ---+ mixin interface in ALSA to share input
         record   |
                  +----> SoX ALSA recording <---- SSH connect from mon
                         record
                         stream

---------- mon ----------

prosody ---------> XMPP bot ----+---------> show events in UI/LCD
chat room                       |
                                +---------> connect fon via SSH
                                            |
                                            +-> play stream back with SoX
```


## 2. Installation

### 2.1 Required Hardware

* Two Raspberry Pis
  - I use classic Model B, but newer ones like B+ or B2 should work, too
  - Model B/B+/B2 is recommended since networking is required
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
    - Tmux is used for conveniently running the fon/mon bots
    - git is used to get the pifon source code
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
  LCD simulator there. Even **fon** runs here for quick local audio testing.

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
  following packages:

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

```python
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

Please **note** that the test bot reads the configuration file called **sample.cfg**
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

The **fon** Raspi will use its microphone to capture audio and we install the
recording tools there.

The **mon** Raspi will setup its audio playback.

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


### 4.2 Audio Playback Setup on mon Raspi

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


### 4.3 Setup Audio Streaming

For audio streaming we need a working ssh setup without passwords, SoX setup
for both parts and the recorder tool installed at the right place.

### SSH Setup

The **mon** raspi must be able to log into the **fon** raspi without password
by using authorized keys.

You can test your setup by running:

```
chris@mon $ ssh fon    # log in as chris on fon
```

If you can connect the fon server without password everything is fine.

If it does not work for you then set it up like this:

On **mon** do a:
```
chris@mon $ ssh-keygen
chris@mon $ ssh-copy-id fon
```

### Test streaming

Audio streaming is done by running a script called **stream_ssh** on **mon**.
The script resides in the folder **raspi/pifon/mon/tools**. It connects to
**fon** via ssh and runs a recorder there called
**raspi/pifon/fon/tools/recorder**. To make this work ensure that the
project's code is available at **raspi** in your home folder on **fon**.

First we need to install SoX on **mon**, too:

```
# apt-get install sox
```

A quick streaming test can be launched manually on **mon**:

```
chris@mon $ cd ~/raspi/pifon/mon
chris@mon $ tools/stream_ssh fon
```

Give the name of the **fon** raspi as single argument. This will stream the
audio from **fon** until you stop it by pressing ``Ctrl+C``.

If this works you are ready to run the bots on **mon** and **fon**!


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

* Your display is attached to address **0x20**:
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: 20 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
```

* Also the i2c bus devices should be available:
```
> ls -la /dev/i2c*
crw-rw---- 1 root i2c 89, 0 Feb  9 11:00 /dev/i2c-0
```

* Make sure your user is member of group **i2c**:
```
# usermod -a -G i2c chris
```

* Re-login to activate new group and now re-test bus scan as user
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


## 6. Setting up the pifon Bots

In the previous chapters the environment for the pifon bot instances was
prepared and we are now ready to run the main components

### 6.1 Common setup options for both fon and mon

#### Config File Location

* The pifon fon part resides in the directory ``raspi/pifon/fon``, the mon
  part in ``raspi/pifon/mon``.

* The fon part is configured with the file ``pifon_fon.cfg``there and
  mon in ``pifon_mon.cfg``.

* Note: You need to adjust this file to your needs otherwise the bot will not
  work!

* You can either edit the config file directly in place but this may collide
  with changes if you update your pifon source. Another option is to copy the
  config file to ``~/.pifon_fon.cfg`` and ``~/.pifon_mon.cfg`` and edit it
  there. If this file exists it will be loaded from there.

* Actually the files in your home are loaded first and then the local files
  are overlayed. Therefore, it makes sense to only add the options you change
  to your config in the home directory. All other options are then fetched
  from the shipped files in the source tree.

#### Common XMPP Options

* Both fon and mon bots share some options:
```
[xmppbot]
jid=fon@coin.local
password=fon
room=pifon@muc.coin.local
nick=fon
```
  * **jid** is the login setup in prosody so that the bot is allowed to enter
    the chat room. All fons can share a single login.
  * **password** as set in prosody.
  * **room** is the room name that will be created and joined by the bots.
    Pattern is **room@muc.server**. Room name can be arbitrary but must be
    the same for both fon and mon clients.
  * **nick** is the name of the bot in the chat room. It will be automatically
    extended by the hostname so you can distinguish instances on different
    hosts.


### 6.2 fon Config

* Config options for fon include the **audio** module:
```
[audio]
sim=False
trace=False
location=%%h
listen_url=%%H
alevel=1
slevel=0
attack=0
sustain=5
respite=10
update=5
```

#### General Audio Options

  * **sim**: set to **True** will enable an audio simulator: It creates audio
    events without recording from the microphone. Use this to test your mon
    setup without the need of generating noise all the time :)
  * **trace**: set to **True** will enable more output on the console so you
    can watch all the audio levels that are detected.
  * **location**: the room name of the microphone. It will be displayed in
    mon when an audio event is detected there. Use ``%%h`` as a placeholder
    for the hostname and ``%%H``for the full qualified host name.
  * **listen_url**: this url is broadcasted to the mon player so it knows how
    to reach the audio stream. This url will be passed to the player commands
    on the mon so that they can reach this audio source. Typically its the
    host name of the machine. ``%%h`` and ``%%H``work here, too.

#### Audio Detector Config

* The following options control the audio detector. It has one of the following
states:
  * **idle**: no audio activity detected
  * **attack**: level is above a limit for a certain amount of time. this
    begins the activity.
  * **busy**: level is still high. activity is detected.
  * **sustain**: audio level drops below a given level for a certain amount
    of time. activity will end.
  * **respite**: after an activity interval enforce a time of inactivity no
    matter what audio level is recorded. After that a new cycle may begin
    with **attack** or **idle** is entered.

* The corresponding config options are:
  * **alevel**: the level that must be reached to enter **attack** state
  * **attack**: the duration in seconds the attack level must be reached to
    enter **attack** state
  * **slevel**: the level that must be reached to enter **sustain** state
  * **sustain**: the duration in seconds the sustain level must be held to
    enter **sustain** state
  * **respite**: the silence period in seconds after **sustain**
  * **update**: if the audio level is reported give a new value every n *
    100ms

#### VUMeter Config

* Sound level detection can be controlled in **vumeter** module:
```
[vumeter]
recorder=rec
sample_rate=0
channels=0
interval=250
device=mixin
zero_range=0
sox_filter=highpass 500
tool=tools/vumeter
```

  * **recorder**: select the recording program for capturing. currently only
    SoX' rec tool is supported
  * **sample_rate**: use this sample rate for recording. 0 means auto detect
    sample rate
  * **channels**: setup the channels for recording. Typically use only one
    channel but sometimes devices can only run stereo. 0 means auto detect.
  * **interval**: derive a loudness value every n ms. Smaller intervals give
    faster reaction time but need more CPU power.
  * **device**: the ALSA audio device we use for recording
  * **zero_range**: all recorded sample values below this range are set to
    zero. Use this to do some kind of simple noise cancelling.
  * **sox_filter**: run a filter after recording. We use a high pass here to
    remove power humming
  * **tool**: the external script that records the audio signal and outputs
    the loudness values to stdout.


### 6.3 mon Config

The mon raspi has two config sections, one for the audio player and the other
one configuring the user interface (UI).

#### Audio Player Config

* The monitor has this player options:
```
[player]
chime_start_sound=sounds/prompt.wav
chime_stop_sound=sounds/finish.wav
chime_start_cmd=play %%s
chime_stop_cmd=play %%s
start_stream_cmd=tools/stream_ssh %%s
stop_stream_cmd=
play_chimes=True
start_muted=False
```
  * **chime_start_sound** and **chime_stop_sound** give the filename of the
    sound file that will be played when audio activity starts or ends. The
    default are some shipped sounds but you can give your own files here.
    Either give a full path or copy your sounds into **sound** folder.
  * **chime_start_cmd** and **chime_stop_cmd** define the external player
    commands that will be executed. Note that ``%%s`` is a placeholder for
    the audio file that will be played (see options before). By default
    we use the player from SoX called **play**.
  * **start_stream_cmd** is called when the audio stream has to start. The
    placeholder ``%%s`` gives the audio listen_url emitted by the **fon**.
    (See **listen_url** in **fon** section). The start stream command can
    either be a short running command that starts streaming in an external
    process or is a long running command that runs as long as the stream is
    needed. We use the latter option and a custom script called **stream_ssh**
    that streams the audio from **fon** via ssh. The mon will kill this
    command when playing has to stop.
  * **stop_stream_cmd** is typically used if you only have a short running
    start command and tells the external player to stop streaming. By default
    we left the field blank and this does no stop operation.
  * **play_chimes** is a bool field that defines if chime sounds are to be
    played before and after the streamed audio. Note that this is the preset
    and you can alter this value via UI later on. Default is true.
  * **start_muted** is a bool field that defines if the player starts muted,
    i.e. it does not play an audio stream if a **fon** client is active.
    Note that this is the preset and you can alter this value via UI later
    on. Default is false.


#### User Interface Config

* The monitor has the following UI options:
```
[ui]
name=lcd
```

  * **ui** lets you select the UI module that is used. Supported values are:
    * **lcd**: Adafruit 16x2 LCD driver
    * **dummy**: A simple dummy output on the console only

* The LCD UI has some special options:
```
[ui_lcd]
mode=auto
```

  * **mode**: **sim** will use the LCD simulator running on PyGame on all
    machines, **hw** will use the real Adafruit LCD and **auto** tries to
    automatically detect if the HW is available and if yes it will use it.


### 6.4 A First Test Drive

With the configuration in place we can try to manually run the fon and mon
bots.

#### Running fon

* Prepare config for ``pifon_fon.cfg`` as described above
* Enter the pifon fon directory ``raspi/pifon/fon``
* Run ``./pifon_fon``
* It will connect to the chat room, start recording and show you all audio
  events

#### Running mon

* Prepare config for ``pifon_mon.cfg`` as described above
* Enter the pifon mon directory ``raspi/pifon/mon``
* Run ``./pifon_mon``
* It will start displaying the UI and show all incoming events

#### Test

* **mon** should see the fon client(s) and show their state
* If the audio level on **fon** increases then **mon** should show it and
  start streaming data
* Abort both bots with ``Ctrl+C`` after testing.


### 6.5 Setting up Autostart for the Bots

Now that the bots run manually in test drive mode it is time to run them
automatically when your Pis start. This will be your production setup
where both bots on power on.

#### Autostart fon

* as root edit ``/etc/rc.local`` and add before ``exit 0``:
```
su -l chris -c '/home/chris/raspi/pifon/fon/rc.pifon_fon start'
```
  - note: change **chris** to your user name

* test:
  * reboot and test
  * you can always attach to your running processes with
```
> tmux list-sessions
> tmux attach -t fon
leave the tmux session with Ctrl+B and d
```
  * you can exit the audio server by pressing Ctrl+C while being attached
  * manually start/stop the fon with:
```
> $HOME/raspi/pifon/fon/rc.pifon_fon start
> $HOME/raspi/pifon/fon/rc.pifon_fon stop
```

#### Autostart mon

* see instruction for **fon** above
* but use script in **mon** folder in ``/etc/rc.local``:
```
su -l chris -c '/home/chris/raspi/pifon/mon/rc.pifon_mon start'
```


## 7. User's Guide

### 7.1 LCD User Interface

#### Display Items

The display has 16 chars in two rows and while the first row changes its
contents depending on the mode the **mon** is in, the second row always
shows the state of the discovered **fon** clients and the local **player**.

**mon** has the following modes:
  * **Idle**: none of the attached **fon** clients is active
  * **Active**: at least one **fon** client is active
  * **Info**: information messages are available

**Top Row** displays:
  * In **idle** mode a clock and the date, time zone and calender week
  * In **active** mode information of the **fon** client that is currently
    active. The line looks like this
```
BabyName00-___-12
```
  * Line contents
    * It displays the location (room name) of the active **fon** client
    * Then the duration of the active event in seconds
    * A bar graph of the incoming audio levels (vumeter values)
    * The current audio level also given as a number
  * In **info** mode a scolling text containing the information

**Bottom Row** displays:
  * each **fon** client in a small block:
```
1I._
```
  * the first number is the number of the fon client. starts with 1.
  * the letter gives the state of the audio detector on the **fon**
    client. The following states are used:
    * **I)dle**: no audio activity on client.
    * **A)ttack**: audio level is above limit. waiting for activity to start.
    * **B)usy**: activity has started and audio level is still hight enough.
    * **S)ustain**: audio level is below limit. Activity will stop soon.
    * **R)espite**: after sustain enforce a delay
  * the "liveness" of the **fon** is given with the next character:
    * **. Dot**: fon client answers pings and is thus considered alive
    * **! Ping**: a new ping message was just received.
    * **? Timeout**: fon did not answer ping in time
    * **p Playing**: local player is playing audio stream of this **fon**
  * the fourth character is a bar graph that gives the current audio level
    (vumeter values) received from this fon raspi.
  * on the right most corner a single letter denotes **local player state**:
    * if the letter is lowercase then playing chimes is disable. Otherwise
      chimes are enabled. Note: you can toggle this switch via UI, too.
    * the following letters/symbols are used:
      * **m)onitor** watch out for any audio activity coming from a **fon**
      * **mu)te** disable playback until toggled again via UI
      * **p)lay** (icon) play an audio source
      * **l)isten** mode: directly connect to a **fon** and start streaming.

#### Background Color

The LCD has a nice feature and provides a backlight that can be set to
different RGB colors. We use the backlight to show the state of the monitor
colored coded. This is very helpful if you mute the player: you can still
recognize audio events by simply judging the color of the display.

The following colors are displayed:
  * **Green**: monitor is idle. No **fon** client is active.
  * **Red**: at least one **fon** client is active.
  * **Blue**: monitor is not connected to chat bot
  * **Violet**: at least one **fon** client does not answer regular pings

#### Button Control

The LCD has some buttons attached that allow to create a minimal UI.
The following buttons are scanned:
  * **left**: toggle play chimes flag
  * **right**: toggle mute flag
  * **up**: start listening to a fon client. call mutltiple times to cycle
    through available clients and the regular monitor mode.
  * **down**: toggle screen blanking. it will render the screen black if the
    monitor is idle for some seconds.
  * **select**: trigger to show valuable information: who is connected on
    which port.
  * **left + right**: press both buttons to quit the bot.

EOF
