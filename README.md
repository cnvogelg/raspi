chris' Raspberry Pi Projects
============================

This project holds a collection of all stuff I am currently
doing with my new RaspberryPi board.

raspi install docs
------------------

how to setup your new raspi with nice features like:

* own user login
* DNS naming for your box
* NFS work share with autofs

more: [doc/install.txt](raspi/blob/master/doc/install.txt)

pifon - the geeky baby monitor appliance
----------------------------------------

### Ingredients

* A raspi
* A USB web cam with microphone

### Server

* Setup an Icecast2 streaming MP3 service for the baby's audio
* Setup an XMPP chat server that broadcasts audio events

### Client(s)

* Listen for audio events on XMPP chat room from server to start/stop audio streaming
* Stream MP3 from server to monitor baby's activity

more: [doc/pifon.md](raspi/blob/master/doc/pifon.md)

pifoto - tethered shooting with iPad and raspi
----------------------------------------------

make a WiFi based tethered camera shooting tool uses gphoto2

more: [doc/pifoto.txt](raspi/blob/master/doc/pifoto.txt)
