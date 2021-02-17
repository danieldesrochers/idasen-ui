# idasen-ui

[Get latest version here!](https://github.com/danieldesrochers/idasen-ui/releases)

Desk control application that works with ikea IDÅSEN desk.


![app screenshot](./idasen-ui.png)

IDÅSEN is an electric sitting-standing desk with a Linak bluetooth controller sold by ikea.
The position of the desk can controlled by a physical switch on the desk or via bluetooth using an phone app.

This application controls the Idasen desk via bluetooth from a desktop computer and allows to store two favorite positions.

This application is built in Python on top of the IdasenDesk API made by 'newAM/idasen' which was a heavily modified fork of 'rhyst/idasen-controller'.

The Idasen desk control app (idasen-ui) has been package for Windows 10 for easier installation.


Prerequisites
=============
**The desk must be connected and paired to the computer before launching the application.**
- Open Windows Parameters
- Find your Bluetooth settings
- Put the IKEA Idasen desk in pairing mode (blue light will flash slowly)
- On the Bluetooth setting window, click "Add a Bluetooth device"
- Select "Desk 8638" and add it to your bluetooth devices

Install Idasen-UI
=================
- Download latest release idasen-ui package (https://github.com/danieldesrochers/idasen-ui/releases)

- Unzip the package to any **\<folder\>** with read-write user permissions (e.g.: c:/Program Files)

- Browse to your extracted **\<folder\>**/idasen-ui 

- Run 'idasen-ui.exe'

For faster access to the application, consider creating a shortcut on your desktop and start menu.

How To Use Idasen-UI
====================
Idasen Desk Control application is a simple graphical user interface.

Connect your desk
------------------
When application runs for the first time, no save configuration will be found. 
Be patient, it might take few minutes to explore all Bluetooth devices paired with the computer.
Click Bluetooth button to discover your desk and save initial configuration.

You are connected!
------------------
Once connected to the desk, current desk position will be displayed and moving buttons will be enabled. 
- Press and maintain the up/down arrow the move the desk to the desired position.
- Press M(emory) button to save the current position to 1 or 2.
- Press position 1 or 2 to move the desk to the save position.

Known issues
============
IKEA IDASEN Desk internal Linak controller seems to have a built-in memory for previous positions. This could cause some weird move effects. The app will retry twice to move to the right direction. The built-in memory issue seems to reduce while using the application for a longer period since the previous built-in positions match those from the application.
